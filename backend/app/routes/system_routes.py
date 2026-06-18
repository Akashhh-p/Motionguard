from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..security import get_current_user


router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health")
def system_health(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.execute(text("SELECT 1"))
    return {
        "database": "connected",
        "auth": "active" if current_user else "unavailable",
        "motion_engine": "ready",
        "evidence_engine": "ready",
        "zone_engine": "ready",
    }
