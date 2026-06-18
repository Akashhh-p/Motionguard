import base64
import time
import cv2
import numpy as np
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Detection, MotionEvent, User, Video, Zone, ZoneEvent
from ..schemas_detection import FrameDetectionRequest
from ..security import get_current_user, sync_user_from_claims, verify_firebase_token
from ..services.audit_service import audit
from ..services.motion_service import detect_motion_regions
from ..services.settings_service import get_or_create_settings, settings_classes
from ..services.video_service import process_video_job, save_upload
from ..services.webcam_service import webcam_manager
from ..services.yolo_service import detect_frame
from ..utils.geometry_utils import point_in_polygon
from ..utils.time_utils import utc_iso


router = APIRouter(prefix="/detection", tags=["detection"])


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


def normalized_center(box: list[float], width: int, height: int) -> tuple[float, float]:
    x1, y1, x2, y2 = box
    return ((x1 + x2) / 2 / max(width, 1), (y1 + y2) / 2 / max(height, 1))


@router.post("/frame")
def detect_single_frame(payload: FrameDetectionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    started = time.perf_counter()
    frame = decode_base64_frame(payload.image)
    height, width = frame.shape[:2]
    settings = get_or_create_settings(db, current_user)
    detections = detect_frame(frame, settings.confidence_threshold, settings_classes(settings))
    motion = detect_motion_regions(current_user.id, frame, min_area=int(700 + (1 - settings.detection_sensitivity) * 2000))
    zones = db.query(Zone).filter(Zone.user_id == current_user.id).all()
    alerts: list[dict] = []

    for detection in detections:
        db.add(
            Detection(
                user_id=current_user.id,
                object_class=detection["object_class"],
                confidence=detection["confidence"],
                source_type=payload.source_type,
                bbox=",".join(str(round(v, 2)) for v in detection["bbox"]),
            )
        )
        if detection["object_class"] == "person":
            center = normalized_center(detection["bbox"], width, height)
            for zone in zones:
                coords = __import__("json").loads(zone.coordinates)
                if point_in_polygon(center, coords):
                    detection["alert"] = True
                    db.add(ZoneEvent(user_id=current_user.id, zone_id=zone.id, event_type="Person Detected Inside Zone", motion_count=0, object_count=1, screenshot_path=None))
                    alerts.append({"zone_id": zone.id, "zone_name": zone.name})
    if motion["motion_detected"]:
        db.add(MotionEvent(user_id=current_user.id, event_type="Motion Event", source_type=payload.source_type, motion_count=motion["motion_count"], estimated_moving_subjects=motion["estimated_moving_subjects"], motion_area_total=motion["motion_area_total"], motion_area=motion["motion_area_total"], status="open"))
    db.commit()
    fps = 1.0 / max(time.perf_counter() - started, 1e-6)
    return {
        "detections": [
            {"class_name": item["object_class"], "confidence": item["confidence"], "bbox": item["bbox"], "alert": item.get("alert", False)}
            for item in detections
        ],
        "fps": round(fps, 1),
        "frame_width": width,
        "frame_height": height,
        "motion_detected": motion["motion_detected"],
        "motion_boxes": motion["motion_boxes"],
        "object_count": len(detections),
        "alerts": alerts,
    }


@router.post("/upload-video")
async def upload_video(background_tasks: BackgroundTasks, request: Request, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    video = await save_upload(db, current_user, file)
    audit(db, current_user, "upload", f"Uploaded video {video.filename}.", request)
    background_tasks.add_task(process_video_job, current_user.id, video.id)
    return {"message": "Video queued for background processing.", "video_id": video.id, "status": video.processing_status}


@router.get("/videos/{video_id}/status")
def video_status(video_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    video = db.query(Video).filter(Video.id == video_id, Video.user_id == current_user.id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")
    return {"video_id": video.id, "status": video.processing_status, "error": video.processing_error, "processed_path": video.processed_path}


@router.post("/process-video")
def process_video(background_tasks: BackgroundTasks, video_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    video = db.query(Video).filter(Video.id == video_id, Video.user_id == current_user.id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")
    background_tasks.add_task(process_video_job, current_user.id, video.id)
    return {"job_id": video.id, "video_id": video.id, "status": "queued"}


@router.get("/video-status/{job_id}")
def video_job_status(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return video_status(job_id, db, current_user)


@router.get("/video-results/{job_id}")
def video_results(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    video = db.query(Video).filter(Video.id == job_id, Video.user_id == current_user.id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")
    detections = db.query(Detection).filter(Detection.user_id == current_user.id, Detection.video_id == video.id).order_by(Detection.timestamp.desc()).limit(200).all()
    return {
        "job_id": video.id,
        "status": video.processing_status,
        "detections": [{"class_name": d.object_class, "confidence": d.confidence, "bbox": d.bbox, "timestamp": utc_iso(d.timestamp)} for d in detections],
    }


@router.post("/start-webcam")
def start_webcam(camera_index: int = 0, current_user: User = Depends(get_current_user)):
    return webcam_manager.start(current_user, camera_index)


@router.post("/stop-webcam")
def stop_webcam(current_user: User = Depends(get_current_user)):
    return webcam_manager.stop(current_user.id)


@router.get("/status")
def status(current_user: User = Depends(get_current_user)):
    return webcam_manager.status.get(current_user.id, {"running": False, "fps": 0, "detections": 0, "message": "Idle"})


@router.get("/webcam-stream")
def webcam_stream(token: str = Query(...), db: Session = Depends(get_db)):
    claims = verify_firebase_token(token)
    user = sync_user_from_claims(db, claims)
    return StreamingResponse(webcam_manager.stream(user.id), media_type="multipart/x-mixed-replace; boundary=frame")
