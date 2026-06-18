from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field, field_serializer
from .utils.time_utils import utc_iso


class UserOut(BaseModel):
    id: int
    firebase_uid: str | None = None
    full_name: str
    email: EmailStr
    auth_provider: str
    role: str
    email_verified: bool
    profile_picture: str | None = None
    created_at: datetime
    last_login: datetime | None = None

    model_config = {"from_attributes": True}

    @field_serializer("created_at", "last_login")
    def serialize_utc_datetime(self, value: datetime | None):
        return utc_iso(value)


class ZoneIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    zone_type: str
    coordinates: list[dict[str, float]]
    source_type: str = "any"


class ZoneOut(BaseModel):
    id: int
    name: str
    zone_type: str
    coordinates: list[dict[str, float]]
    source_type: str
    created_at: datetime


class SettingsIn(BaseModel):
    confidence_threshold: float = Field(ge=0.05, le=0.95)
    alert_sound: bool
    evidence_capture: bool
    screenshot_save_folder: str = "evidence"
    video_clip_save: bool = False
    frame_skip: int = Field(ge=1, le=30)
    theme: str = "light"
    detection_sensitivity: float = Field(ge=0.1, le=1.0)
    allowed_object_classes: list[str]
    dashboard_layout: dict[str, bool] = {"kpis": True, "timeline": True, "zones": True}
    default_landing_page: str = "/dashboard"


class SettingsOut(SettingsIn):
    id: int
    user_id: int


class ReportGenerateRequest(BaseModel):
    report_date: date | None = None


class ReportOut(BaseModel):
    id: int
    report_date: date
    file_path: str
    csv_path: str | None
    summary: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime):
        return utc_iso(value)


class BulkDeleteEvidenceRequest(BaseModel):
    evidence_ids: list[int] = Field(min_length=1, max_length=1000)


class BulkDeleteReportRequest(BaseModel):
    report_ids: list[int] = Field(min_length=1, max_length=1000)
