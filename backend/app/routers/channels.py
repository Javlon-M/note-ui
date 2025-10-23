from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from ..core.config import settings
from ..services.telegram import get_bot_info, verify_channel_access

router = APIRouter(prefix="/channels", tags=["channels"])


@router.get("/")
def list_channels() -> list[dict[str, str]]:
    return settings.get_channels()

@router.get("/status")
async def get_channels_status() -> Dict[str, Any]:
    """Get status of all configured channels including bot verification."""
    channels = settings.get_channels()
    token = settings.telegram_bot_token
    
    if not token:
        return {
            "bot_configured": False,
            "error": "Telegram bot token not configured",
            "channels": []
        }
    
    # Verify bot token
    try:
        bot_info = await get_bot_info(token)
        bot_configured = bot_info.get("ok", False)
        bot_username = bot_info.get("result", {}).get("username", "Unknown")
    except Exception as e:
        return {
            "bot_configured": False,
            "error": f"Failed to verify bot token: {str(e)}",
            "channels": []
        }
    
    # Check each channel
    channel_statuses = []
    for channel in channels:
        channel_id = channel.get("id")
        channel_name = channel.get("name")
        
        if not channel_id:
            channel_statuses.append({
                "id": channel_id,
                "name": channel_name,
                "accessible": False,
                "error": "Channel ID not provided"
            })
            continue
            
        try:
            access_result = await verify_channel_access(token, channel_id)
            channel_statuses.append({
                "id": channel_id,
                "name": channel_name,
                "accessible": access_result.get("accessible", False),
                "chat_info": access_result.get("chat", {}),
                "error": access_result.get("error") if not access_result.get("accessible") else None
            })
        except Exception as e:
            channel_statuses.append({
                "id": channel_id,
                "name": channel_name,
                "accessible": False,
                "error": f"Failed to check channel access: {str(e)}"
            })
    
    return {
        "bot_configured": bot_configured,
        "bot_username": bot_username,
        "channels": channel_statuses
    }

@router.post("/verify/{channel_id}")
async def verify_channel(channel_id: str) -> Dict[str, Any]:
    """Verify access to a specific channel."""
    token = settings.telegram_bot_token
    
    if not token:
        raise HTTPException(status_code=400, detail="Telegram bot token not configured")
    
    try:
        result = await verify_channel_access(token, channel_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify channel: {str(e)}")
