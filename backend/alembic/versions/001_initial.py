"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("general_context", sa.Text(), nullable=True),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        sa.Column("context_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("session_number", sa.Integer(), nullable=False),
        sa.Column("audio_files", sa.JSON(), nullable=True),
        sa.Column("transcription", sa.Text(), nullable=True),
        sa.Column("raw_summary", sa.Text(), nullable=True),
        sa.Column("final_summary", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum("pending", "transcribing", "summarizing", "ready", "error", name="sessionstatus"), server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "processing_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step", sa.String(100), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("level", sa.String(20), server_default="info"),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("processing_logs")
    op.drop_table("sessions")
    op.drop_table("campaigns")
