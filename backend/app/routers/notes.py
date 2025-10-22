from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select, or_, desc

from ..db import get_session
from ..models import Note, NoteCreate, NoteUpdate

router = APIRouter(prefix="/notes", tags=["notes"])


def strip_html(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value or "")


class NotesListResponse(BaseModel):
    items: List[Note]


@router.get("/", response_model=NotesListResponse)
def list_notes(
    folder_id: Optional[int] = None,
    q: Optional[str] = None,
    include_deleted: bool = False,
    pinned_first: bool = True,
) -> NotesListResponse:
    with get_session() as session:
        query = select(Note)
        if folder_id is not None:
            query = query.where(Note.folder_id == folder_id)
        if not include_deleted:
            query = query.where(Note.is_deleted == False)  # noqa: E712
        if q:
            like = f"%{q}%"
            query = query.where(or_(Note.title.ilike(like), Note.content_html.ilike(like)))
        if pinned_first:
            query = query.order_by(desc(Note.is_pinned), desc(Note.updated_at))
        else:
            query = query.order_by(desc(Note.updated_at))
        items = session.exec(query).all()
        return NotesListResponse(items=items)


@router.post("/", response_model=Note)
def create_note(payload: NoteCreate) -> Note:
    with get_session() as session:
        note = Note(
            title=payload.title or "Untitled",
            folder_id=payload.folder_id,
            content_html=payload.content_html or "",
        )
        session.add(note)
        session.flush()
        session.refresh(note)
        return note


@router.get("/{note_id}", response_model=Note)
def get_note(note_id: int) -> Note:
    with get_session() as session:
        note = session.get(Note, note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        return note


@router.patch("/{note_id}", response_model=Note)
def update_note(note_id: int, payload: NoteUpdate) -> Note:
    with get_session() as session:
        note = session.get(Note, note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(note, key, value)
        note.updated_at = datetime.utcnow()
        session.add(note)
        session.flush()
        session.refresh(note)
        return note


@router.post("/{note_id}/pin")
def toggle_pin(note_id: int, pinned: Optional[bool] = None) -> dict:
    with get_session() as session:
        note = session.get(Note, note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        note.is_pinned = (not note.is_pinned) if pinned is None else bool(pinned)
        note.updated_at = datetime.utcnow()
        session.add(note)
        return {"ok": True, "is_pinned": note.is_pinned}


@router.post("/{note_id}/restore")
def restore_note(note_id: int) -> dict:
    with get_session() as session:
        note = session.get(Note, note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        note.is_deleted = False
        note.updated_at = datetime.utcnow()
        session.add(note)
        return {"ok": True}


@router.delete("/{note_id}")
def delete_note(note_id: int, hard: bool = False) -> dict:
    with get_session() as session:
        note = session.get(Note, note_id)
        if not note:
            return {"ok": True}
        if hard or note.is_deleted:
            session.delete(note)
        else:
            note.is_deleted = True
            note.updated_at = datetime.utcnow()
            session.add(note)
        return {"ok": True}
