from __future__ import annotations

import asyncio
import html
import os
import re
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import httpx

from ..core.config import settings

TELEGRAM_API_BASE = "https://api.telegram.org"


def extract_image_srcs(html_content: str) -> List[str]:
    if not html_content:
        return []
    return re.findall(r"<img[^>]+src=\"([^\"]+)\"", html_content)

def is_data_url(url: str) -> bool:
    return url.startswith("data:")

def parse_data_url(data_url: str) -> Tuple[str, bytes]:
    # Returns (mime, bytes)
    # Example: data:image/png;base64,AAA...
    m = re.match(r"data:([^;]+);base64,(.*)", data_url, flags=re.I | re.S)
    if not m:
        raise ValueError("Unsupported data URL format")
    mime = m.group(1)
    b64 = m.group(2)
    import base64
    return mime, base64.b64decode(b64)

def html_to_telegram_html(html_content: str) -> str:
    # Telegram supports a limited subset of HTML. We'll strip most tags except b,i,u,s,a,code,pre,blockquote.
    if not html_content:
        return ""
    # Allow basic formatting and links
    allowed = ["b", "strong", "i", "em", "u", "ins", "s", "strike", "a", "code", "pre", "blockquote"]
    # Remove images and unsupported tags; keep inner text
    def replacer(match: re.Match[str]) -> str:
        tag = match.group(1).lower()
        if tag in allowed:
            return match.group(0)
        return html.escape(match.group(2) or "")

    # Replace block tags with spacing
    text = re.sub(r"<(?:img|video|audio)[^>]*>", "", html_content, flags=re.I)
    # Convert <br> and <p> to newlines
    text = re.sub(r"<\s*br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<\s*/?p\s*>", "\n", text, flags=re.I)
    # Strip most tags but preserve inner text for unsupported
    text = re.sub(r"<([a-zA-Z0-9]+)[^>]*>(.*?)</\1>", replacer, text, flags=re.S)
    # Unescape any remaining entities properly
    return text

async def send_message(token: str, chat_id: str, text: str, disable_web_page_preview: bool = False) -> dict:
    url = f"{TELEGRAM_API_BASE}/bot{token}/sendMessage"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, data={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": disable_web_page_preview,
        })
        resp.raise_for_status()
        return resp.json()

async def send_photo_file(token: str, chat_id: str, filename: str, content_bytes: bytes, mime: str, caption: Optional[str] = None) -> dict:
    url = f"{TELEGRAM_API_BASE}/bot{token}/sendPhoto"
    async with httpx.AsyncClient(timeout=60) as client:
        files = {"photo": (filename, content_bytes, mime)}
        data = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption
            data["parse_mode"] = "HTML"
        resp = await client.post(url, data=data, files=files)
        resp.raise_for_status()
        return resp.json()

async def send_photo_url(token: str, chat_id: str, photo_url: str, caption: Optional[str] = None) -> dict:
    url = f"{TELEGRAM_API_BASE}/bot{token}/sendPhoto"
    async with httpx.AsyncClient(timeout=60) as client:
        data = {"chat_id": chat_id, "photo": photo_url}
        if caption:
            data["caption"] = caption
            data["parse_mode"] = "HTML"
        resp = await client.post(url, data=data)
        resp.raise_for_status()
        return resp.json()

async def get_bot_info(token: str) -> dict:
    """Get bot information to verify token and connection."""
    url = f"{TELEGRAM_API_BASE}/bot{token}/getMe"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()

async def get_chat_info(token: str, chat_id: str) -> dict:
    """Get chat information to verify bot has access to the channel."""
    url = f"{TELEGRAM_API_BASE}/bot{token}/getChat"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, data={"chat_id": chat_id})
        resp.raise_for_status()
        return resp.json()

async def verify_channel_access(token: str, chat_id: str) -> dict:
    """Verify that the bot can access the specified channel."""
    try:
        chat_info = await get_chat_info(token, chat_id)
        return {
            "ok": True,
            "chat": chat_info.get("result", {}),
            "accessible": True
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            error_data = e.response.json()
            error_code = error_data.get("error_code", 0)
            if error_code == 400:
                return {
                    "ok": False,
                    "error": "Bot is not a member of this channel or channel doesn't exist",
                    "accessible": False
                }
        return {
            "ok": False,
            "error": f"Failed to access channel: {e.response.text}",
            "accessible": False
        }
    except Exception as e:
        return {
            "ok": False,
            "error": f"Unexpected error: {str(e)}",
            "accessible": False
        }

async def publish_content(html_content: str, title: str, *, chat_id: Optional[str] = None, token: Optional[str] = None) -> dict:
    if not token:
        token = settings.telegram_bot_token
    if not chat_id:
        chat_id = settings.telegram_channel_id
    if not token or not chat_id:
        raise ValueError("Telegram credentials not configured")

    text = html_to_telegram_html(html_content)
    # Extract images hosted on this server and send first image with caption, rest separately
    image_srcs = extract_image_srcs(html_content)

    results: List[dict] = []
    if image_srcs:
        first = image_srcs[0]
        caption = f"{html.escape(title)}\n\n{text}" if title else text
        if is_data_url(first):
            mime, bytes_content = parse_data_url(first)
            filename = f"image.{mime.split('/')[-1]}"
            results.append(await send_photo_file(token, chat_id, filename, bytes_content, mime, caption=caption))
        elif first.startswith("http://") or first.startswith("https://"):
            results.append(await send_photo_url(token, chat_id, first, caption=caption))
        else:
            # Unrecognized src scheme; fallback to text
            pass
        # Send remaining images without captions
        for src in image_srcs[1:]:
            try:
                if is_data_url(src):
                    mime, bytes_content = parse_data_url(src)
                    filename = f"image.{mime.split('/')[-1]}"
                    results.append(await send_photo_file(token, chat_id, filename, bytes_content, mime, caption=None))
                elif src.startswith("http://") or src.startswith("https://"):
                    results.append(await send_photo_url(token, chat_id, src, caption=None))
            except Exception:
                # Skip bad images but continue
                continue
        if results:
            return {"ok": True, "results": results}

    # Fallback: send text-only message
    results.append(await send_message(token, chat_id, f"{html.escape(title)}\n\n{text}" if title else text))
    return {"ok": True, "results": results}
