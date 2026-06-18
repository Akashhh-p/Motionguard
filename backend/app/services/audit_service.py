from fastapi import Request
from sqlalchemy.orm import Session
from ..models import AuditLog, User


def audit(db: Session, user: User | None, action: str, details: str = "", request: Request | None = None) -> None:
    ip = request.client.host if request and request.client else None
    db.add(AuditLog(user_id=user.id if user else None, action=action, details=details, ip_address=ip))
    db.commit()

