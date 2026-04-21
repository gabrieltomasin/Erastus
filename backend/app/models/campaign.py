import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    general_context: Mapped[str | None] = mapped_column(Text)
    system_prompt: Mapped[str | None] = mapped_column(Text)
    context_updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    sessions: Mapped[list["Session"]] = relationship(  # noqa: F821
        back_populates="campaign", cascade="all, delete-orphan", order_by="Session.session_number"
    )
