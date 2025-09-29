from database import Base
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    DateTime
)

if TYPE_CHECKING:
    from models.database.attendance import Attendance


class Agency(Base):
    """
    Describes an agency entity
    """

    __tablename__ = "agencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)  # type: ignore
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore

    contractors = relationship("Contractor", back_populates="agency")


class Contractor(Base):
    """
    Describes a contractor/worker entity
    """

    __tablename__ = "contractors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    agency_id: Mapped[int] = mapped_column(  # type: ignore
        Integer, ForeignKey("agencies.id"), nullable=False
    )
    person_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore
    person_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore
    village_id: Mapped[Optional[int]] = mapped_column(  # type: ignore
        Integer, ForeignKey("villages.id"), nullable=True
    )
    contract_start_date: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)  # type: ignore
    contract_end_date: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)  # type: ignore

    # Relationships
    agency: Mapped[Agency] = relationship("Agency", back_populates="contractors")
    village = relationship("Village", back_populates="contractors")
    attendances: Mapped[List["Attendance"]] = relationship("Attendance", back_populates="contractor")