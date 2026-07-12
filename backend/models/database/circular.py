"""Database model for circulars."""
from datetime import datetime

from sqlalchemy import (
    Integer,
    String,
    DateTime,
    Boolean,
)
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.sql import func

from database import Base  # type: ignore


class Circular(Base):  # type: ignore
    """Database model for a circular."""

    __tablename__ = "circulars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    pdf_url: Mapped[str] = mapped_column(String, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    start_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    end_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
