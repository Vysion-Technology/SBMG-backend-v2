"""Database models for events and their media."""

from datetime import datetime

from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, mapped_column, Mapped

from database import Base  # type: ignore


class Event(Base):  # type: ignore
    """Database model for an event."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    # Keep start_time and end_time as datetime objects with timezone info
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    media = relationship("EventMedia", back_populates="event")


class EventMedia(Base):  # type: ignore
    """Database model for event media."""

    __tablename__ = "event_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    media_url: Mapped[str] = mapped_column(String, nullable=False)

    event = relationship("Event", back_populates="media")
