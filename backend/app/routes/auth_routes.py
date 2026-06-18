from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import UserOut
from ..security import get_current_user
from ..services.audit_service import audit


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/session", response_model=UserOut)
def sync_session(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    audit(db, current_user, "login", f"Firebase {current_user.auth_provider} session synced.", request)
    return current_user


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    audit(db, current_user, "logout", "User logged out.")
    return {"message": "Logged out. Remove the token on the client."}
