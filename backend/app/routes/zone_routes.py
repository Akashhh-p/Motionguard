import base64
import json
import time

import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Detection, Evidence, MotionEvent, User, Zone, ZoneEvent
from ..schemas import ZoneIn
from ..security import get_current_user
from ..services.audit_service import audit
from ..services.motion_service import detect_motion_regions
from ..services.yolo_service import detect_frame
from ..utils.file_utils import storage_subdir
from ..utils.geometry_utils import point_in_polygon
from ..utils.time_utils import utc_filename_stamp
from ..services.zone_service import create_zone, list_zones, serialize_zone


router = APIRouter(prefix="/zones", tags=["zones"])


class ZoneFrameRequest(BaseModel):
    image: str = Field(description="Base64 data URL or raw base64 JPEG/PNG frame.")
    sensitivity: float = Field(default=0.65, ge=0.1, le=1.0)
    min_area: int = Field(default=900, ge=100, le=50000)
    cooldown_seconds: int = Field(default=15, ge=5, le=120)
    confidence: float = Field(default=0.35, ge=0.05, le=0.95)


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
    return frame


def load_zone(db: Session, user: User, zone_id: int) -> Zone:
    zone = db.query(Zone).filter(Zone.id == zone_id, Zone.user_id == user.id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found.")
    return zone


def normalized_center(box: list[float], width: int, height: int) -> tuple[float, float]:
    x1, y1, x2, y2 = box
    return ((x1 + x2) / 2 / max(width, 1), (y1 + y2) / 2 / max(height, 1))


def box_overlaps_zone(box: list[float], width: int, height: int, coordinates: list[dict[str, float]]) -> bool:
    x1, y1, x2, y2 = box
    candidates = [
        (x1 / max(width, 1), y1 / max(height, 1)),
        (x2 / max(width, 1), y1 / max(height, 1)),
        (x2 / max(width, 1), y2 / max(height, 1)),
        (x1 / max(width, 1), y2 / max(height, 1)),
        normalized_center(box, width, height),
    ]
    return any(point_in_polygon(point, coordinates) for point in candidates)


def save_zone_screenshot(user: User, frame) -> str:
    folder = storage_subdir("evidence")
    filename = f"user{user.id}_zone_{utc_filename_stamp()}.jpg"
    path = folder / filename
    cv2.imwrite(str(path), frame)
    return str(path)


def save_zone_event(db: Session, user: User, zone: Zone, event_type: str, motion_count: int, object_count: int, screenshot_path: str | None):
    event = ZoneEvent(
        user_id=user.id,
        zone_id=zone.id,
        event_type=event_type,
        motion_count=motion_count,
        object_count=object_count,
        screenshot_path=screenshot_path,
    )
    db.add(event)
    return event


def zone_response_base(zone: Zone, frame, started: float):
    height, width = frame.shape[:2]
    return {
        "success": True,
        "zone_id": zone.id,
        "zone_name": zone.name,
        "fps": round(1.0 / max(time.perf_counter() - started, 1e-6), 1),
        "frame_width": width,
        "frame_height": height,
    }


def analyze_zone_motion(db: Session, user: User, zone: Zone, frame, payload: ZoneFrameRequest) -> tuple[dict, bool]:
    height, width = frame.shape[:2]
    coordinates = json.loads(zone.coordinates)
    motion = detect_motion_regions(user.id * 100000 + zone.id, frame, min_area=payload.min_area, resize_width=640)
    inside_boxes = [{**box, "inside_zone": True} for box in motion["motion_boxes"] if box_overlaps_zone(box["bbox"], width, height, coordinates)]
    event_created = False
    if inside_boxes:
        screenshot_path = save_zone_screenshot(user, frame)
        save_zone_event(db, user, zone, "Motion Detected Inside Restricted Zone", len(inside_boxes), 0, screenshot_path)
        db.add(MotionEvent(user_id=user.id, event_type="Zone Motion Event", source_type="zone", motion_count=len(inside_boxes), estimated_moving_subjects=len(inside_boxes), motion_area_total=float(sum(item["area"] for item in inside_boxes)), motion_area=float(sum(item["area"] for item in inside_boxes)), screenshot_path=screenshot_path, status="open"))
        db.add(Evidence(user_id=user.id, evidence_path=screenshot_path, object_class="motion", evidence_type="screenshot"))
        event_created = True
        db.commit()
    return {
        "motion_detected": bool(inside_boxes),
        "motion_boxes": inside_boxes,
        "motion_count": len(inside_boxes),
        "estimated_moving_subjects": len(inside_boxes),
    }, event_created


def analyze_zone_objects(db: Session, user: User, zone: Zone, frame, payload: ZoneFrameRequest) -> tuple[dict, bool]:
    height, width = frame.shape[:2]
    coordinates = json.loads(zone.coordinates)
    detections = []
    for item in detect_frame(frame, payload.confidence, allowed_classes=None):
        if not point_in_polygon(normalized_center(item["bbox"], width, height), coordinates):
            continue
        detections.append({"class_name": item["class_name"], "confidence": item["confidence"], "bbox": item["bbox"], "inside_zone": True})
        db.add(Detection(user_id=user.id, object_class=item["class_name"], confidence=item["confidence"], source_type="zone", bbox=",".join(str(round(v, 2)) for v in item["bbox"])))
    human_count = sum(1 for item in detections if item["class_name"] == "person")
    event_created = False
    if detections:
        screenshot_path = save_zone_screenshot(user, frame)
        save_zone_event(db, user, zone, "Object Detected Inside Zone", 0, len(detections), screenshot_path)
        db.add(Evidence(user_id=user.id, evidence_path=screenshot_path, object_class=",".join(sorted({item["class_name"] for item in detections})), evidence_type="screenshot"))
        event_created = True
        db.commit()
    return {
        "detections": detections,
        "human_count": human_count,
        "object_count": len(detections),
    }, event_created


@router.get("")
def zones(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return [serialize_zone(zone) for zone in list_zones(db, current_user)]


@router.post("")
def add_zone(payload: ZoneIn, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    zone = create_zone(db, current_user, payload)
    audit(db, current_user, "zone_creation", f"Created zone {zone.name}.", request)
    return serialize_zone(zone)


@router.put("/{zone_id}")
def update_zone(zone_id: int, payload: ZoneIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    zone = db.query(Zone).filter(Zone.id == zone_id, Zone.user_id == current_user.id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found.")
    zone.name = payload.name
    zone.zone_type = payload.zone_type
    zone.coordinates = json.dumps(payload.coordinates)
    zone.source_type = payload.source_type
    db.commit()
    db.refresh(zone)
    return serialize_zone(zone)


@router.delete("/{zone_id}")
def delete_zone(zone_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    zone = db.query(Zone).filter(Zone.id == zone_id, Zone.user_id == current_user.id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found.")
    db.delete(zone)
    db.commit()
    return {"message": "Zone deleted."}


@router.post("/{zone_id}/motion-frame")
def zone_motion_frame(zone_id: int, payload: ZoneFrameRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    started = time.perf_counter()
    zone = load_zone(db, current_user, zone_id)
    frame = decode_base64_frame(payload.image)
    motion, event_created = analyze_zone_motion(db, current_user, zone, frame, payload)
    return {
        **zone_response_base(zone, frame, started),
        **motion,
        "event_created": event_created,
    }


@router.post("/{zone_id}/object-frame")
def zone_object_frame(zone_id: int, payload: ZoneFrameRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    started = time.perf_counter()
    zone = load_zone(db, current_user, zone_id)
    frame = decode_base64_frame(payload.image)
    objects, event_created = analyze_zone_objects(db, current_user, zone, frame, payload)
    return {
        **zone_response_base(zone, frame, started),
        **objects,
        "event_created": event_created,
    }


@router.post("/{zone_id}/analyze-frame")
def zone_analyze_frame(zone_id: int, payload: ZoneFrameRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    started = time.perf_counter()
    zone = load_zone(db, current_user, zone_id)
    frame = decode_base64_frame(payload.image)
    motion, motion_event = analyze_zone_motion(db, current_user, zone, frame, payload)
    objects, object_event = analyze_zone_objects(db, current_user, zone, frame, payload)
    return {
        **zone_response_base(zone, frame, started),
        "motion": {
            "motion_detected": motion["motion_detected"],
            "motion_boxes": motion["motion_boxes"],
            "motion_count": motion["motion_count"],
        },
        "objects": objects,
        "event_created": motion_event or object_event,
    }
