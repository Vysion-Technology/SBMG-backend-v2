"""Database models for schemes and their associated media."""
from datetime import datetime, timezone

from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy.sql import func

from database import Base  # type: ignore

class Scheme(Base):  # type: ignore
    """Database model for a scheme."""

    __tablename__ = "schemes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    eligibility: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    benefits: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    # Keep start_time and end_time as datetime objects with timezone info
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    media = relationship("SchemeMedia", back_populates="scheme")


class SchemeMedia(Base):  # type: ignore
    """Database model for scheme media."""

    __tablename__ = "scheme_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scheme_id: Mapped[int] = mapped_column(Integer, ForeignKey("schemes.id"), nullable=False)
    media_url: Mapped[str] = mapped_column(String, nullable=False)

    scheme = relationship("Scheme", back_populates="media")


class SchemeBookmark(Base):  # type: ignore
    """Database model for scheme bookmarks."""

    __tablename__ = "scheme_bookmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scheme_id: Mapped[int] = mapped_column(Integer, ForeignKey("schemes.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("authority_users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    scheme = relationship("Scheme")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("scheme_id", "user_id", name="uix_scheme_user_bookmark"),
    )
