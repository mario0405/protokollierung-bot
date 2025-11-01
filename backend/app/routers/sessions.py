from __future__ import annotations

import datetime as dt
import re
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import SessionLocal, get_session
from ..models import AppSettings, RecordingSession
from ..schemas import (
    FinalizeResponse,
    SessionCreateResponse,
    SessionDetail,
    SessionListItem,
    SettingsPayload,
    TranscriptResponse,
)
from ..services.audio import append_audio_chunk, ensure_storage_dir
from ..services.summarizer import summarize
from ..services.transcribe import transcribe_file

router = APIRouter(prefix="/api/sessions", tags=["sessions"])
settings = get_settings()


def _get_db_settings(db: Session) -> dict:
    settings_row = db.get(AppSettings, "default")
    if not settings_row:
        settings_row = AppSettings(id="default", data=SettingsPayload().model_dump())
        db.add(settings_row)
        db.commit()
        db.refresh(settings_row)
    data = settings_row.get_data() or {}
    if not data.get("sections"):
        defaults = SettingsPayload().model_dump()
        data = {**defaults, **data}
        settings_row.set_data(data)
        db.add(settings_row)
        db.commit()
        db.refresh(settings_row)
    return data


def _fallback_title(created_at: dt.datetime | None) -> str:
    if not created_at:
        return "Unbenannte Sitzung"
    return f"Sitzung vom {created_at.strftime('%d.%m.%Y %H:%M')}"


def _generate_session_title(transcript: str, summary: dict[str, Any] | None, created_at: dt.datetime | None) -> str:
    candidates: list[str] = []
    if summary:
        sections = summary.get("sections") or {}
        if isinstance(sections, dict):
            for value in sections.values():
                if isinstance(value, str):
                    snippet = value.strip().splitlines()[0].strip()
                    if snippet:
                        candidates.append(snippet)
        raw = summary.get("raw")
        if isinstance(raw, str) and raw.strip():
            candidates.append(raw.strip().splitlines()[0].strip())
    transcript = transcript.strip()
    if transcript:
        sentences = re.split(r"(?<=[.!?])\s+", transcript)
        if sentences:
            candidates.append(sentences[0].strip())
    for candidate in candidates:
        text = candidate.strip().strip(" -–—")
        if not text:
            continue
        lowered = text.lower()
        if lowered.startswith("keine inhalte"):
            continue
        return (text[:120] + "…") if len(text) > 120 else text
    return _fallback_title(created_at)


@router.post("", response_model=SessionCreateResponse, status_code=201)
def create_session(db: Session = Depends(get_session)) -> SessionCreateResponse:
    session_id = str(uuid.uuid4())
    app_settings = _get_db_settings(db)
    session_obj = RecordingSession(
        id=session_id,
        status="recording",
        language=app_settings.get("language", "de"),
        settings_snapshot=app_settings,
    )
    storage_dir = ensure_storage_dir(settings.storage_dir, session_id)
    session_obj.audio_path = str(storage_dir / "audio.raw")
    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)
    ws_url = f"/api/sessions/{session_id}/stream"
    return SessionCreateResponse(id=session_id, websocket_url=ws_url, created_at=session_obj.created_at)


@router.get("", response_model=list[SessionListItem])
def list_sessions(db: Session = Depends(get_session)) -> list[SessionListItem]:
    sessions = (
        db.query(RecordingSession)
        .order_by(RecordingSession.created_at.desc())
        .all()
    )
    return [
        SessionListItem(
            id=s.id,
            created_at=s.created_at,
            updated_at=s.updated_at,
            status=s.status,
            has_transcript=bool(s.transcript_text),
            title=s.title or _fallback_title(s.created_at),
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionDetail)
def get_session_detail(session_id: str, db: Session = Depends(get_session)) -> SessionDetail:
    session_obj = db.get(RecordingSession, session_id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Sitzung nicht gefunden")
    return SessionDetail(
        id=session_obj.id,
        created_at=session_obj.created_at,
        updated_at=session_obj.updated_at,
        status=session_obj.status,
        has_transcript=bool(session_obj.transcript_text),
        title=session_obj.title or _fallback_title(session_obj.created_at),
        language=session_obj.language,
        summary=session_obj.summary_json,
    )


@router.get("/{session_id}/transcript", response_model=TranscriptResponse)
def get_transcript(session_id: str, db: Session = Depends(get_session)) -> TranscriptResponse:
    session_obj = db.get(RecordingSession, session_id)
    if not session_obj or not session_obj.transcript_text:
        raise HTTPException(status_code=404, detail="Transkript nicht gefunden")
    return TranscriptResponse(transcript=session_obj.transcript_text, summary=session_obj.summary_json or {})


@router.post("/{session_id}/finalize", response_model=FinalizeResponse)
async def finalize_session(session_id: str, db: Session = Depends(get_session)) -> FinalizeResponse:
    session_obj = db.get(RecordingSession, session_id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Sitzung nicht gefunden")
    if not session_obj.audio_path:
        raise HTTPException(status_code=400, detail="Keine Audiodaten")
    audio_path = Path(session_obj.audio_path)
    if not audio_path.exists():
        raise HTTPException(status_code=400, detail="Audiodatei fehlt")

    transcription = await transcribe_file(audio_path, language=session_obj.language)
    summary_input = transcription.get("clean_text") or transcription.get("text", "")
    summary = await summarize(summary_input, session_obj.settings_snapshot or {})

    session_obj.status = "completed"
    session_obj.title = _generate_session_title(summary_input, summary, session_obj.created_at)
    session_obj.transcript_text = transcription["text"]
    session_obj.transcript_json = transcription
    session_obj.summary_json = summary
    try:
        session_obj.audio_bytes = audio_path.read_bytes()
    except Exception:
        session_obj.audio_bytes = None
    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)
    return FinalizeResponse(
        id=session_obj.id,
        status=session_obj.status,
        transcript=session_obj.transcript_text,
        summary=session_obj.summary_json or {},
        title=session_obj.title,
    )


@router.websocket("/{session_id}/stream")
async def stream_audio(websocket: WebSocket, session_id: str):
    await websocket.accept()
    with SessionLocal() as db:
        session_obj = db.get(RecordingSession, session_id)
        if not session_obj:
            await websocket.send_json({"error": "Sitzung nicht gefunden"})
            await websocket.close(code=1008)
            return
        audio_path = Path(session_obj.audio_path)

    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
            if "bytes" in message and message["bytes"]:
                append_audio_chunk(audio_path, message["bytes"])
                await websocket.send_json({"ok": True, "bytes": len(message["bytes"])} )
            elif "text" in message:
                data = message["text"]
                if data == "stop":
                    await websocket.send_json({"ok": True, "event": "stopped"})
                    break
                await websocket.send_json({"ok": True})
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        await websocket.send_json({"error": str(exc)})
    finally:
        await websocket.close()

