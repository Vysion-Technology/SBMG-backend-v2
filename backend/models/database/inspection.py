from enum import Enum as PyEnum
from database import Base  # type: ignore
from typing import Optional, List
from datetime import date as dt_date, datetime


from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, Integer, ForeignKey, Date, DateTime, Boolean, Enum
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

    village_id: Mapped[int] = mapped_column(  # type: ignore
        Integer, ForeignKey("villages.id"), nullable=False
    )
    date: Mapped[dt_date] = mapped_column(Date, nullable=False, default=dt_date.today)  # type: ignore
    start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )  # type: ignore
    lat: Mapped[Optional[str]] = mapped_column(String, nullable=False)  # type: ignore
    long: Mapped[Optional[str]] = mapped_column(String, nullable=False)  # type: ignore
    register_maintenance: Mapped[Optional[bool]] = mapped_column(  # type: ignore
        Boolean, nullable=True
    )

    village: Mapped[GramPanchayat] = relationship(
        "GramPanchayat", foreign_keys=[village_id]
    )

    @property
    def district(self) -> Optional[District]:
        """Get district from village relationship."""
        return self.village.district if self.village else None

    @property
    def block(self) -> Optional[Block]:
        """Get block from village relationship."""
        return self.village.block if self.village else None

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


class WasteCollectionFrequency(str, PyEnum):
    DAILY = "DAILY"
    ONCE_IN_THREE_DAYS = "ONCE_IN_THREE_DAYS"
    WEEKLY = "WEEKLY"
    NONE = "NONE"


class HouseHoldWasteCollectionAndDisposalInspectionItem(Base):  # type: ignore
    """
    Describes a household waste collection and disposal inspection item entity
    """

    __tablename__ = (
        "inspection_household_waste_collection_and_disposal_inspection_items"
    )

    id: Mapped[int] = mapped_column(
        Integer, ForeignKey("inspections.id"), primary_key=True
    )
    waste_collection_frequency: Mapped[Optional[WasteCollectionFrequency]] = (
        mapped_column(Enum(WasteCollectionFrequency), nullable=True)
    )
    dry_wet_vehicle_segregation: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True
    )
    covered_collection_in_vehicles: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True
    )
    waste_disposed_at_rrc: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True
    )
    rrc_waste_collection_and_disposal_arrangement: Mapped[Optional[bool]] = (
        mapped_column(Boolean, nullable=True)
    )
    waste_collection_vehicle_functional: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True
    )


class RoadCleaningFrequency(str, PyEnum):
    WEEKLY = "WEEKLY"
    FORTNIGHTLY = "FORTNIGHTLY"
    MONTHLY = "MONTHLY"
    NONE = "NONE"


class DrainCleaningFrequency(str, PyEnum):
    WEEKLY = "WEEKLY"
    FORTNIGHTLY = "FORTNIGHTLY"
    MONTHLY = "MONTHLY"
    NONE = "NONE"


class RoadAndDrainCleaningInspectionItem(Base):  # type: ignore
    """
    Describes a road cleaning inspection item entity
    """

    __tablename__ = "inspection_road_cleaning_inspection_items"

    id: Mapped[int] = mapped_column(
        Integer, ForeignKey("inspections.id"), primary_key=True
    )
    road_cleaning_frequency: Mapped[Optional[RoadCleaningFrequency]] = mapped_column(
        Enum(RoadCleaningFrequency), nullable=True
    )
    drain_cleaning_frequency: Mapped[Optional[DrainCleaningFrequency]] = mapped_column(
        Enum(DrainCleaningFrequency), nullable=True
    )
    disposal_of_sludge_from_drains: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True
    )
    drain_waste_colllected_on_roadside: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True
    )


class CSCCleaningFrequency(str, PyEnum):
    DAILY = "DAILY"
    ONCE_IN_THREE_DAYS = "ONCE_IN_THREE_DAYS"
    WEEKLY = "WEEKLY"
    NONE = "NONE"


class CommunitySanitationInspectionItem(Base):  # type: ignore
    """
    Describes a community sanitation inspection item entity
    """

    __tablename__ = "inspection_community_sanitation_inspection_items"

    id: Mapped[int] = mapped_column(
        Integer, ForeignKey("inspections.id"), primary_key=True
    )
    csc_cleaning_frequency: Mapped[Optional[CSCCleaningFrequency]] = mapped_column(
        Enum(CSCCleaningFrequency), nullable=True
    )
    electricity_and_water: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True
    )
    csc_used_by_community: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True
    )
    pink_toilets_cleaning: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True
    )
    pink_toilets_used: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)


class OtherInspectionItem(Base):  # type: ignore
    """
    Describes other inspection item entity
    """

    __tablename__ = "inspection_other_inspection_items"

    id: Mapped[int] = mapped_column(
        Integer, ForeignKey("inspections.id"), primary_key=True
    )
    firm_paid_regularly: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    cleaning_staff_paid_regularly: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True
    )
    firm_provided_safety_equipment: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True
    )
    regular_feedback_register_entry: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True
    )
    chart_prepared_for_cleaning_work: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True
    )
    village_visibly_clean: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True
    )
    rate_chart_displayed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
