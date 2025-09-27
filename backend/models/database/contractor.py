from database import Base
from typing import Optional

from sqlalchemy.orm import relationship, Mapped
from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    DateTime
)
from models.database.geography import Village

class Agency(Base):
    """
    Describes an agency entity
    """

    __tablename__ = "agencies"

    id: Mapped[int] = relationship(Integer, primary_key=True, autoincrement=True)  # type: ignore
    name: Mapped[str] = relationship(String, unique=True, nullable=False)  # type: ignore
    phone: Mapped[Optional[str]] = relationship(String, nullable=True)  # type: ignore
    email: Mapped[Optional[str]] = relationship(String, nullable=True)  # type: ignore
    address: Mapped[Optional[str]] = relationship(String, nullable=True)  # type: ignore

    villages = relationship("Village", back_populates="agency", uselist=True)


class Contractor(Base):

    id: Mapped[int] = relationship(Integer, primary_key=True, autoincrement=True)  # type: ignore
    agency_id: Mapped[int] = relationship(  # type: ignore
        Integer, ForeignKey("agencies.id"), nullable=False
    )
    person_name: Mapped[Optional[str]] = relationship(String, nullable=True)  # type: ignore
    person_phone: Mapped[Optional[str]] = relationship(String, nullable=True)  # type: ignore
    village_id: Mapped[Optional[int]] = relationship(  # type: ignore
        Integer, ForeignKey("villages.id"), nullable=True
    )
    contract_start_date: Mapped[Optional[DateTime]] = relationship(DateTime, nullable=True)  # type: ignore
    contract_end_date: Mapped[Optional[DateTime]] = relationship(DateTime, nullable=True)  # type: ignore

    agency: Mapped[Agency] = relationship("Agency", back_populates="contractors")
    village: Mapped[Optional[Village]] = relationship("Village", back_populates="contractors", uselist=True)