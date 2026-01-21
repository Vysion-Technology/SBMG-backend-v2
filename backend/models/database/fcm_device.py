from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    DateTime,
    UniqueConstraint,
)

from database import Base  # type: ignore


class UserDeviceToken(Base):  # type: ignore
    """
    Stores FCM device tokens for staff users (Workers, VDOs, BDOs, CEOs, Admins)
    """

    __tablename__ = "user_device_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("authority_users.id", ondelete="CASCADE"), nullable=False
    )  # type: ignore
    device_id: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore
    fcm_token: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore
    device_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore
    platform: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore # ios, android, web
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc)
    )  # type: ignore
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=lambda: datetime.now(tz=timezone.utc), nullable=True
    )  # type: ignore

    # Relationships
    user = relationship("User", backref="device_tokens")

    # Unique constraint: one device_id per user
    __table_args__ = (UniqueConstraint("user_id", "device_id", name="uq_user_device"),)


class PublicUserDeviceToken(Base):  # type: ignore
    """
    Stores FCM device tokens for public users (citizens who create complaints)
    """

    __tablename__ = "public_user_device_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    public_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("public_users.id", ondelete="CASCADE"), nullable=False
    )  # type: ignore
    device_id: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore
    fcm_token: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore
    device_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore
    platform: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore # ios, android, web
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc)
    )  # type: ignore
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=lambda: datetime.now(tz=timezone.utc), nullable=True
    )  # type: ignore

    # Relationships
    public_user = relationship("PublicUser", backref="device_tokens")

    # Unique constraint: one device_id per public user
    __table_args__ = (
        UniqueConstraint("public_user_id", "device_id", name="uq_public_user_device"),
    )
