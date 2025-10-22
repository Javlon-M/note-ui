from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from ..core.config import settings

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/")
async def upload_file(file: UploadFile = File(...)) -> dict:
    suffix = Path(file.filename).suffix or ""
    name = secrets.token_hex(16) + suffix
    dest = settings.media_dir / name
    try:
        data = await file.read()
        dest.write_bytes(data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {exc}")
    url = f"/media/{name}"
    return {"url": url, "filename": file.filename}
