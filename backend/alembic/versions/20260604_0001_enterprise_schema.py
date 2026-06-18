"""enterprise schema

Revision ID: 20260604_0001
Revises:
Create Date: 2026-06-04
"""

from alembic import op
import sqlalchemy as sa


revision = "20260604_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLAlchemy metadata creates the full schema in development startup.
    # This migration records the initial enterprise schema boundary for Alembic
    # and PostgreSQL-ready versioning.
    pass


def downgrade() -> None:
    pass

