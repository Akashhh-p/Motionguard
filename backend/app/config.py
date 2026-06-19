from functools import lru_cache
from pathlib import Path
import secrets
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent


class Settings(BaseSettings):
    app_name: str = "MotionGuard AI Enterprise"
    api_prefix: str = "/api"
    database_url: str = f"sqlite:///{BASE_DIR / 'motionguard.db'}"
    jwt_secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    google_client_id: str = ""
    firebase_service_account_path: str = ""
    firebase_service_account_json: str = ""
    firebase_project_id: str = ""
    frontend_url: str = "http://127.0.0.1:5173"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    yolo_model_path: str = str(PROJECT_ROOT / "yolov8n.pt")
    yolo_config_dir: str = str(PROJECT_ROOT / "Ultralytics")
    max_upload_mb: int = 500
    default_frame_width: int = 960
    default_frame_skip: int = 3
    event_cooldown_seconds: int = 20
    storage_dir: Path = BASE_DIR / "storage"
    logs_dir: Path = BASE_DIR / "logs"
    rate_limit_per_minute: int = 120

    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", env_file_encoding="utf-8", extra="ignore")

    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    for child in ("uploads", "evidence", "reports", "processed", "outbox"):
        (settings.storage_dir / child).mkdir(parents=True, exist_ok=True)
    return settings
