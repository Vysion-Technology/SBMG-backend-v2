"""Database models for events and their media."""

from datetime import datetime, timezone

from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy.sql import func

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


class EventBookmark(Base):  # type: ignore
    """Database model for event bookmarks."""

    __tablename__ = "event_bookmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("authority_users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    event = relationship("Event")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uix_event_user_bookmark"),
    )
