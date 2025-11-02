"""GPS Tracking database model."""

from datetime import datetime
from typing import List

from sqlalchemy import String, Integer, DateTime, Index, Float, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from models.database.geography import GramPanchayat  # type: ignore


class Vehicle(Base):
    """
    Describes a Vehicle entity
    """

    __tablename__ = "vehicles"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    gp_id: Mapped[int] = mapped_column(Integer, ForeignKey("gram_panchayats.id"), nullable=False, index=True)
    vehicle_no: Mapped[str] = mapped_column(String, nullable=False, index=True)
    imei: Mapped[str] = mapped_column(String, nullable=False)

    gp: Mapped["GramPanchayat"] = relationship(
        "GramPanchayat",
        back_populates="vehicles",
        foreign_keys=[gp_id],
    )

    gps_records: Mapped[List["GPSRecord"]] = relationship(
        "GPSRecord",
        back_populates="vehicle",
        foreign_keys="[GPSRecord.vehicle_id]",
    )

    __table_args__ = (Index("idx_gp_vehicle", "gp_id", "vehicle_no", unique=True),)


class GPSRecord(Base):
    """
    Describes a GPS record entity
    """

    __tablename__ = "gps_records"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    speed: Mapped[float] = mapped_column(Float, nullable=False)
    ignition: Mapped[bool] = mapped_column(Boolean, nullable=False)
    total_gps_odometer: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    vehicle: Mapped["Vehicle"] = relationship(
        "Vehicle",
        back_populates="gps_records",
        foreign_keys=[vehicle_id],
    )

    __table_args__ = (
        Index("idx_gps_record_vehicle_timestamp", "vehicle_id", "timestamp"),
        Index("idx_gps_record_vehicle", "vehicle_id"),
        Index("idx_gps_record_timestamp", "timestamp"),
    )

class GPSTracking(Base):
    """
    Describes a GPS tracking entity
    """

    __tablename__ = "gps_tracking"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_no: Mapped[str] = mapped_column(String, nullable=False, index=True)
    imei: Mapped[str] = mapped_column(String, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    speed: Mapped[float] = mapped_column(Float, nullable=False)
    ignition: Mapped[bool] = mapped_column(Boolean, nullable=False)
    total_gps_odometer: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        Index("idx_vehicle_timestamp", "vehicle_no", "timestamp"),
        Index("idx_vehicle", "vehicle_no"),
        Index("idx_timestamp", "timestamp"),
    )
