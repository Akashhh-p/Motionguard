from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Report, User
from ..schemas import ReportGenerateRequest, BulkDeleteReportRequest
from ..security import get_current_user
from ..services.report_service import generate_report
from ..services.audit_service import audit
from ..utils.file_utils import assert_storage_file
from ..utils.time_utils import utc_iso


router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate")
def generate(payload: ReportGenerateRequest, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = generate_report(db, current_user, payload.report_date)
    audit(db, current_user, "report_generation", f"Generated report {report.id}.", request)
    return serialize_report(report)


@router.get("")
def reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return [serialize_report(report) for report in db.query(Report).filter(Report.user_id == current_user.id).order_by(Report.created_at.desc()).all()]


@router.get("/{report_id}/download")
def download(report_id: int, format: str = "pdf", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = db.query(Report).filter(Report.id == report_id, Report.user_id == current_user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    path = report.csv_path if format == "csv" else report.file_path
    file_path = assert_storage_file(path)
    return FileResponse(file_path, filename=file_path.name)


@router.delete("/{report_id}")
def delete_report(report_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = db.query(Report).filter(Report.id == report_id, Report.user_id == current_user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    for path in (report.file_path, report.csv_path):
        if not path:
            continue
        try:
            file_path = assert_storage_file(path)
            file_path.unlink(missing_ok=True)
        except HTTPException as exc:
            if exc.status_code not in {404}:
                raise
    db.delete(report)
    db.commit()
    audit(db, current_user, "report_deleted", f"Deleted report {report_id}.", request)
    return {"success": True, "message": "Report deleted successfully"}


@router.post("/bulk-delete")
def bulk_delete_reports(
    payload: BulkDeleteReportRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete multiple reports belonging to current user."""
    if not payload.report_ids:
        raise HTTPException(status_code=400, detail="No report IDs provided.")
    
    # Get all reports belonging to current user with IDs in the list
    reports = db.query(Report).filter(
        Report.id.in_(payload.report_ids),
        Report.user_id == current_user.id
    ).all()
    
    deleted_count = 0
    skipped_count = len(payload.report_ids) - len(reports)
    
    # Delete files and database records
    for report in reports:
        try:
            # Delete physical files if they exist
            for path in (report.file_path, report.csv_path):
                if not path:
                    continue
                try:
                    file_path = assert_storage_file(path)
                    file_path.unlink(missing_ok=True)
                except HTTPException:
                    pass  # File might not exist, continue with deletion
            
            # Delete from database
            db.delete(report)
            deleted_count += 1
        except Exception as exc:
            audit(db, current_user, "error", f"Error deleting report {report.id}: {exc}", request)
            skipped_count += 1
    
    db.commit()
    
    # Log the bulk deletion
    audit(
        db,
        current_user,
        "report_bulk_deleted",
        f"Deleted {deleted_count} reports. {skipped_count} skipped.",
        request,
    )
    
    return {
        "success": True,
        "deleted_count": deleted_count,
        "skipped_count": skipped_count,
        "message": f"{deleted_count} reports deleted." + (f" {skipped_count} skipped." if skipped_count > 0 else ""),
    }


def serialize_report(report: Report) -> dict:
    return {
        "id": report.id,
        "report_date": report.report_date,
        "file_path": report.file_path,
        "csv_path": report.csv_path,
        "summary": report.summary,
        "created_at": utc_iso(report.created_at),
    }
