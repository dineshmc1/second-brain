from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path

from platformdirs import user_data_dir
from pydantic_settings import BaseSettings, SettingsConfigDict


def _resource_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Second Brain"
    host: str = "127.0.0.1"
    port: int = 8765
    debug: bool = False
    model: str = "openai/gpt-5.4-nano"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_site_url: str = "https://secondbrain.local"
    openrouter_app_name: str = "Second Brain"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    data_dir: Path = Path(user_data_dir("Second Brain", "Second Brain"))
    allowed_origins: str = "http://localhost:3000,tauri://localhost,http://tauri.localhost"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SECOND_BRAIN_",
        extra="ignore",
    )

    @property
    def database_path(self) -> Path:
        return self.data_dir / "second_brain.sqlite3"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def exports_dir(self) -> Path:
        return self.data_dir / "exports"

    @property
    def resource_dir(self) -> Path:
        return _resource_dir()

    def ensure_directories(self) -> None:
        for path in (self.data_dir, self.uploads_dir, self.exports_dir):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    override = os.getenv("SECOND_BRAIN_DATA_DIR")
    if override:
        settings.data_dir = Path(override).expanduser().resolve()
    settings.ensure_directories()
    return settings
