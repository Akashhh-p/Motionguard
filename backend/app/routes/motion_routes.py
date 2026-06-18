import base64
import json
import logging
import time
from datetime import timedelta

import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import Evidence, MotionEvent, User, Zone, ZoneEvent
from ..security import get_current_user
from ..services.motion_service import detect_motion_regions
from ..services.settings_service import get_or_create_settings
from ..utils.geometry_utils import point_in_polygon
from ..utils.time_utils import utc_day_bounds, utc_filename_stamp, utc_now


router = APIRouter(prefix="/motion", tags=["motion"])
logger = logging.getLogger(__name__)


class MotionFrameRequest(BaseModel):
    image: str = Field(description="Base64 data URL or raw base64 JPEG/PNG frame.")
    source_type: str = "webcam"
    sensitivity: float | None = Field(default=None, ge=0.1, le=1.0)
    min_area: int = Field(default=500, ge=100, le=50000)
    learning_rate: float = Field(default=-1)
    cooldown_seconds: int | None = Field(default=None, ge=5, le=120)
    blur_kernel: int = Field(default=5, ge=3, le=31)
    morph_iterations: int = Field(default=2, ge=1, le=6)
    resize_width: int = Field(default=640, ge=320, le=1280)


def decode_base64_frame(image: str):
    payload = image.split(",", 1)[1] if "," in image else image
    try:
        raw = base64.b64decode(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid base64 image frame.") from exc
    array = np.frombuffer(raw, dtype=np.uint8)
    frame = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Frame could not be decoded.")
    logger.info("Decoded motion frame shape=%s", frame.shape)
    return frame


def user_storage_dir(user_id: int, name: str):
    settings = get_settings()
    path = settings.storage_dir / f"user_{user_id}" / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_motion_screenshot(user: User, frame) -> str:
    folder = user_storage_dir(user.id, "motion")
    filename = f"motion_{utc_filename_stamp()}.jpg"
    path = folder / filename
    cv2.imwrite(str(path), frame)
    return str(path)


def normalized_box_center(box: dict, width: int, height: int) -> tuple[float, float]:
    x1, y1, x2, y2 = box["bbox"]
    return ((x1 + x2) / 2 / max(width, 1), (y1 + y2) / 2 / max(height, 1))


def create_motion_records(db: Session, user: User, frame, boxes: list[dict], width: int, height: int, source_type: str, cooldown_seconds: int | None = None) -> list[dict]:
    settings = get_settings()
    user_settings = get_or_create_settings(db, user)
    cooldown = cooldown_seconds or settings.event_cooldown_seconds
    since = utc_now() - timedelta(seconds=cooldown)
    existing = (
        db.query(MotionEvent)
        .filter(MotionEvent.user_id == user.id, MotionEvent.timestamp >= since)
        .order_by(MotionEvent.timestamp.desc())
        .first()
    )
    if existing:
        return []

    screenshot_path = save_motion_screenshot(user, frame) if user_settings.evidence_capture else None
    total_area = float(sum(item["area"] for item in boxes))
    estimated = len(boxes)
    event = MotionEvent(
        user_id=user.id,
        event_type="Motion Event",
        source_type=source_type,
        motion_count=len(boxes),
        estimated_moving_subjects=estimated,
        motion_area_total=total_area,
        motion_area=total_area,
        screenshot_path=screenshot_path,
        status="open",
    )
    db.add(event)

    if screenshot_path:
        db.add(Evidence(user_id=user.id, evidence_path=screenshot_path, object_class="motion", evidence_type="screenshot"))

    alerts: list[dict] = []
    zones = db.query(Zone).filter(Zone.user_id == user.id).all()
    for box in boxes:
        center = normalized_box_center(box, width, height)
        for zone in zones:
            coordinates = json.loads(zone.coordinates)
            if point_in_polygon(center, coordinates):
                db.add(ZoneEvent(
                    user_id=user.id,
                    zone_id=zone.id,
                    event_type="Motion Detected Inside Zone",
                    motion_count=len(boxes),
                    object_count=0,
                    screenshot_path=screenshot_path,
                ))
                alerts.append({"zone_id": zone.id, "zone_name": zone.name})
                break

    db.commit()
    return alerts


@router.post("/frame")
def detect_motion_frame(payload: MotionFrameRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    started = time.perf_counter()
    frame = decode_base64_frame(payload.image)
    height, width = frame.shape[:2]
    settings = get_or_create_settings(db, current_user)
    sensitivity = payload.sensitivity if payload.sensitivity is not None else settings.detection_sensitivity
    min_area = payload.min_area or int(450 + (1 - sensitivity) * 2600)
    motion = detect_motion_regions(
        current_user.id,
        frame,
        threshold=16,
        min_area=min_area,
        learning_rate=payload.learning_rate,
        blur_kernel=payload.blur_kernel,
        morph_iterations=payload.morph_iterations,
        resize_width=payload.resize_width,
    )
    alerts = create_motion_records(db, current_user, frame, motion["motion_boxes"], width, height, payload.source_type, payload.cooldown_seconds) if motion["motion_detected"] else []
    fps = 1.0 / max(time.perf_counter() - started, 1e-6)
    logger.info(
        "Motion frame shape=%s fps=%.1f contours=%s boxes=%s foreground=%s",
        frame.shape,
        fps,
        motion.get("debug", {}).get("contours_found"),
        motion.get("debug", {}).get("boxes_after_filter"),
        motion.get("debug", {}).get("foreground_pixels"),
    )
    today_start, _ = utc_day_bounds(utc_now().date())
    events_today = db.query(MotionEvent).filter(MotionEvent.user_id == current_user.id, MotionEvent.timestamp >= today_start).count()
    return {
        "success": True,
        "motion_detected": motion["motion_detected"],
        "motion_boxes": motion["motion_boxes"],
        "fps": round(fps, 1),
        "frame_width": width,
        "frame_height": height,
        "alerts": alerts,
        "motion_count": motion["motion_count"],
        "estimated_moving_subjects": motion["estimated_moving_subjects"],
        "motion_area_total": motion["motion_area_total"],
        "motion_events_today": events_today,
        "debug": motion["debug"],
    }
