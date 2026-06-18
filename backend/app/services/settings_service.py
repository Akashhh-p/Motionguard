from sqlalchemy.orm import Session
from ..models import User, UserSettings


def get_or_create_settings(db: Session, user: User) -> UserSettings:
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if settings:
        return settings
    settings = UserSettings(user_id=user.id)
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def settings_classes(settings: UserSettings) -> set[str]:
    return {item.strip() for item in settings.allowed_object_classes.split(",") if item.strip()}

