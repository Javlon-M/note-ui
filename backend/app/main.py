from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .core.config import settings
from .routers import channels, publish


app = FastAPI(title=settings.app_name, debug=settings.debug)

# CORS (allow same-origin + local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers under /api
app.include_router(channels.router, prefix="/api")
app.include_router(publish.router, prefix="/api")


@app.on_event("startup")
def on_startup() -> None:
    # stateless backend - nothing to initialize
    pass


# Static files (frontend) and media
frontend_dir = settings.frontend_dir
if not frontend_dir.exists():
    # Best-effort to derive from project root
    candidate = Path(__file__).resolve().parents[3] / "frontend"
    frontend_dir = candidate if candidate.exists() else Path(os.getcwd()) / "frontend"

app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
