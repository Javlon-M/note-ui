from __future__ import annotations

from pathlib import Path
import json
import os
from typing import List, Dict

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    # Base
    app_name: str = Field(default="Apple Notes Web UI")
    debug: bool = Field(default=True)

    # Paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[3])
    frontend_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[3] / "frontend")

    # Telegram
    telegram_bot_token: str | None = Field(default=None)
    telegram_channel_id: str | None = Field(default=None, description="Default @channel_username or numeric chat id like -100123...")

    # Channels config (stateless)
    # Provide channels via env var TELEGRAM_CHANNELS as JSON, e.g.:
    #   [{"id":"-100123456","name":"My Channel"}, {"id":"@mychannel","name":"Public"}]
    # Or as CSV-like string: "My Channel=-100123456, Public=@mychannel"
    def get_channels(self) -> List[Dict[str, str]]:
        raw = os.getenv("TELEGRAM_CHANNELS", "").strip()
        if not raw:
            return []
        # Try JSON first
        try:
            data = json.loads(raw)
            result: List[Dict[str, str]] = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "id" in item and "name" in item:
                        result.append({"id": str(item["id"]), "name": str(item["name"])})
            if result:
                return result
        except Exception:
            pass
        # Fallback simple parser: "Name=-1001, Name2=@chan" or with ':'
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        parsed: List[Dict[str, str]] = []
        for p in parts:
            if "=" in p:
                name, cid = p.split("=", 1)
            elif ":" in p:
                name, cid = p.split(":", 1)
            else:
                continue
            name = name.strip()
            cid = cid.strip()
            if name and cid:
                parsed.append({"name": name, "id": cid})
        return parsed


settings = Settings()
