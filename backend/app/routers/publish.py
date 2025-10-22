from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..db import get_session
from ..models import Note
from ..services.telegram import publish_note

router = APIRouter(prefix="/publish", tags=["publish"])


class PublishRequest(BaseModel):
    chat_id: str | None = None
    token: str | None = None


@router.post("/note/{note_id}")
async def publish_note_endpoint(note_id: int, payload: PublishRequest) -> dict:
    with get_session() as session:
        note = session.get(Note, note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        try:
            return await publish_note(note.content_html or "", note.title or "", chat_id=payload.chat_id, token=payload.token)
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
