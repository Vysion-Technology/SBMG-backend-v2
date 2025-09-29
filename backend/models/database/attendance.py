from typing import Optional
from database import Base
from datetime import datetime

from models.database.contractor import Contractor

from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    Date,
    DateTime
)

class Attendance(Base):
    """
    Describes an attendance entity
    """

    __tablename__ = "attendances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    contractor_id: Mapped[int] = mapped_column(  # type: ignore
        Integer, ForeignKey("contractors.id"), nullable=False
    )
    date: Mapped[Date] = mapped_column(Date, nullable=False)  # type: ignore
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=False, default=datetime.now)  # type: ignore
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # type: ignore
    remarks: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore

    contractor: Mapped[Contractor] = relationship("Contractor", back_populates="attendances")