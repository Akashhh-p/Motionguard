"""motion events and evidence detections

Revision ID: 20260605_0002
Revises: 20260604_0001
Create Date: 2026-06-05
"""

from alembic import op
import sqlalchemy as sa


revision = "20260605_0002"
down_revision = "20260604_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "motion_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False, server_default="motion"),
        sa.Column("source_type", sa.String(length=40), nullable=False, server_default="webcam"),
        sa.Column("motion_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_moving_subjects", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("motion_area_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("motion_area", sa.Float(), nullable=False, server_default="0"),
        sa.Column("screenshot_path", sa.String(length=700), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="open"),
    )
    op.create_index("ix_motion_events_user_id", "motion_events", ["user_id"])
    op.create_index("ix_motion_events_timestamp", "motion_events", ["timestamp"])
    op.create_index("ix_motion_events_event_type", "motion_events", ["event_type"])
    op.create_index("ix_motion_events_status", "motion_events", ["status"])
    op.create_index("ix_motion_events_source_type", "motion_events", ["source_type"])

    op.create_table(
        "evidence_detections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("evidence_id", sa.Integer(), sa.ForeignKey("evidence.id"), nullable=False),
        sa.Column("object_class", sa.String(length=80), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_evidence_detections_user_id", "evidence_detections", ["user_id"])
    op.create_index("ix_evidence_detections_evidence_id", "evidence_detections", ["evidence_id"])
    op.create_index("ix_evidence_detections_object_class", "evidence_detections", ["object_class"])
    op.create_index("ix_evidence_detections_detected_at", "evidence_detections", ["detected_at"])


def downgrade() -> None:
    op.drop_table("evidence_detections")
    op.drop_table("motion_events")
