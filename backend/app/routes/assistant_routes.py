from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import get_current_user
from ..models import User
from ..services.analytics_service import charts, daily_summary, summary


router = APIRouter(prefix="/assistant", tags=["assistant"])


class AssistantQuestion(BaseModel):
    question: str


@router.post("/ask")
def ask_assistant(payload: AssistantQuestion, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = payload.question.lower()
    data = summary(db, current_user)
    chart_data = charts(db, current_user)
    if "today" in q or "summary" in q:
        return {"answer": daily_summary(db, current_user)["narrative"]}
    if "zone" in q:
        top = chart_data["top_zones"][0] if chart_data["top_zones"] else None
        return {"answer": f"The most active zone is {top['label']} with {top['value']} zone event(s)." if top else "No zone events have been recorded yet."}
    if "people" in q:
        return {"answer": f"{data['people_detected']} people detections are recorded for your account."}
    if "vehicle" in q:
        return {"answer": f"{data['vehicles_detected']} vehicle detections are recorded for your account."}
    if "motion" in q:
        return {"answer": f"{data['motion_events_today']} motion event(s) are recorded today."}
    return {"answer": f"Your workspace has {data['total_objects_detected']} detections, {data['motion_events_today']} motion event(s) today, and {data['evidence_captured']} evidence item(s)."}
