import csv
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table
from sqlalchemy.orm import Session

from ..models import Detection, Evidence, EvidenceDetection, MotionEvent, Report, User, ZoneEvent
from ..utils.file_utils import storage_subdir
from ..utils.time_utils import ensure_utc, utc_day_bounds, utc_iso, utc_now


def generate_report(db: Session, user: User, report_date: date | None = None) -> Report:
    report_day = report_date or utc_now().date()
    start, end = utc_day_bounds(report_day)

    motion_events = db.query(MotionEvent).filter(MotionEvent.user_id == user.id, MotionEvent.timestamp.between(start, end)).all()
    evidence_items = db.query(Evidence).filter(Evidence.user_id == user.id, Evidence.created_at.between(start, end)).all()
    evidence_detections = db.query(EvidenceDetection).filter(EvidenceDetection.user_id == user.id, EvidenceDetection.detected_at.between(start, end)).all()
    object_detections = db.query(Detection).filter(Detection.user_id == user.id, Detection.timestamp.between(start, end)).all()
    zone_events = db.query(ZoneEvent).filter(ZoneEvent.user_id == user.id, ZoneEvent.timestamp.between(start, end)).all()

    people = [item for item in object_detections if item.object_class == "person"]
    vehicles = [item for item in object_detections if item.object_class in {"car", "truck", "bus", "motorcycle", "bicycle"}]
    summary = (
        f"MotionGuard recorded {len(motion_events)} motion event(s), {len(evidence_items)} evidence item(s), "
        f"{len(evidence_detections)} evidence analysis result(s), {len(zone_events)} zone monitoring result(s), "
        f"{len(people)} person detection(s), and {len(vehicles)} vehicle detection(s) on {report_day}."
    )

    report_dir = storage_subdir("reports")
    pdf_path = report_dir / f"user{user.id}_daily_report_{report_day.isoformat()}.pdf"
    csv_path = report_dir / f"user{user.id}_daily_report_{report_day.isoformat()}.csv"
    write_pdf(pdf_path, user.full_name, report_day, summary, motion_events, evidence_detections, zone_events, object_detections)
    write_csv(csv_path, motion_events, evidence_detections, zone_events, object_detections)

    report = Report(user_id=user.id, report_date=report_day, file_path=str(pdf_path), csv_path=str(csv_path), summary=summary)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def write_pdf(path: Path, user_name: str, report_day: date, summary: str, motion_events, evidence_detections, zone_events, object_detections) -> None:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=A4, title="MotionGuard Daily Surveillance Report")
    story = [
        Paragraph("MotionGuard AI Enterprise", styles["Title"]),
        Paragraph(f"Daily Surveillance Report - {report_day.isoformat()}", styles["Heading2"]),
        Paragraph(f"Prepared for {user_name}", styles["Normal"]),
        Spacer(1, 14),
        Paragraph(summary, styles["BodyText"]),
        Spacer(1, 14),
        Table(
            [
                ["Motion Events", "Evidence Analysis Results", "Zone Monitoring Results", "Object Detection Results"],
                [len(motion_events), len(evidence_detections), len(zone_events), len(object_detections)],
            ],
            style=[("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFF2EC")), ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7E1"))],
        ),
        Spacer(1, 18),
        Paragraph("Motion Events", styles["Heading3"]),
    ]
    motion_rows = [["ID", "Source", "Count", "Moving Subjects", "Time"]]
    motion_rows += [[item.id, item.source_type, item.motion_count, item.estimated_moving_subjects, ensure_utc(item.timestamp).strftime("%H:%M:%S UTC")] for item in motion_events[:30]]
    story.append(Table(motion_rows, repeatRows=1, style=[("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7E1")), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F7F8F4"))]))
    story += [Spacer(1, 18), Paragraph("Zone Monitoring Results", styles["Heading3"])]
    zone_rows = [["ID", "Type", "Motion Count", "Object Count", "Time"]]
    zone_rows += [[item.id, item.event_type, item.motion_count, item.object_count, ensure_utc(item.timestamp).strftime("%H:%M:%S UTC")] for item in zone_events[:30]]
    story.append(Table(zone_rows, repeatRows=1, style=[("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7E1")), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F7F8F4"))]))
    doc.build(story)


def write_csv(path: Path, motion_events, evidence_detections, zone_events, object_detections) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["kind", "id", "type_or_class", "count_or_confidence", "source", "timestamp"])
        for item in motion_events:
            writer.writerow(["motion_event", item.id, item.event_type, item.motion_count, item.source_type, utc_iso(item.timestamp)])
        for item in evidence_detections:
            writer.writerow(["evidence_detection", item.id, item.object_class, item.confidence, "evidence", utc_iso(item.detected_at)])
        for item in zone_events:
            writer.writerow(["zone_event", item.id, item.event_type, item.motion_count + item.object_count, item.zone_id, utc_iso(item.timestamp)])
        for item in object_detections:
            writer.writerow(["object_detection", item.id, item.object_class, item.confidence, item.source_type, utc_iso(item.timestamp)])
