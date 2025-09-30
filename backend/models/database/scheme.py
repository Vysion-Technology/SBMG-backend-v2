from datetime import datetime
from database import Base

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped


class Scheme(Base):
    __tablename__ = "schemes"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    name: Mapped[str] = Column(String, nullable=False)
    description: Mapped[str | None] = Column(String, nullable=True)
    eligibility: Mapped[str | None] = Column(String, nullable=True, default=None)
    benefits: Mapped[str | None] = Column(String, nullable=True, default=None)
    # Keep start_time and end_time as datetime objects with timezone info
    start_time: Mapped[datetime] = Column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = Column(DateTime(timezone=True), nullable=False)
    active: Mapped[bool] = Column(Boolean, default=True)

    media = relationship("SchemeMedia", back_populates="scheme")


class SchemeMedia(Base):
    __tablename__ = "scheme_media"

    id = Column(Integer, primary_key=True, index=True)
    scheme_id = Column(Integer, ForeignKey("schemes.id"), nullable=False)
    media_url = Column(String, nullable=False)

    scheme = relationship("Scheme", back_populates="media")
