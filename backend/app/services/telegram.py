from __future__ import annotations

import asyncio
import html
import os
import re
from pathlib import Path
from typing import Iterable, List, Optional

import httpx

from ..core.config import settings

TELEGRAM_API_BASE = "https://api.telegram.org"


def extract_image_srcs(html_content: str) -> List[str]:
    if not html_content:
        return []
    return re.findall(r"<img[^>]+src=\"([^\"]+)\"", html_content)


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


async def send_photo(token: str, chat_id: str, image_path: Path, caption: Optional[str] = None) -> dict:
    url = f"{TELEGRAM_API_BASE}/bot{token}/sendPhoto"
    async with httpx.AsyncClient(timeout=60) as client:
        with image_path.open("rb") as f:
            files = {"photo": (image_path.name, f, "image/jpeg")}
            data = {"chat_id": chat_id}
            if caption:
                data["caption"] = caption
                data["parse_mode"] = "HTML"
            resp = await client.post(url, data=data, files=files)
            resp.raise_for_status()
            return resp.json()


async def publish_note(html_content: str, title: str, *, chat_id: Optional[str] = None, token: Optional[str] = None) -> dict:
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
        if first.startswith("/media/"):
            path = settings.media_dir / first.split("/media/")[-1]
            if path.exists():
                # Use title as caption if present
                caption = f"<b>{html.escape(title)}</b>\n\n{text}" if title else text
                results.append(await send_photo(token, chat_id, path, caption=caption))
                # Send remaining images without captions
                for src in image_srcs[1:]:
                    if src.startswith("/media/"):
                        p = settings.media_dir / src.split("/media/")[-1]
                        if p.exists():
                            results.append(await send_photo(token, chat_id, p, caption=None))
                return {"ok": True, "results": results}

    # Fallback: send text-only message
    results.append(await send_message(token, chat_id, f"<b>{html.escape(title)}</b>\n\n{text}" if title else text))
    return {"ok": True, "results": results}
