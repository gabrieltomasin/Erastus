import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProcessingLog(Base):
    __tablename__ = "processing_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))
    step: Mapped[str] = mapped_column(String(100))
    message: Mapped[str] = mapped_column(Text)
    level: Mapped[str] = mapped_column(String(20), default="info")
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped["Session"] = relationship(back_populates="processing_logs")  # noqa: F821
