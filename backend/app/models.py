from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship


class FolderBase(SQLModel):
    name: str
    is_deleted: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Folder(FolderBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    notes: List["Note"] = Relationship(back_populates="folder")


class FolderCreate(SQLModel):
    name: str


class FolderUpdate(SQLModel):
    name: Optional[str] = None
    is_deleted: Optional[bool] = None


class NoteBase(SQLModel):
    title: str = "Untitled"
    content_html: str = ""
    is_pinned: bool = False
    is_deleted: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Note(NoteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    folder_id: Optional[int] = Field(default=None, foreign_key="folder.id", index=True)

    folder: Optional[Folder] = Relationship(back_populates="notes")
    attachments: List["Attachment"] = Relationship(back_populates="note")


class NoteCreate(SQLModel):
    title: Optional[str] = None
    folder_id: Optional[int] = None
    content_html: Optional[str] = None


class NoteUpdate(SQLModel):
    title: Optional[str] = None
    folder_id: Optional[int] = None
    content_html: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_deleted: Optional[bool] = None


class AttachmentBase(SQLModel):
    filename: str
    url: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Attachment(AttachmentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    note_id: int = Field(foreign_key="note.id")

    note: Note = Relationship(back_populates="attachments")


class SearchResult(SQLModel):
    id: int
    title: str
    snippet: str
    folder_id: Optional[int]
    updated_at: datetime
