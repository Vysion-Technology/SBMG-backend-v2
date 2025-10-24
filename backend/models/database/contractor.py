from database import Base  # type: ignore
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, Integer, ForeignKey, DateTime

from models.database.geography import GramPanchayat

if TYPE_CHECKING:
    from models.database.attendance import DailyAttendance


class Agency(Base):  # type: ignore
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


class Contractor(Base):  # type: ignore
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
    gp_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("gram_panchayats.id"), index=True, nullable=False
    )
    contract_start_date: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # type: ignore
    contract_end_date: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # type: ignore

    # Relationships
    agency: Mapped[Agency] = relationship("Agency", back_populates="contractors")
    gp: Mapped[GramPanchayat] = relationship("GramPanchayat")
    attendances: Mapped[List["DailyAttendance"]] = relationship(
        "DailyAttendance", back_populates="contractor"
    )

    @property
    def name(self) -> str:
        return self.person_name if self.person_name else "Unnamed Contractor"
