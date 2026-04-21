import datetime
import enum

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SessionStatus(str, enum.Enum):
    PENDING = "pending"
    TRANSCRIBING = "transcribing"
    SUMMARIZING = "summarizing"
    READY = "ready"
    ERROR = "error"


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    session_number: Mapped[int] = mapped_column(Integer)
    audio_files: Mapped[list | None] = mapped_column(JSON, default=list)
    transcription: Mapped[str | None] = mapped_column(Text)
    raw_summary: Mapped[str | None] = mapped_column(Text)
    final_summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, values_callable=lambda e: [x.value for x in e]),
        default=SessionStatus.PENDING,
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    campaign: Mapped["Campaign"] = relationship(back_populates="sessions")  # noqa: F821
    processing_logs: Mapped[list["ProcessingLog"]] = relationship(  # noqa: F821
        back_populates="session", cascade="all, delete-orphan", order_by="ProcessingLog.timestamp"
    )
