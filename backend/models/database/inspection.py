from database import Base  # type: ignore
from typing import Optional, List
from datetime import date, datetime


from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, Integer, ForeignKey, Date, DateTime
from models.database.geography import District, Block, GramPanchayat


class Inspection(Base):  # type: ignore
    """
    Describes an inspection entity
    """

    __tablename__ = "inspections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    remarks: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore

    position_holder_id: Mapped[int] = mapped_column(  # type: ignore
        Integer, ForeignKey("authority_holder_persons.id"), nullable=False
    )

    district_id: Mapped[int] = mapped_column(  # type: ignore
        Integer, ForeignKey("districts.id"), nullable=False
    )
    block_id: Mapped[int] = mapped_column(  # type: ignore
        Integer, ForeignKey("blocks.id"), nullable=False
    )
    village_id: Mapped[int] = mapped_column(  # type: ignore
        Integer, ForeignKey("villages.id"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)  # type: ignore
    start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )  # type: ignore
    lat: Mapped[Optional[str]] = mapped_column(String, nullable=False)  # type: ignore
    long: Mapped[Optional[str]] = mapped_column(String, nullable=False)  # type: ignore

    district: Mapped[District] = relationship("District")
    block: Mapped[Block] = relationship("Block")
    village: Mapped[GramPanchayat] = relationship("GramPanchayat")

    media: Mapped[List["InspectionImage"]] = relationship(
        "InspectionImage", back_populates="inspection"
    )


class InspectionImage(Base):  # type: ignore
    """
    Describes an inspection image entity
    """

    __tablename__ = "inspection_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    inspection_id: Mapped[int] = mapped_column(  # type: ignore
        Integer, ForeignKey("inspections.id"), nullable=False
    )
    image_url: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore

    inspection: Mapped[Inspection] = relationship("Inspection", back_populates="media")
