from __future__ import annotations

import asyncio
import os
import re
import tempfile
import wave
from pathlib import Path
from typing import Any, Iterable

from faster_whisper import WhisperModel

from ..config import get_settings

settings = get_settings()
_model_instance: WhisperModel | None = None

_NOISY_CHAR_PATTERN = re.compile(r"[^a-zA-ZäöüÄÖÜß\s,.?!-]")


def get_model() -> WhisperModel:
    global _model_instance
    if _model_instance is None:
        _model_instance = WhisperModel(settings.whisper_model, device="auto")
    return _model_instance


def _clean_transcript_segments(segment_texts: Iterable[str]) -> str:
    cleaned_lines: list[str] = []
    for raw_line in segment_texts:
        text = raw_line.strip()
        if len(text.split()) < 3:
            continue
        if _NOISY_CHAR_PATTERN.search(text):
            continue
        text = (
            text.replace(" ,", ",")
            .replace(" .", ".")
            .replace(" ?", "?")
            .replace(" !", "!")
        )
        if text:
            text = text[0].upper() + text[1:]
            cleaned_lines.append(text)
    return "\n".join(cleaned_lines)


async def transcribe_file(path: Path, language: str | None = None) -> dict[str, Any]:
    model = get_model()

    def _run():
        audio_input: str
        temp_path: str | None = None
        if path.suffix.lower() in {".wav", ".mp3", ".m4a", ".flac", ".ogg"}:
            audio_input = str(path)
        else:
            raw = path.read_bytes()
            if not raw:
                raise ValueError("Audiodatei ist leer")
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_path = temp_file.name
            temp_file.close()
            with wave.open(temp_path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(48000)
                wav_file.writeframes(raw)
            audio_input = temp_path
        try:
            segments, info = model.transcribe(audio_input, language=language)
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
        segment_list: list[dict[str, Any]] = []
        segment_texts: list[str] = []
        for segment in segments:
            text = segment.text.strip()
            segment_list.append(
                {
                    "id": segment.id,
                    "start": segment.start,
                    "end": segment.end,
                    "text": text,
                }
            )
            segment_texts.append(text)
        raw_text = " ".join(segment_texts)
        clean_text = _clean_transcript_segments(segment_texts)
        return {
            "language": info.language,
            "duration": info.duration,
            "segments": segment_list,
            "text": raw_text,
            "clean_text": clean_text,
        }

    return await asyncio.to_thread(_run)
