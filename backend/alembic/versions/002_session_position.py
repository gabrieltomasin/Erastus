"""add position column to sessions

Revision ID: 002
Revises: 001
Create Date: 2026-04-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("position", sa.Integer(), nullable=True))
    # Backfill: set position = row number within each campaign
    op.execute(
        """
        UPDATE sessions SET position = sub.row_num
        FROM (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY campaign_id ORDER BY session_number) AS row_num
            FROM sessions
        ) AS sub
        WHERE sessions.id = sub.id
        """
    )
    op.alter_column("sessions", "position", nullable=False, server_default=sa.text("0"))


def downgrade() -> None:
    op.drop_column("sessions", "position")
