from __future__ import annotations

import datetime as dt
import json
from typing import Any

from sqlalchemy import Column, DateTime, LargeBinary, String, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB

from .database import Base, engine


def _json_column():
    if engine.dialect.name == "postgresql":
        return JSONB
    return JSON


class RecordingSession(Base):
    __tablename__ = "recording_sessions"

    id = Column(String(36), primary_key=True)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)
    status = Column(String(32), default="recording", nullable=False)
    title = Column(String(255), nullable=True)
    language = Column(String(16), default="de", nullable=False)
    audio_path = Column(String(512), nullable=True)
    audio_bytes = Column(LargeBinary, nullable=True)
    transcript_text = Column(Text, nullable=True)
    transcript_json = Column(_json_column(), nullable=True)
    summary_json = Column(_json_column(), nullable=True)
    settings_snapshot = Column(_json_column(), nullable=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "status": self.status,
            "title": self.title,
            "language": self.language,
            "audio_path": self.audio_path,
            "has_audio_blob": self.audio_bytes is not None,
            "has_transcript": self.transcript_text is not None,
            "summary": self.summary_json,
        }


class AppSettings(Base):
    __tablename__ = "app_settings"

    id = Column(String(36), primary_key=True, default="default")
    data = Column(_json_column(), nullable=False, default=dict)

    def get_data(self) -> dict[str, Any]:
        if isinstance(self.data, (bytes, str)):
            return json.loads(self.data)
        return self.data or {}

    def set_data(self, value: dict[str, Any]) -> None:
        self.data = value

