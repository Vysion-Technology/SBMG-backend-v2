"""Feedback model definition."""

from typing import Optional


from sqlalchemy import CheckConstraint, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Feedback(Base):  # type: ignore
    """Feedback model representing user feedback."""

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    auth_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("authority_users.id"), nullable=True)
    public_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("public_users.id"), nullable=True)
    rating: Mapped[int] = mapped_column(nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Constraint that at least one of auth_user_id or public_user_id must be provided

    __table_args__ = (
        CheckConstraint(
            (auth_user_id.isnot(None)) | (public_user_id.isnot(None)),
            name="auth_or_public_user_constraint",
        ),
        # One user can give only one feedback
        UniqueConstraint(
            auth_user_id,
            name="unique_auth_user_feedback",
        ),
        UniqueConstraint(
            public_user_id,
            name="unique_public_user_feedback",
        )
    )
