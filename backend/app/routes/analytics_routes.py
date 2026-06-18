from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..security import get_current_user
from ..services.analytics_service import charts, daily_summary, summary


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def analytics_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return summary(db, current_user)


@router.get("/charts")
def analytics_charts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return charts(db, current_user)


@router.get("/daily-summary")
def analytics_daily_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return daily_summary(db, current_user)

