"""GPS Tracking database model."""

from datetime import datetime

from sqlalchemy import String, Integer, DateTime, Index, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from database import Base  # type: ignore

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
