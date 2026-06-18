from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import logging
from ..database import get_db
from ..models import Evidence, User
from ..security import get_current_user
from ..utils.file_utils import assert_storage_file


router = APIRouter(prefix="/files", tags=["files"])
logger = logging.getLogger(__name__)


@router.get("/evidence/{evidence_id}/download")
def evidence_download(evidence_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id, Evidence.user_id == current_user.id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found.")
    try:
        path = assert_storage_file(evidence.evidence_path)
        return FileResponse(path, filename=path.name)
    except HTTPException as e:
        logger.error(f"File access error for evidence {evidence_id}: path={evidence.evidence_path}, detail={e.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error downloading evidence {evidence_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve evidence file.")
