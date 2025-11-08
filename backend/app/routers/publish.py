from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..services.telegram import publish_content, verify_channel_access, validate_content_length, extract_image_srcs
from ..core.config import settings

router = APIRouter(prefix="/publish", tags=["publish"])


class PublishRequest(BaseModel):
    telegram_channel: str
    telegram_bot_token: str
    channel_id: str
    title: str | None = None
    content_html: str | None = None
    token: str | None = None
    verify_channel: bool = True  # Whether to verify channel access before publishing


@router.post("")
async def publish_endpoint(payload: PublishRequest) -> dict:
    # Use provided token or fall back to settings
    token = payload.telegram_bot_token
    chennel_id = payload.telegram_channel.split("=")[1]
    
    if not token:
        raise HTTPException(status_code=400, detail="Telegram bot token not provided")
    
    if not chennel_id:
        raise HTTPException(status_code=400, detail="Channel ID is required")
    
    # Verify channel access if requested
    if payload.verify_channel:
        try:
            verification = await verify_channel_access(token, chennel_id)
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
            chat_id=chennel_id,
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


@router.post("/validate")
async def validate_content(payload: PublishRequest) -> dict:
    """Validate content length against Telegram limits."""
    try:
        # Extract images to determine if content has images
        image_srcs = extract_image_srcs(payload.content_html or "")
        has_images = len(image_srcs) > 0
        
        # Validate content length
        validation = validate_content_length(
            payload.content_html or "", 
            payload.title or "", 
            has_images
        )
        
        return {
            "success": True,
            "validation": validation,
            "recommendation": get_recommendation(validation)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate content: {str(e)}")


def get_recommendation(validation: dict) -> str:
    """Get recommendation based on validation result."""
    if validation["is_valid"]:
        return "Content is within Telegram limits. Ready to publish!"
    
    exceeded_by = validation["exceeded_by"]
    limit_type = validation["limit_type"]
    
    if limit_type == "image caption":
        return f"⚠️ Content exceeds Telegram limit for image captions (1,024 characters). Please reduce content by {exceeded_by} characters, or remove images to use the 4,096 character limit for text-only messages."
    else:
        return f"⚠️ Content exceeds Telegram limit for text messages (4,096 characters). Please reduce content by {exceeded_by} characters."
