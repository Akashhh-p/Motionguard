import cv2
import base64
import logging
import time
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Detection, Evidence, EvidenceDetection, User
from ..security import get_current_user
from ..services.audit_service import audit
from ..services.yolo_service import detect_frame
from ..utils.file_utils import assert_storage_file
from ..utils.file_utils import sanitize_filename
from ..config import get_settings
from ..utils.time_utils import parse_utc, utc_filename_stamp, utc_iso
from ..schemas import BulkDeleteEvidenceRequest


router = APIRouter(prefix="/evidence", tags=["evidence"])
logger = logging.getLogger(__name__)


class ObjectDetectFrameRequest(BaseModel):
    image: str = Field(description="Base64 data URL or raw base64 JPEG/PNG frame.")
    confidence: float = Field(default=0.25, ge=0.05, le=0.95)


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
    logger.info("Decoded evidence frame shape=%s", frame.shape)
    return frame


@router.get("")
def list_evidence(
    object_class: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Evidence).filter(Evidence.user_id == current_user.id)
    if object_class:
        query = query.filter(Evidence.object_class == object_class)
    if date_from:
        query = query.filter(Evidence.created_at >= parse_utc(date_from))
    if date_to:
        query = query.filter(Evidence.created_at <= parse_utc(date_to))
    return [
        {
            "id": item.id,
            "object_class": item.object_class,
            "evidence_type": item.evidence_type,
            "created_at": utc_iso(item.created_at),
        }
        for item in query.order_by(Evidence.created_at.desc()).all()
    ]


def user_storage_dir(user_id: int, name: str):
    path = get_settings().storage_dir / f"user_{user_id}" / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def frame_from_evidence(path: str):
    file_path = assert_storage_file(path)
    suffix = file_path.suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
        frame = cv2.imread(str(file_path))
        if frame is None:
            raise HTTPException(status_code=400, detail="Evidence image could not be decoded.")
        return frame
    capture = cv2.VideoCapture(str(file_path))
    ok, frame = capture.read()
    capture.release()
    if not ok or frame is None:
        raise HTTPException(status_code=400, detail="Evidence video could not be decoded.")
    return frame


@router.post("/upload")
async def upload_evidence(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    safe_name = sanitize_filename(file.filename or "evidence.bin")
    suffix = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
    evidence_type = "video" if suffix in {"mp4", "mov", "avi", "mkv", "webm"} else "image"
    target_dir = user_storage_dir(current_user.id, "evidence")
    path = target_dir / f"{utc_filename_stamp()}_{safe_name}"
    max_bytes = get_settings().max_upload_mb * 1024 * 1024
    written = 0
    with path.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            written += len(chunk)
            if written > max_bytes:
                path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Evidence upload exceeds size limit.")
            out.write(chunk)
    evidence = Evidence(user_id=current_user.id, evidence_path=str(path), object_class=None, evidence_type=evidence_type)
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    audit(db, current_user, "evidence_uploaded", f"Uploaded evidence {evidence.id}.", request)
    return {"id": evidence.id, "evidence_type": evidence.evidence_type, "created_at": utc_iso(evidence.created_at)}


@router.post("/object-detect")
async def object_detect(
    request: Request,
    evidence_id: int | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    evidence: Evidence | None = None
    if evidence_id is not None:
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id, Evidence.user_id == current_user.id).first()
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found.")
    elif file is not None:
        upload = await upload_evidence(request, file, db, current_user)
        evidence = db.query(Evidence).filter(Evidence.id == upload["id"], Evidence.user_id == current_user.id).first()
    else:
        raise HTTPException(status_code=400, detail="Provide evidence_id or file.")

    frame = frame_from_evidence(evidence.evidence_path)
    height, width = frame.shape[:2]
    detections = detect_frame(frame, confidence=0.35, allowed_classes=None)

    db.query(EvidenceDetection).filter(EvidenceDetection.user_id == current_user.id, EvidenceDetection.evidence_id == evidence.id).delete()
    for item in detections:
        bbox = ",".join(str(round(v, 2)) for v in item["bbox"])
        db.add(
            EvidenceDetection(
                user_id=current_user.id,
                evidence_id=evidence.id,
                object_class=item["class_name"],
                confidence=item["confidence"],
            )
        )
        db.add(Detection(user_id=current_user.id, object_class=item["class_name"], confidence=item["confidence"], source_type="evidence", bbox=bbox))
    evidence.object_class = ",".join(sorted({item["class_name"] for item in detections})) or None
    db.commit()
    audit(db, current_user, "object_detection", f"Analyzed evidence {evidence.id}; {len(detections)} detections.", request)
    return {
        "evidence_id": evidence.id,
        "detections": [{"class_name": item["class_name"], "confidence": item["confidence"], "bbox": item["bbox"]} for item in detections],
        "frame_width": width,
        "frame_height": height,
    }


@router.post("/object-detect-frame")
def object_detect_frame(payload: ObjectDetectFrameRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    started = time.perf_counter()
    frame = decode_base64_frame(payload.image)
    height, width = frame.shape[:2]
    inference_started = time.perf_counter()
    detections = detect_frame(frame, confidence=payload.confidence, allowed_classes=None)
    inference_ms = round((time.perf_counter() - inference_started) * 1000, 2)
    human_count = sum(1 for item in detections if item["class_name"] == "person")
    fps = 1.0 / max(time.perf_counter() - started, 1e-6)
    logger.info("YOLO frame inference shape=%s inference_ms=%s detections=%s confidence=%s", frame.shape, inference_ms, len(detections), payload.confidence)
    return {
        "success": True,
        "detections": [{"class_name": item["class_name"], "confidence": item["confidence"], "bbox": item["bbox"]} for item in detections],
        "human_count": human_count,
        "object_count": len(detections),
        "fps": round(fps, 1),
        "frame_width": width,
        "frame_height": height,
        "debug": {
            "model_loaded": True,
            "input_shape": list(frame.shape),
            "detections_count": len(detections),
            "inference_ms": inference_ms,
            "confidence": payload.confidence,
        },
    }


@router.delete("/{evidence_id}")
def delete_evidence(evidence_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id, Evidence.user_id == current_user.id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found.")
    path = assert_storage_file(evidence.evidence_path)
    path.unlink(missing_ok=True)
    db.delete(evidence)
    db.commit()
    audit(db, current_user, "evidence_deleted", f"Deleted evidence {evidence_id}.", request)
    return {"message": "Evidence deleted."}


@router.post("/bulk-delete")
def bulk_delete_evidence(
    payload: BulkDeleteEvidenceRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete multiple evidence items belonging to current user."""
    if not payload.evidence_ids:
        raise HTTPException(status_code=400, detail="No evidence IDs provided.")
    
    # Get all evidence belonging to current user with IDs in the list
    evidence_items = db.query(Evidence).filter(
        Evidence.id.in_(payload.evidence_ids),
        Evidence.user_id == current_user.id
    ).all()
    
    deleted_count = 0
    skipped_count = len(payload.evidence_ids) - len(evidence_items)
    
    # Delete files and database records
    for evidence in evidence_items:
        try:
            # Delete physical file if it exists
            try:
                file_path = assert_storage_file(evidence.evidence_path)
                file_path.unlink(missing_ok=True)
            except HTTPException:
                pass  # File might not exist, continue with deletion
            
            # Delete from database
            db.delete(evidence)
            deleted_count += 1
        except Exception as exc:
            logger.exception("Error deleting evidence %s: %s", evidence.id, exc)
            skipped_count += 1
    
    db.commit()
    
    # Log the bulk deletion
    audit(
        db,
        current_user,
        "evidence_bulk_deleted",
        f"Deleted {deleted_count} evidence items. {skipped_count} skipped.",
        request,
    )
    
    return {
        "success": True,
        "deleted_count": deleted_count,
        "skipped_count": skipped_count,
        "message": f"{deleted_count} evidence items deleted." + (f" {skipped_count} skipped." if skipped_count > 0 else ""),
    }
