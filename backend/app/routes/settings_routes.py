from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import SettingsIn
from ..security import get_current_user
from ..services.settings_service import get_or_create_settings
from ..services.audit_service import audit
import json


router = APIRouter(prefix="/settings", tags=["settings"])


def serialize(settings):
    return {
        "id": settings.id,
        "user_id": settings.user_id,
        "confidence_threshold": settings.confidence_threshold,
        "alert_sound": settings.alert_sound,
        "evidence_capture": settings.evidence_capture,
        "screenshot_save_folder": settings.screenshot_save_folder,
        "video_clip_save": settings.video_clip_save,
        "frame_skip": settings.frame_skip,
        "theme": settings.theme,
        "detection_sensitivity": settings.detection_sensitivity,
        "allowed_object_classes": [item.strip() for item in settings.allowed_object_classes.split(",") if item.strip()],
        "dashboard_layout": json.loads(settings.dashboard_layout),
        "default_landing_page": settings.default_landing_page,
    }


@router.get("")
def get_settings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return serialize(get_or_create_settings(db, current_user))


@router.put("")
def update_settings(payload: SettingsIn, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    settings = get_or_create_settings(db, current_user)
    for key, value in payload.model_dump().items():
        if key == "allowed_object_classes":
            setattr(settings, key, ",".join(value))
        elif key == "dashboard_layout":
            setattr(settings, key, json.dumps(value))
        else:
            setattr(settings, key, value)
    db.commit()
    db.refresh(settings)
    audit(db, current_user, "settings_change", "Updated detection/dashboard settings.", request)
    return serialize(settings)
