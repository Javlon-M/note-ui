from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.telegram import publish_content

router = APIRouter(prefix="/publish", tags=["publish"])


class PublishRequest(BaseModel):
    channel_id: str
    title: str | None = None
    content_html: str | None = None
    token: str | None = None


@router.post("")
async def publish_endpoint(payload: PublishRequest) -> dict:
    try:
        return await publish_content(
            html_content=payload.content_html or "",
            title=payload.title or "",
            chat_id=payload.channel_id,
            token=payload.token,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
