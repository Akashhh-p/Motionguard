from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Detection, Evidence, EvidenceDetection, MotionEvent, Report, User, Zone, ZoneEvent
from ..security import get_current_user
from ..utils.time_utils import ensure_utc, utc_day_bounds, utc_iso, utc_now


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    today_start, _ = utc_day_bounds(utc_now().date())

    motion_query = db.query(MotionEvent).filter(MotionEvent.user_id == current_user.id)
    evidence_query = db.query(Evidence).filter(Evidence.user_id == current_user.id)
    zones_query = db.query(Zone).filter(Zone.user_id == current_user.id)
    zone_events_query = db.query(ZoneEvent).filter(ZoneEvent.user_id == current_user.id)
    detections_query = db.query(EvidenceDetection).filter(EvidenceDetection.user_id == current_user.id)

    last_motion = motion_query.order_by(MotionEvent.timestamp.desc()).first()
    recent_motion_events = [
        {
            "id": item.id,
            "event_type": item.event_type,
            "source_type": item.source_type,
            "motion_count": item.motion_count,
            "estimated_moving_subjects": item.estimated_moving_subjects,
            "motion_area_total": item.motion_area_total,
            "timestamp": utc_iso(item.timestamp),
        }
        for item in motion_query.order_by(MotionEvent.timestamp.desc()).limit(5).all()
    ]
    recent_evidence = [
        {
            "id": item.id,
            "object_class": item.object_class,
            "evidence_type": item.evidence_type,
            "created_at": utc_iso(item.created_at),
        }
        for item in evidence_query.order_by(Evidence.created_at.desc()).limit(5).all()
    ]
    active_zones = [
        {
            "id": item.id,
            "name": item.name,
            "zone_type": item.zone_type,
            "source_type": item.source_type,
            "created_at": utc_iso(item.created_at),
        }
        for item in zones_query.order_by(Zone.created_at.desc()).limit(5).all()
    ]
    recent_zone_events = [
        {
            "id": item.id,
            "event_type": item.event_type,
            "zone_id": item.zone_id,
            "motion_count": item.motion_count,
            "object_count": item.object_count,
            "timestamp": utc_iso(item.timestamp),
        }
        for item in zone_events_query.order_by(ZoneEvent.timestamp.desc()).limit(5).all()
    ]

    timeline = build_activity_timeline(motion_query, evidence_query, detections_query, zone_events_query)

    return {
        "motion_events_today": motion_query.filter(MotionEvent.timestamp >= today_start).count(),
        "evidence_items": evidence_query.count(),
        "active_zones": zones_query.count(),
        "last_motion_time": utc_iso(last_motion.timestamp) if last_motion else None,
        "latest_motion_count": last_motion.motion_count if last_motion else 0,
        "latest_motion_source": last_motion.source_type if last_motion else None,
        "recent_motion_events": recent_motion_events,
        "recent_evidence": recent_evidence,
        "active_zone_items": active_zones,
        "recent_zone_events": recent_zone_events,
        "activity_timeline": timeline,
    }


@router.get("/workflow-status")
def workflow_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    counts = {
        "live_motion": db.query(MotionEvent).filter(MotionEvent.user_id == current_user.id).count(),
        "evidence_capture": db.query(Evidence).filter(Evidence.user_id == current_user.id).count(),
        "object_analysis": db.query(EvidenceDetection).filter(EvidenceDetection.user_id == current_user.id).count(),
        "zone_monitoring": db.query(ZoneEvent).filter(ZoneEvent.user_id == current_user.id).count(),
        "report_ready": db.query(Report).filter(Report.user_id == current_user.id).count(),
    }
    active_key = next((key for key, count in reversed(list(counts.items())) if count > 0), None)
    return {
        key: {
            "status": "active" if key == active_key else "completed" if active_key and count > 0 else "idle",
            "count": count,
        }
        for key, count in counts.items()
    }


def build_activity_timeline(motion_query, evidence_query, detections_query, zone_events_query) -> list[dict]:
    items: list[dict] = []
    for item in motion_query.order_by(MotionEvent.timestamp.desc()).limit(8).all():
        items.append({"id": f"motion-{item.id}", "label": "Motion Detected", "timestamp": utc_iso(item.timestamp), "source": item.source_type})
        if item.screenshot_path:
            items.append({"id": f"motion-capture-{item.id}", "label": "Screenshot Captured", "timestamp": utc_iso(item.timestamp), "source": item.source_type})
    for item in evidence_query.order_by(Evidence.created_at.desc()).limit(8).all():
        items.append({"id": f"evidence-{item.id}", "label": "Evidence Analysis Completed" if item.object_class else "Evidence Captured", "timestamp": utc_iso(item.created_at), "source": item.evidence_type})
    for item in detections_query.order_by(EvidenceDetection.detected_at.desc()).limit(8).all():
        label = "Human Detected in Evidence" if item.object_class == "person" else f"{item.object_class.title()} Detected in Evidence"
        items.append({"id": f"detection-{item.id}", "label": label, "timestamp": utc_iso(item.detected_at), "source": "evidence"})
    for item in zone_events_query.order_by(ZoneEvent.timestamp.desc()).limit(8).all():
        items.append({"id": f"zone-{item.id}", "label": "Zone Event Recorded", "timestamp": utc_iso(item.timestamp), "source": item.event_type})
    return sorted(items, key=lambda item: ensure_utc(item["timestamp"]) if not isinstance(item["timestamp"], str) else item["timestamp"], reverse=True)[:12]
