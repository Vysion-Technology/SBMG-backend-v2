from typing import Optional, TYPE_CHECKING
from models.database.contractor import Agency
from database import Base  # type: ignore
from datetime import datetime, date as dt_date

from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, Integer, ForeignKey, Date, DateTime

if TYPE_CHECKING:
    from models.database.contractor import Contractor


class DailyAttendance(Base):  # type: ignore
    """
    Describes an attendance entity
    """

    __tablename__ = "contractor_attendances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    contractor_id: Mapped[int] = mapped_column(  # type: ignore
        Integer, ForeignKey("contractors.id"), nullable=False
    )
    date: Mapped[dt_date] = mapped_column(Date, nullable=False, default=dt_date.today)  # type: ignore
    start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )  # type: ignore
    start_lat: Mapped[Optional[str]] = mapped_column(String, nullable=False)  # type: ignore
    start_long: Mapped[Optional[str]] = mapped_column(String, nullable=False)  # type: ignore
    end_lat: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore
    end_long: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore
    end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # type: ignore
    remarks: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore

    contractor: Mapped["Contractor"] = relationship(
        "Contractor", back_populates="attendances", uselist=False
    )
