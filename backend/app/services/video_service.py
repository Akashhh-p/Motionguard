import json
from pathlib import Path
import cv2
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from ..config import get_settings
from ..models import Detection, User, Video, Zone, ZoneEvent
from ..utils.file_utils import sanitize_filename, storage_subdir
from ..utils.geometry_utils import point_in_polygon
from ..utils.time_utils import utc_filename_stamp
from .settings_service import get_or_create_settings, settings_classes
from .yolo_service import detect_frame, draw_detections, resize_to_width


ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
ALLOWED_MIME_PREFIXES = ("video/", "application/octet-stream")


async def save_upload(db: Session, user: User, file: UploadFile) -> Video:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported video format.")
    if file.content_type and not file.content_type.startswith(ALLOWED_MIME_PREFIXES):
        raise HTTPException(status_code=400, detail="Unsupported video MIME type.")

    safe_name = f"{utc_filename_stamp()}_{sanitize_filename(file.filename or 'video.mp4')}"
    destination = storage_subdir("uploads") / f"user{user.id}_{safe_name}"
    max_bytes = get_settings().max_upload_mb * 1024 * 1024
    written = 0
    with destination.open("wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            written += len(chunk)
            if written > max_bytes:
                destination.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Video upload is too large.")
            buffer.write(chunk)

    video = Video(user_id=user.id, filename=safe_name, file_path=str(destination), source_type="upload", processing_status="queued")
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


def process_video(db: Session, user: User, video: Video) -> dict:
    video.processing_status = "processing"
    video.processing_error = None
    db.commit()
    settings = get_or_create_settings(db, user)
    zones = db.query(Zone).filter_by(user_id=user.id).all()
    zone_payloads = [(zone.id, zone.name, json.loads(zone.coordinates)) for zone in zones]

    capture = cv2.VideoCapture(video.file_path)
    if not capture.isOpened():
        raise HTTPException(status_code=400, detail="Uploaded video could not be opened.")

    fps = capture.get(cv2.CAP_PROP_FPS) or 20
    processed_path = storage_subdir("processed") / f"user{user.id}_processed_{Path(video.filename).stem}.mp4"
    writer = None
    frame_index = 0
    detection_count = 0
    zone_event_count = 0

    allowed = settings_classes(settings)
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        frame_index += 1
        frame = resize_to_width(frame, get_settings().default_frame_width)
        if writer is None:
            h, w = frame.shape[:2]
            writer = cv2.VideoWriter(str(processed_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

        detections = []
        if frame_index % max(1, settings.frame_skip) == 0:
            detections = detect_frame(frame, settings.confidence_threshold, allowed)
            for detection in detections:
                detection_count += 1
                db.add(
                    Detection(
                        user_id=user.id,
                        object_class=detection["object_class"],
                        confidence=detection["confidence"],
                        source_type="upload",
                        video_id=video.id,
                        bbox=",".join(str(round(v, 2)) for v in detection["bbox"]),
                    )
                )
                if detection["object_class"] == "person":
                    x1, y1, x2, y2 = detection["bbox"]
                    height, width = frame.shape[:2]
                    center = (((x1 + x2) / 2) / max(width, 1), ((y1 + y2) / 2) / max(height, 1))
                    for zone_id, zone_name, coords in zone_payloads:
                        if point_in_polygon(center, coords):
                            detection["alert"] = True
                            db.add(ZoneEvent(user_id=user.id, zone_id=zone_id, event_type="Person Detected Inside Zone", motion_count=0, object_count=1, screenshot_path=None))
                            zone_event_count += 1
            db.commit()
        writer.write(draw_detections(frame, detections, ["Zone Event"] if zone_event_count else None))

    capture.release()
    if writer:
        writer.release()
    video.processed_path = str(processed_path)
    video.processing_status = "completed"
    db.commit()
    return {"video_id": video.id, "detections": detection_count, "zone_events": zone_event_count, "processed_path": str(processed_path)}


def process_video_job(user_id: int, video_id: int) -> None:
    from ..database import SessionLocal

    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        video = db.query(Video).filter(Video.id == video_id, Video.user_id == user_id).first()
        if not user or not video:
            return
        process_video(db, user, video)
    except Exception as exc:
        video = db.query(Video).filter(Video.id == video_id, Video.user_id == user_id).first()
        if video:
            video.processing_status = "failed"
            video.processing_error = str(exc)
            db.commit()
    finally:
        db.close()
