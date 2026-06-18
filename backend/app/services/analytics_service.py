from collections import Counter

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Detection, Evidence, EvidenceDetection, MotionEvent, User, ZoneEvent
from ..utils.time_utils import ensure_utc, utc_day_bounds, utc_iso, utc_now


VEHICLES = {"car", "truck", "bus", "motorcycle", "bicycle"}


def summary(db: Session, user: User) -> dict:
    today_start, _ = utc_day_bounds(utc_now().date())
    detections = db.query(Detection).filter(Detection.user_id == user.id)
    evidence = db.query(Evidence).filter(Evidence.user_id == user.id)
    motion_events = db.query(MotionEvent).filter(MotionEvent.user_id == user.id)
    zone_events = db.query(ZoneEvent).filter(ZoneEvent.user_id == user.id)
    all_detections = detections.all()
    today_motion = motion_events.filter(MotionEvent.timestamp >= today_start)
    last_motion = motion_events.order_by(MotionEvent.timestamp.desc()).first()
    return {
        "total_objects_detected": detections.count(),
        "people_detected": sum(1 for item in all_detections if item.object_class == "person"),
        "vehicles_detected": sum(1 for item in all_detections if item.object_class in VEHICLES),
        "evidence_captured": evidence.count(),
        "motion_events_today": today_motion.count(),
        "estimated_moving_subjects": int(today_motion.with_entities(func.coalesce(func.sum(MotionEvent.estimated_moving_subjects), 0)).scalar() or 0),
        "last_motion_detected": utc_iso(last_motion.timestamp) if last_motion else None,
        "highest_motion_area": int(today_motion.with_entities(func.coalesce(func.max(MotionEvent.motion_area_total), 0)).scalar() or 0),
        "evidence_objects_detected": db.query(EvidenceDetection).filter(EvidenceDetection.user_id == user.id).count(),
        "zone_events_today": zone_events.filter(ZoneEvent.timestamp >= today_start).count(),
    }


def charts(db: Session, user: User) -> dict:
    detections = db.query(Detection).filter(Detection.user_id == user.id).all()
    motion_events = db.query(MotionEvent).filter(MotionEvent.user_id == user.id).all()
    zone_events = db.query(ZoneEvent).filter(ZoneEvent.user_id == user.id).all()
    per_hour = Counter(ensure_utc(item.timestamp).strftime("%H:00") for item in detections)
    class_dist = Counter(item.object_class for item in detections)
    zone_dist = Counter(str(item.zone_id) for item in zone_events)
    return {
        "detections_per_hour": [{"label": key, "value": value} for key, value in sorted(per_hour.items())],
        "motion_trend": [{"label": key, "value": value} for key, value in sorted(Counter(ensure_utc(item.timestamp).strftime("%H:00") for item in motion_events).items())],
        "object_class_distribution": [{"label": key, "value": value} for key, value in class_dist.items()],
        "top_zones": [{"label": key, "value": value} for key, value in zone_dist.most_common(5)],
        "most_active_hours": [{"label": key, "value": value} for key, value in Counter(ensure_utc(item.timestamp).hour for item in detections).most_common(5)],
        "weekly_trends": trend_counts(motion_events, "%Y-W%W"),
        "monthly_trends": trend_counts(motion_events, "%Y-%m"),
    }


def trend_counts(items, fmt: str) -> list[dict]:
    counts = Counter(ensure_utc(item.timestamp).strftime(fmt) for item in items)
    return [{"label": key, "value": value} for key, value in sorted(counts.items())]


def daily_summary(db: Session, user: User) -> dict:
    data = summary(db, user)
    chart_data = charts(db, user)
    peak = chart_data["most_active_hours"][0]["label"] if chart_data["most_active_hours"] else "No activity"
    top_zone = chart_data["top_zones"][0]["label"] if chart_data["top_zones"] else "No zone activity"
    narrative = (
        f"Today, MotionGuard recorded {data['motion_events_today']} motion event(s), "
        f"{data['people_detected']} people detection(s), {data['vehicles_detected']} vehicle detection(s), "
        f"and {data['zone_events_today']} zone event(s). Peak activity is {peak}, and the most active zone is {top_zone}."
    )
    return {"summary": data, "peak_activity": peak, "most_active_zone": top_zone, "narrative": narrative}
