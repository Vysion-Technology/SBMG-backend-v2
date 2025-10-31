"""Defines the Notice and NoticeMedia models for the database."""
from datetime import date
from typing import Optional

from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, Integer, ForeignKey, Date, Text, UniqueConstraint

from database import Base
from models.database.auth import PositionHolder  # type: ignore

class NoticeType(Base):  # type: ignore
    """
    Describes a notice type entity
    """

    __tablename__ = "notice_types"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)  # type: ignore
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # type: ignore

    __table_args__ = (
        UniqueConstraint("name", name="uq_notice_type_name"),
    )

class Notice(Base):  # type: ignore
    """
    Describes a notice entity
    """

    __tablename__ = "notices"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    type_id: Mapped[int] = mapped_column(Integer, ForeignKey("notice_types.id"), nullable=False)  # type: ignore
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("authority_holder_persons.id"), nullable=False)  # type: ignore
    receiver_id: Mapped[Optional[int]] = mapped_column(  # type: ignore
        Integer, ForeignKey("authority_holder_persons.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore
    date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)  # type: ignore
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # type: ignore

    media: Mapped[list["NoticeMedia"]] = relationship(
        "NoticeMedia", back_populates="notice", cascade="all, delete-orphan"
    )

    sender: Mapped["PositionHolder"] = relationship(
        PositionHolder, foreign_keys=[sender_id]
    )
    receiver: Mapped[Optional["PositionHolder"]] = relationship(  # type: ignore
        PositionHolder, foreign_keys=[receiver_id]
    )


class NoticeMedia(Base):  # type: ignore
    """
    Describes a notice media entity
    """

    __tablename__ = "notice_media"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    notice_id: Mapped[int] = mapped_column(Integer, ForeignKey(Notice.id), nullable=False)  # type: ignore
    media_url: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore

    notice: Mapped[Notice] = relationship("Notice", back_populates="media")
