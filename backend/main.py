from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.config import get_settings
from app.database import Base, engine
from app.routers import sessions, settings as settings_router

settings = get_settings()
Base.metadata.create_all(bind=engine)


def _ensure_schema() -> None:
    inspector = inspect(engine)
    try:
        columns = {column["name"] for column in inspector.get_columns("recording_sessions")}
    except Exception:
        columns = set()
    if "title" not in columns:
        try:
            with engine.connect() as connection:
                connection.execute(text("ALTER TABLE recording_sessions ADD COLUMN title VARCHAR(255)"))
                connection.commit()
        except Exception:
            pass


_ensure_schema()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(settings_router.router)
app.include_router(sessions.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "bereit"}

