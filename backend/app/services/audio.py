from __future__ import annotations

from pathlib import Path


def ensure_storage_dir(base: Path, session_id: str) -> Path:
    session_dir = base / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def append_audio_chunk(path: Path, data: bytes) -> None:
    with path.open("ab") as f:
        f.write(data)


def write_audio_blob(path: Path, data: bytes) -> None:
    path.write_bytes(data)

