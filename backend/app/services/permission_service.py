from fastapi import Depends, HTTPException
from ..models import User
from ..security import get_current_user


ROLE_LEVELS = {"Viewer": 1, "Operator": 2, "Manager": 3, "Admin": 4}


def require_role(minimum_role: str):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if ROLE_LEVELS.get(current_user.role, 0) < ROLE_LEVELS.get(minimum_role, 0):
            raise HTTPException(status_code=403, detail="Insufficient permissions.")
        return current_user

    return dependency

