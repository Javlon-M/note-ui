from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..services.telegram import publish_content, verify_channel_access
from ..core.config import settings

router = APIRouter(prefix="/publish", tags=["publish"])


class PublishRequest(BaseModel):
    channel_id: str
    title: str | None = None
    content_html: str | None = None
    token: str | None = None
    verify_channel: bool = True  # Whether to verify channel access before publishing


@router.post("")
async def publish_endpoint(payload: PublishRequest) -> dict:
    # Use provided token or fall back to settings
    token = payload.token or settings.telegram_bot_token
    
    if not token:
        raise HTTPException(status_code=400, detail="Telegram bot token not provided")
    
    if not payload.channel_id:
        raise HTTPException(status_code=400, detail="Channel ID is required")
    
    # Verify channel access if requested
    if payload.verify_channel:
        try:
            verification = await verify_channel_access(token, payload.channel_id)
            if not verification.get("accessible", False):
                raise HTTPException(
                    status_code=403, 
                    detail=f"Cannot access channel: {verification.get('error', 'Unknown error')}"
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to verify channel access: {str(e)}")
    
    try:
        result = await publish_content(
            html_content=payload.content_html or "",
            title=payload.title or "",
            chat_id=payload.channel_id,
            token=token,
        )
        return {
            "success": True,
            "message": "Content published successfully",
            "result": result
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish content: {str(e)}")


@router.post("/test")
async def test_publish(payload: PublishRequest) -> dict:
    """Test publishing without actually sending the message."""
    token = payload.token or settings.telegram_bot_token
    
    if not token:
        raise HTTPException(status_code=400, detail="Telegram bot token not provided")
    
    if not payload.channel_id:
        raise HTTPException(status_code=400, detail="Channel ID is required")
    
    # Verify channel access
    try:
        verification = await verify_channel_access(token, payload.channel_id)
        return {
            "success": verification.get("accessible", False),
            "verification": verification,
            "message": "Channel access verified" if verification.get("accessible") else "Channel access failed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test channel access: {str(e)}")
