from __future__ import annotations

from pathlib import Path
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
    media_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2] / "media")

    # Database
    database_url: str = Field(default_factory=lambda: f"sqlite:///{(Path(__file__).resolve().parents[2] / 'data' / 'app.db').as_posix()}")

    # Telegram
    telegram_bot_token: str | None = Field(default=None)
    telegram_channel_id: str | None = Field(default=None, description="@channel_username or numeric chat id like -100123...")


settings = Settings()
