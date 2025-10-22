from enum import Enum as PyEnum
from database import Base  # type: ignore
from typing import Optional, List
from datetime import date as dt_date, datetime


from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Index, String, Integer, ForeignKey, Date, DateTime, Boolean, Enum
from models.database.geography import District, Block, GramPanchayat


class Inspection(Base):  # type: ignore
    """
    Describes an inspection entity
    """

    __tablename__ = "inspections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    remarks: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    position_holder_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("authority_holder_persons.id"), nullable=False
    )

    gp_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("gram_panchayats.id"),
        nullable=False,
        index=True,
    )
    date: Mapped[dt_date] = mapped_column(
        Date,
        nullable=False,
        default=dt_date.today,
        index=True,
    )
    start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )  # type: ignore
    lat: Mapped[Optional[str]] = mapped_column(String, nullable=False)
    long: Mapped[Optional[str]] = mapped_column(String, nullable=False)
    register_maintenance: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )

    gp: Mapped[GramPanchayat] = relationship(
        "GramPanchayat", foreign_keys=[gp_id]
    )

    # Create the index on date and village_id separately for faster queries
    # Create another index on village_id if needed

    __table_args__ = (
        Index("ix_inspections_date", "date"),
        Index("ix_inspections_gp_id", "gp_id"),
        Index("ix_inspections_date_gp_id", "date", "gp_id"),
    )

    @property
    def district(self) -> Optional[District]:
        """Get district from village relationship."""
        return self.gp.district if self.gp else None

    @property
    def block(self) -> Optional[Block]:
        """Get block from village relationship."""
        return self.gp.block if self.gp else None

    media: Mapped[List["InspectionImage"]] = relationship(
        "InspectionImage", back_populates="inspection"
    )

    # 1:1 relationships with inspection items
    household_waste_item: Mapped[
        Optional["HouseHoldWasteCollectionAndDisposalInspectionItem"]
    ] = relationship(
        "HouseHoldWasteCollectionAndDisposalInspectionItem",
        back_populates="inspection",
        uselist=False,
        cascade="all, delete-orphan",
    )

    road_and_drain_item: Mapped[Optional["RoadAndDrainCleaningInspectionItem"]] = (
        relationship(
            "RoadAndDrainCleaningInspectionItem",
            back_populates="inspection",
            uselist=False,
            cascade="all, delete-orphan",
        )
    )

    community_sanitation_item: Mapped[Optional["CommunitySanitationInspectionItem"]] = (
        relationship(
            "CommunitySanitationInspectionItem",
            back_populates="inspection",
            uselist=False,
            cascade="all, delete-orphan",
        )
    )

    other_item: Mapped[Optional["OtherInspectionItem"]] = relationship(
        "OtherInspectionItem",
        back_populates="inspection",
        uselist=False,
        cascade="all, delete-orphan",
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

    __tablename__ = "inspection_household_waste_collection_and_disposal_inspection_i"

    id: Mapped[int] = mapped_column(
        Integer, ForeignKey("inspections.id"), primary_key=True
    )

    waste_collection_frequency: Mapped[Optional[WasteCollectionFrequency]] = (
        mapped_column(
            Enum(WasteCollectionFrequency, name="waste_coll_freq"), nullable=True
        )
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

    # 1:1 relationship back to inspection
    inspection: Mapped["Inspection"] = relationship(
        "Inspection", back_populates="household_waste_item"
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
        Enum(RoadCleaningFrequency, name="road_clean_freq"), nullable=True
    )
    drain_cleaning_frequency: Mapped[Optional[DrainCleaningFrequency]] = mapped_column(
        Enum(DrainCleaningFrequency, name="drain_clean_freq"), nullable=True
    )
    disposal_of_sludge_from_drains: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True
    )
    drain_waste_colllected_on_roadside: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True
    )

    # 1:1 relationship back to inspection
    inspection: Mapped["Inspection"] = relationship(
        "Inspection", back_populates="road_and_drain_item"
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
        Enum(CSCCleaningFrequency, name="csc_clean_freq"), nullable=True
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

    # 1:1 relationship back to inspection
    inspection: Mapped["Inspection"] = relationship(
        "Inspection", back_populates="community_sanitation_item"
    )


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

    # 1:1 relationship back to inspection
    inspection: Mapped["Inspection"] = relationship(
        "Inspection", back_populates="other_item"
    )
