"""zone events

Revision ID: 20260606_0003
Revises: 20260605_0002
Create Date: 2026-06-06
"""

from alembic import op
import sqlalchemy as sa


revision = "20260606_0003"
down_revision = "20260605_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "zone_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("zone_id", sa.Integer(), sa.ForeignKey("zones.id"), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("motion_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("object_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("screenshot_path", sa.String(length=700), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_zone_events_user_id", "zone_events", ["user_id"])
    op.create_index("ix_zone_events_zone_id", "zone_events", ["zone_id"])
    op.create_index("ix_zone_events_event_type", "zone_events", ["event_type"])
    op.create_index("ix_zone_events_timestamp", "zone_events", ["timestamp"])


def downgrade() -> None:
    op.drop_table("zone_events")
