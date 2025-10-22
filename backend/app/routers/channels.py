from __future__ import annotations

from fastapi import APIRouter

from ..core.config import settings

router = APIRouter(prefix="/channels", tags=["channels"])


@router.get("/")
def list_channels() -> list[dict[str, str]]:
    return settings.get_channels()
