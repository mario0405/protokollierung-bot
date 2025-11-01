from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "Protocolito API"
    database_url: str = Field(
        default="sqlite:///./protocolito.db",
        alias="DATABASE_URL",
    )
    storage_dir: Path = Field(default=Path("storage"), alias="STORAGE_DIR")
    ollama_host: str = Field(default="http://ollama:11434", alias="OLLAMA_HOST")
    whisper_model: str = Field(default="base", alias="WHISPER_MODEL")
    summary_model: str = Field(default="llama3", alias="SUMMARY_MODEL")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    return settings

