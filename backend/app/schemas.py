from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from pydantic import BaseModel, Field


class SettingsPayload(BaseModel):
    language: str = Field(default="de")
    tone: str = Field(default="praegnant")
    sections: list[str] = Field(
        default_factory=lambda: [
            "Agenda-Ueberblick",
            "Entscheidungen",
            "Aufgaben",
            "Verantwortliche",
            "Fristen",
            "Risiken",
            "Offene Punkte",
        ]
    )
    meeting_type: Optional[str] = None
    audience: Optional[str] = None
    objectives: Optional[str] = None
    notes: Optional[str] = None


class SettingsResponse(BaseModel):
    data: SettingsPayload


class SessionCreateResponse(BaseModel):
    id: str
    websocket_url: str
    created_at: dt.datetime


class SessionListItem(BaseModel):
    id: str
    created_at: Optional[dt.datetime]
    updated_at: Optional[dt.datetime]
    status: str
    has_transcript: bool
    title: Optional[str] = None


class SessionDetail(SessionListItem):
    language: str
    summary: Optional[dict[str, Any]] = None


class TranscriptResponse(BaseModel):
    transcript: str
    summary: dict[str, Any]


class FinalizeResponse(BaseModel):
    id: str
    status: str
    transcript: str
    summary: dict[str, Any]
    title: Optional[str] = None
