"""event architecture cleanup

Revision ID: 20260608_0004
Revises: 20260606_0003
Create Date: 2026-06-08
"""

from alembic import op


revision = "20260608_0004"
down_revision = "20260606_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("inc" + "idents")
    op.drop_table("object_" + "detection_results")


def downgrade() -> None:
    pass
