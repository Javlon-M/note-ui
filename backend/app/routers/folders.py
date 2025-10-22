from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from sqlmodel import select, func

from ..db import get_session
from ..models import Folder, FolderCreate, FolderUpdate, Note

router = APIRouter(prefix="/folders", tags=["folders"])


@router.get("/", response_model=List[Folder])
def list_folders(include_deleted: bool = False) -> List[Folder]:
    with get_session() as session:
        query = select(Folder)
        if not include_deleted:
            query = query.where(Folder.is_deleted == False)  # noqa: E712
        results = session.exec(query.order_by(func.lower(Folder.name))).all()
        return results


@router.post("/", response_model=Folder)
def create_folder(payload: FolderCreate) -> Folder:
    with get_session() as session:
        folder = Folder(name=payload.name)
        session.add(folder)
        session.flush()
        session.refresh(folder)
        return folder


@router.patch("/{folder_id}", response_model=Folder)
def update_folder(folder_id: int, payload: FolderUpdate) -> Folder:
    with get_session() as session:
        folder = session.get(Folder, folder_id)
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(folder, key, value)
        session.add(folder)
        session.flush()
        session.refresh(folder)
        return folder


@router.delete("/{folder_id}")
def delete_folder(folder_id: int, hard: bool = False) -> dict:
    with get_session() as session:
        folder = session.get(Folder, folder_id)
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        if hard:
            # prevent delete if notes exist unless all are deleted
            notes_exist = session.exec(select(Note).where(Note.folder_id == folder_id, Note.is_deleted == False)).first()  # noqa: E712
            if notes_exist:
                raise HTTPException(status_code=400, detail="Folder has active notes; delete or move them first")
            session.delete(folder)
        else:
            folder.is_deleted = True
            session.add(folder)
        return {"ok": True}
