"""Feedback model definition."""

from typing import Optional


from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Feedback(Base):  # type: ignore
    """Feedback model representing user feedback."""

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    auth_user_id: Mapped[int] = mapped_column(ForeignKey("authority_users.id"), nullable=False)
    public_user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("public_users.id"), nullable=True)
    rating: Mapped[int] = mapped_column(nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(nullable=True)
