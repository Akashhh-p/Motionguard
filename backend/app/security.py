from functools import lru_cache
import json
from pathlib import Path
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials, get_app, initialize_app
from sqlalchemy.orm import Session
from .config import get_settings
from .database import get_db
from .models import User
from .services.settings_service import get_or_create_settings
from .utils.time_utils import utc_now


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/session")


@lru_cache(maxsize=1)
def get_firebase_app():
    settings = get_settings()
    try:
        return get_app()
    except ValueError:
        pass

    if settings.firebase_service_account_json:
        try:
            service_account_info = json.loads(settings.firebase_service_account_json)
            credential = credentials.Certificate(service_account_info)
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Firebase Admin service account JSON is invalid.") from exc
    else:
        if not settings.firebase_service_account_path:
            raise HTTPException(status_code=500, detail="Firebase Admin service account is not configured.")

        service_account = Path(settings.firebase_service_account_path)
        if not service_account.exists():
            raise HTTPException(status_code=500, detail="Firebase Admin service account file was not found.")

        credential = credentials.Certificate(str(service_account))
    options = {"projectId": settings.firebase_project_id} if settings.firebase_project_id else None
    return initialize_app(credential, options=options)


def verify_firebase_token(id_token: str) -> dict:
    get_firebase_app()
    try:
        return firebase_auth.verify_id_token(id_token, check_revoked=True)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def provider_from_claims(claims: dict) -> str:
    firebase_claims = claims.get("firebase") or {}
    providers = firebase_claims.get("sign_in_provider") or "password"
    if providers == "google.com":
        return "google"
    if providers == "password":
        return "email"
    return providers


def sync_user_from_claims(db: Session, claims: dict) -> User:
    firebase_uid = claims.get("uid")
    email = claims.get("email")
    if not firebase_uid or not email:
        raise HTTPException(status_code=401, detail="Firebase token is missing required identity fields.")

    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if not user:
        user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        user = User(
            firebase_uid=firebase_uid,
            full_name=claims.get("name") or email.split("@")[0],
            email=email.lower(),
            auth_provider=provider_from_claims(claims),
            profile_picture=claims.get("picture"),
            email_verified=bool(claims.get("email_verified", False)),
            last_login=utc_now(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.firebase_uid = firebase_uid
        user.email = email.lower()
        user.full_name = claims.get("name") or user.full_name
        user.profile_picture = claims.get("picture") or user.profile_picture
        user.auth_provider = provider_from_claims(claims)
        user.email_verified = bool(claims.get("email_verified", user.email_verified))
        user.last_login = utc_now()
        db.commit()
        db.refresh(user)

    get_or_create_settings(db, user)
    return user


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    claims = verify_firebase_token(token)
    return sync_user_from_claims(db, claims)
