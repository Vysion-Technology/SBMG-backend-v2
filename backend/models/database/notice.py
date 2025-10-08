from database import Base  # type: ignore
from typing import Optional
from datetime import date

from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, Integer, ForeignKey, Date, Text
from models.database.auth import PositionHolder


class Notice(Base):  # type: ignore
    """
    Describes a notice entity
    """

    __tablename__ = "notices"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    sender_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(PositionHolder.id), nullable=False
    )  # type: ignore
    receiver_id: Mapped[Optional[int]] = mapped_column(  # type: ignore
        Integer, ForeignKey(PositionHolder.id), nullable=True
    )
    title: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore
    date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)  # type: ignore
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # type: ignore

    media: Mapped[list["NoticeMedia"]] = relationship(
        "NoticeMedia", back_populates="notice", cascade="all, delete-orphan"
    )


class NoticeMedia(Base):  # type: ignore
    """
    Describes a notice media entity
    """

    __tablename__ = "notice_media"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    notice_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(Notice.id), nullable=False
    )  # type: ignore
    media_url: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore

    notice: Mapped[Notice] = relationship("Notice", back_populates="media")
