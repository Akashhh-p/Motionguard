from datetime import datetime
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base
from .utils.time_utils import utc_now


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    firebase_uid: Mapped[str | None] = mapped_column(String(160), unique=True, nullable=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    auth_provider: Mapped[str] = mapped_column(String(32), default="email")
    google_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    profile_picture: Mapped[str | None] = mapped_column(String(500), nullable=True)
    role: Mapped[str] = mapped_column(String(40), default="Operator", index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    verification_token: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    verification_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    reset_token_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    settings: Mapped["UserSettings"] = relationship(back_populates="user", cascade="all, delete-orphan")


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(700))
    source_type: Mapped[str] = mapped_column(String(32), default="upload")
    processed_path: Mapped[str | None] = mapped_column(String(700), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(40), default="pending", index=True)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Zone(Base):
    __tablename__ = "zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    zone_type: Mapped[str] = mapped_column(String(80))
    coordinates: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(40), default="any")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Detection(Base):
    __tablename__ = "detections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    object_class: Mapped[str] = mapped_column(String(80), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    source_type: Mapped[str] = mapped_column(String(32))
    video_id: Mapped[int | None] = mapped_column(ForeignKey("videos.id"), nullable=True, index=True)
    bbox: Mapped[str | None] = mapped_column(String(120), nullable=True)


class MotionEvent(Base):
    __tablename__ = "motion_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(80), default="motion", index=True)
    source_type: Mapped[str] = mapped_column(String(40), default="webcam", index=True)
    motion_count: Mapped[int] = mapped_column(Integer, default=0)
    estimated_moving_subjects: Mapped[int] = mapped_column(Integer, default=0)
    motion_area_total: Mapped[float] = mapped_column(Float, default=0)
    motion_area: Mapped[float] = mapped_column(Float, default=0)
    screenshot_path: Mapped[str | None] = mapped_column(String(700), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    status: Mapped[str] = mapped_column(String(40), default="open", index=True)


class ZoneEvent(Base):
    __tablename__ = "zone_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    motion_count: Mapped[int] = mapped_column(Integer, default=0)
    object_count: Mapped[int] = mapped_column(Integer, default=0)
    screenshot_path: Mapped[str | None] = mapped_column(String(700), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class EvidenceDetection(Base):
    __tablename__ = "evidence_detections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    evidence_id: Mapped[int] = mapped_column(ForeignKey("evidence.id"), index=True)
    object_class: Mapped[str] = mapped_column(String(80), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    report_date: Mapped[datetime] = mapped_column(Date, index=True)
    file_path: Mapped[str] = mapped_column(String(700))
    csv_path: Mapped[str | None] = mapped_column(String(700), nullable=True)
    summary: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    evidence_path: Mapped[str] = mapped_column(String(700))
    object_class: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    evidence_type: Mapped[str] = mapped_column(String(40), default="screenshot")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    details: Mapped[str] = mapped_column(Text, default="")
    ip_address: Mapped[str | None] = mapped_column(String(80), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class UserSettings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.35)
    alert_sound: Mapped[bool] = mapped_column(Boolean, default=True)
    evidence_capture: Mapped[bool] = mapped_column(Boolean, default=True)
    screenshot_save_folder: Mapped[str] = mapped_column(String(255), default="evidence")
    video_clip_save: Mapped[bool] = mapped_column(Boolean, default=False)
    frame_skip: Mapped[int] = mapped_column(Integer, default=3)
    theme: Mapped[str] = mapped_column(String(40), default="light")
    detection_sensitivity: Mapped[float] = mapped_column(Float, default=0.65)
    allowed_object_classes: Mapped[str] = mapped_column(Text, default="person,car,truck,bus,motorcycle,bicycle,backpack,handbag,suitcase")
    dashboard_layout: Mapped[str] = mapped_column(Text, default='{"kpis":true,"timeline":true,"zones":true}')
    default_landing_page: Mapped[str] = mapped_column(String(80), default="/dashboard")

    user: Mapped[User] = relationship(back_populates="settings")
