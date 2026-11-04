"""In-app notification database models."""

from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import (
    String,
    Integer,
    Boolean,
    ForeignKey,
    DateTime,
    Text,
    UniqueConstraint,
)

from database import Base  # type: ignore


class InAppNotification(Base):  # type: ignore
    """
    Stores in-app notifications for authority users and public users.
    Supports both direct (user-specific) and broadcast (to all / target audience) notifications.
    """

    __tablename__ = "in_app_notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Specific recipient (if direct notification)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("authority_users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    public_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("public_users.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Broadcast notification flag and target
    is_broadcast: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    target_audience: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, default="ALL"
    )  # "ALL", "STAFF", "PUBLIC"

    # Notification content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # "NOTICE", "SLA", "EVENT", "SCHEME"
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")  # "LOW", "MEDIUM", "HIGH", "CRITICAL"

    # Deep linking & entity relation
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # "notice", "complaint", "event", "scheme"
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    action_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Read status for direct notifications
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    public_user = relationship("PublicUser", foreign_keys=[public_user_id])
    reads = relationship("InAppNotificationRead", back_populates="notification", cascade="all, delete-orphan")


class InAppNotificationRead(Base):  # type: ignore
    """
    Tracks read receipts for broadcast notifications per user.
    """

    __tablename__ = "in_app_notification_reads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    notification_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("in_app_notifications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("authority_users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    public_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("public_users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )

    notification = relationship("InAppNotification", back_populates="reads")
    user = relationship("User", foreign_keys=[user_id])
    public_user = relationship("PublicUser", foreign_keys=[public_user_id])

    __table_args__ = (
        UniqueConstraint("notification_id", "user_id", name="uq_notif_read_user"),
        UniqueConstraint("notification_id", "public_user_id", name="uq_notif_read_public_user"),
    )
