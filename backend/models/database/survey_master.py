"""
Annual Survey Master Models
Describes the annual survey entity and related models
"""

from enum import Enum as PyEnum
from models.response.admin import PositionHolder
from models.database.contractor import Agency
from database import Base  # type: ignore
from typing import Optional, List
from datetime import date as dt_date, datetime

from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Index, String, Integer, ForeignKey, Date, DateTime, Enum, Numeric
from models.database.geography import District, Block, GramPanchayat


class FundHead(str, PyEnum):
    """Fund head types for sanctioned funds"""

    FFC = "FFC"
    SFC = "SFC"
    CSR = "CSR"
    OWN_INCOME = "OWN_INCOME"
    OTHER = "OTHER"


class CollectionFrequency(str, PyEnum):
    """Collection frequency for door-to-door collection"""

    DAILY = "DAILY"
    ALTERNATE_DAYS = "ALTERNATE_DAYS"
    TWICE_A_WEEK = "TWICE_A_WEEK"
    WEEKLY = "WEEKLY"
    FORTNIGHTLY = "FORTNIGHTLY"
    NONE = "NONE"


class CleaningFrequency(str, PyEnum):
    """Cleaning frequency for various sanitation activities"""

    DAILY = "DAILY"
    ALTERNATE_DAYS = "ALTERNATE_DAYS"
    TWICE_A_WEEK = "TWICE_A_WEEK"
    WEEKLY = "WEEKLY"
    FORTNIGHTLY = "FORTNIGHTLY"
    MONTHLY = "MONTHLY"
    NONE = "NONE"


class AnnualSurvey(Base):  # type: ignore
    """
    Top-level annual survey entity for a Gram Panchayat
    """

    __tablename__ = "annual_surveys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Survey metadata
    gp_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("villages.id"),
        nullable=False,
        index=True,
    )
    survey_date: Mapped[dt_date] = mapped_column(
        Date,
        nullable=False,
        default=dt_date.today,
        index=True,
    )
    # 1. VDO Details
    vdo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("authority_holder_persons.id"), nullable=False
    )

    # 2. Sarpanch Details
    sarpanch_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sarpanch_contact: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # 3. No. of Ward Panchs
    num_ward_panchs: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # 4. Bidder Name (Sanitation activities)
    agency_id: Mapped[Agency] = mapped_column(
        Integer, ForeignKey("agencies.id"), nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )

    # Relationships
    gp: Mapped[GramPanchayat] = relationship("GramPanchayat", foreign_keys=[gp_id])
    vdo: Mapped[PositionHolder] = relationship("PositionHolder", foreign_keys=[vdo_id])
    agency: Mapped[Agency] = relationship("Agency", foreign_keys=[agency_id])

    # 1:1 relationships with sub-sections
    work_order: Mapped[Optional["WorkOrderDetails"]] = relationship(
        "WorkOrderDetails",
        back_populates="survey",
        uselist=False,
        cascade="all, delete-orphan",
    )

    fund_sanctioned: Mapped[Optional["FundSanctioned"]] = relationship(
        "FundSanctioned",
        back_populates="survey",
        uselist=False,
        cascade="all, delete-orphan",
    )

    door_to_door_collection: Mapped[Optional["DoorToDoorCollectionDetails"]] = (
        relationship(
            "DoorToDoorCollectionDetails",
            back_populates="survey",
            uselist=False,
            cascade="all, delete-orphan",
        )
    )

    road_sweeping: Mapped[Optional["RoadSweepingDetails"]] = relationship(
        "RoadSweepingDetails",
        back_populates="survey",
        uselist=False,
        cascade="all, delete-orphan",
    )

    drain_cleaning: Mapped[Optional["DrainCleaningDetails"]] = relationship(
        "DrainCleaningDetails",
        back_populates="survey",
        uselist=False,
        cascade="all, delete-orphan",
    )

    csc_details: Mapped[Optional["CSCDetails"]] = relationship(
        "CSCDetails",
        back_populates="survey",
        uselist=False,
        cascade="all, delete-orphan",
    )

    swm_assets: Mapped[Optional["SWMAssets"]] = relationship(
        "SWMAssets",
        back_populates="survey",
        uselist=False,
        cascade="all, delete-orphan",
    )

    sbmg_targets: Mapped[Optional["SBMGYearTargets"]] = relationship(
        "SBMGYearTargets",
        back_populates="survey",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # 1:Many relationship with village data
    village_data: Mapped[List["VillageData"]] = relationship(
        "VillageData",
        back_populates="survey",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("ix_annual_surveys_gp_id", "gp_id"),
        Index("ix_annual_surveys_survey_date", "survey_date"),
        Index("ix_annual_surveys_gp_id_survey_date", "gp_id", "survey_date"),
    )

    @property
    def district(self) -> Optional[District]:
        """Get district from GP relationship."""
        return self.gp.district if self.gp else None

    @property
    def block(self) -> Optional[Block]:
        """Get block from GP relationship."""
        return self.gp.block if self.gp else None


class WorkOrderDetails(Base):  # type: ignore
    """
    Work order details for the annual survey
    """

    __tablename__ = "survey_work_order_details"

    id: Mapped[int] = mapped_column(
        Integer, ForeignKey("annual_surveys.id"), primary_key=True
    )

    work_order_no: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    work_order_date: Mapped[Optional[dt_date]] = mapped_column(Date, nullable=True)
    work_order_amount: Mapped[Optional[float]] = mapped_column(
        Numeric(15, 2), nullable=True
    )

    # 1:1 relationship back to survey
    survey: Mapped["AnnualSurvey"] = relationship(
        "AnnualSurvey", back_populates="work_order"
    )


class FundSanctioned(Base):  # type: ignore
    """
    Fund sanctioned details for the annual survey
    """

    __tablename__ = "survey_fund_sanctioned"

    id: Mapped[int] = mapped_column(
        Integer, ForeignKey("annual_surveys.id"), primary_key=True
    )

    amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    head: Mapped[FundHead] = mapped_column(
        Enum(FundHead, name="fund_head"), nullable=True
    )

    # 1:1 relationship back to survey
    survey: Mapped["AnnualSurvey"] = relationship(
        "AnnualSurvey", back_populates="fund_sanctioned"
    )


class DoorToDoorCollectionDetails(Base):  # type: ignore
    """
    Door to door collection details
    """

    __tablename__ = "survey_door_to_door_collection"

    id: Mapped[int] = mapped_column(
        Integer, ForeignKey("annual_surveys.id"), primary_key=True
    )

    num_households: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    num_shops: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    collection_frequency: Mapped[Optional[CollectionFrequency]] = mapped_column(
        Enum(CollectionFrequency, name="collection_frequency"), nullable=True
    )

    # 1:1 relationship back to survey
    survey: Mapped["AnnualSurvey"] = relationship(
        "AnnualSurvey", back_populates="door_to_door_collection"
    )


class RoadSweepingDetails(Base):  # type: ignore
    """
    Road sweeping details
    """

    __tablename__ = "survey_road_sweeping"

    id: Mapped[int] = mapped_column(
        Integer, ForeignKey("annual_surveys.id"), primary_key=True
    )

    width: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), nullable=True
    )  # in meters
    length: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), nullable=True
    )  # in meters/km
    cleaning_frequency: Mapped[Optional[CleaningFrequency]] = mapped_column(
        Enum(CleaningFrequency, name="road_cleaning_frequency"), nullable=True
    )

    # 1:1 relationship back to survey
    survey: Mapped["AnnualSurvey"] = relationship(
        "AnnualSurvey", back_populates="road_sweeping"
    )


class DrainCleaningDetails(Base):  # type: ignore
    """
    Drain cleaning details
    """

    __tablename__ = "survey_drain_cleaning"

    id: Mapped[int] = mapped_column(
        Integer, ForeignKey("annual_surveys.id"), primary_key=True
    )

    length: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), nullable=True
    )  # in meters/km
    cleaning_frequency: Mapped[Optional[CleaningFrequency]] = mapped_column(
        Enum(CleaningFrequency, name="drain_cleaning_frequency"), nullable=True
    )

    # 1:1 relationship back to survey
    survey: Mapped["AnnualSurvey"] = relationship(
        "AnnualSurvey", back_populates="drain_cleaning"
    )


class CSCDetails(Base):  # type: ignore
    """
    Community Sanitation Complex (CSC) details
    """

    __tablename__ = "survey_csc_details"

    id: Mapped[int] = mapped_column(
        Integer, ForeignKey("annual_surveys.id"), primary_key=True
    )

    numbers: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cleaning_frequency: Mapped[Optional[CleaningFrequency]] = mapped_column(
        Enum(CleaningFrequency, name="csc_cleaning_frequency"), nullable=True
    )

    # 1:1 relationship back to survey
    survey: Mapped["AnnualSurvey"] = relationship(
        "AnnualSurvey", back_populates="csc_details"
    )


class SWMAssets(Base):  # type: ignore
    """
    Solid Waste Management (SWM) Assets
    """

    __tablename__ = "survey_swm_assets"

    id: Mapped[int] = mapped_column(
        Integer, ForeignKey("annual_surveys.id"), primary_key=True
    )

    rrc: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Resource Recovery Center
    pwmu: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Plastic Waste Management Unit
    compost_pit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    collection_vehicle: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # 1:1 relationship back to survey
    survey: Mapped["AnnualSurvey"] = relationship(
        "AnnualSurvey", back_populates="swm_assets"
    )


class SBMGYearTargets(Base):  # type: ignore
    """
    SBMG (Swachh Bharat Mission Gramin) Year Targets
    """

    __tablename__ = "survey_sbmg_year_targets"

    id: Mapped[int] = mapped_column(
        Integer, ForeignKey("annual_surveys.id"), primary_key=True
    )

    ihhl: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Individual Household Latrine
    csc: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Community Sanitation Complex
    rrc: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Resource Recovery Center
    pwmu: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Plastic Waste Management Unit
    soak_pit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    magic_pit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    leach_pit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    wsp: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Waste Stabilization Pond
    dewats: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Decentralized Wastewater Treatment System

    # 1:1 relationship back to survey
    survey: Mapped["AnnualSurvey"] = relationship(
        "AnnualSurvey", back_populates="sbmg_targets"
    )


class VillageData(Base):  # type: ignore
    """
    Village-level data within a Gram Panchayat survey
    One GP can have multiple villages
    """

    __tablename__ = "survey_village_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    survey_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("annual_surveys.id"),
        nullable=False,
        index=True,
    )

    village_name: Mapped[str] = mapped_column(String(255), nullable=False)
    population: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    num_households: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Many:1 relationship back to survey
    survey: Mapped["AnnualSurvey"] = relationship(
        "AnnualSurvey", back_populates="village_data"
    )

    # 1:1 relationships with asset details
    sbmg_assets: Mapped[Optional["VillageSBMGAssets"]] = relationship(
        "VillageSBMGAssets",
        back_populates="village_data",
        uselist=False,
        cascade="all, delete-orphan",
    )

    gwm_assets: Mapped[Optional["VillageGWMAssets"]] = relationship(
        "VillageGWMAssets",
        back_populates="village_data",
        uselist=False,
        cascade="all, delete-orphan",
    )


class VillageSBMGAssets(Base):  # type: ignore
    """
    SBMG Assets for a village
    """

    __tablename__ = "survey_village_sbmg_assets"

    id: Mapped[int] = mapped_column(
        Integer, ForeignKey("survey_village_data.id"), primary_key=True
    )

    ihhl: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Individual Household Latrine
    csc: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Community Sanitation Complex

    # 1:1 relationship back to village data
    village_data: Mapped["VillageData"] = relationship(
        "VillageData", back_populates="sbmg_assets"
    )


class VillageGWMAssets(Base):  # type: ignore
    """
    Grey Water Management (GWM) Assets for a village
    """

    __tablename__ = "survey_village_gwm_assets"

    id: Mapped[int] = mapped_column(
        Integer, ForeignKey("survey_village_data.id"), primary_key=True
    )

    soak_pit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    magic_pit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    leach_pit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    wsp: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Waste Stabilization Pond
    dewats: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Decentralized Wastewater Treatment System

    # 1:1 relationship back to village data
    village_data: Mapped["VillageData"] = relationship(
        "VillageData", back_populates="gwm_assets"
    )
