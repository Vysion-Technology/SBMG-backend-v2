from datetime import datetime
from database import Base

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    name: Mapped[str] = Column(String, nullable=False)
    description: Mapped[str | None] = Column(String, nullable=True)
    # Keep start_time and end_time as datetime objects with timezone info
    start_time: Mapped[datetime] = Column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = Column(DateTime(timezone=True), nullable=False)
    active: Mapped[bool] = Column(Boolean, default=True)

    media = relationship("EventMedia", back_populates="event")


class EventMedia(Base):
    __tablename__ = "event_media"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    media_url = Column(String, nullable=False)

    event = relationship("Event", back_populates="media")
