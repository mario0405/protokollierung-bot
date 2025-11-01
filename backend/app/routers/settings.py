from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_session
from ..models import AppSettings
from ..schemas import SettingsPayload, SettingsResponse

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _get_settings_row(db: Session) -> AppSettings:
    row = db.get(AppSettings, "default")
    if not row:
        row = AppSettings(id="default", data=SettingsPayload().model_dump())
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@router.get("", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_session)) -> SettingsResponse:
    row = _get_settings_row(db)
    return SettingsResponse(data=SettingsPayload(**row.get_data()))


@router.put("", response_model=SettingsResponse)
def update_settings(payload: SettingsPayload, db: Session = Depends(get_session)) -> SettingsResponse:
    row = _get_settings_row(db)
    row.set_data(payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return SettingsResponse(data=SettingsPayload(**row.get_data()))

