"""
Request Models for Annual Survey Management
"""

from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field
from models.database.survey_master import (
    FundHead,
    CollectionFrequency,
    CleaningFrequency,
)


class WorkOrderDetailsRequest(BaseModel):
    """Request model for work order details."""

    work_order_no: Optional[str] = None
    work_order_date: Optional[date] = None
    work_order_amount: Optional[float] = None


class FundSanctionedRequest(BaseModel):
    """Request model for fund sanctioned details."""

    amount: Optional[float] = None
    head: Optional[FundHead] = None


class DoorToDoorCollectionRequest(BaseModel):
    """Request model for door to door collection details."""

    num_households: Optional[int] = None
    num_shops: Optional[int] = None
    collection_frequency: Optional[CollectionFrequency] = None


class RoadSweepingDetailsRequest(BaseModel):
    """Request model for road sweeping details."""

    width: Optional[float] = None
    length: Optional[float] = None
    cleaning_frequency: Optional[CleaningFrequency] = None


class DrainCleaningDetailsRequest(BaseModel):
    """Request model for drain cleaning details."""

    length: Optional[float] = None
    cleaning_frequency: Optional[CleaningFrequency] = None


class CSCDetailsRequest(BaseModel):
    """Request model for CSC details."""

    numbers: Optional[int] = None
    cleaning_frequency: Optional[CleaningFrequency] = None


class SWMAssetsRequest(BaseModel):
    """Request model for SWM assets."""

    rrc: Optional[int] = None
    pwmu: Optional[int] = None
    compost_pit: Optional[int] = None
    collection_vehicle: Optional[int] = None


class SBMGYearTargetsRequest(BaseModel):
    """Request model for SBMG year targets."""

    ihhl: Optional[int] = None
    csc: Optional[int] = None
    rrc: Optional[int] = None
    pwmu: Optional[int] = None
    soak_pit: Optional[int] = None
    magic_pit: Optional[int] = None
    leach_pit: Optional[int] = None
    wsp: Optional[int] = None
    dewats: Optional[int] = None


class VillageSBMGAssetsRequest(BaseModel):
    """Request model for village SBMG assets."""

    ihhl: Optional[int] = None
    csc: Optional[int] = None


class VillageGWMAssetsRequest(BaseModel):
    """Request model for village GWM assets."""

    soak_pit: Optional[int] = None
    magic_pit: Optional[int] = None
    leach_pit: Optional[int] = None
    wsp: Optional[int] = None
    dewats: Optional[int] = None


class VillageDataRequest(BaseModel):
    """Request model for village data."""

    village_id: str = Field(..., description="ID of the village")
    population: Optional[int] = None
    num_households: Optional[int] = None
    sbmg_assets: Optional[VillageSBMGAssetsRequest] = None
    gwm_assets: Optional[VillageGWMAssetsRequest] = None


class CreateAnnualSurveyRequest(BaseModel):
    """Request model for creating a new annual survey."""

    fy_id: int = Field(..., description="Financial Year ID")
    gp_id: int = Field(..., description="ID of the Gram Panchayat")
    survey_date: Optional[date] = Field(
        None, description="Date of survey (defaults to today)"
    )

    # 1. VDO Details
    vdo_id: int = Field(..., description="ID of the VDO")

    # 2. Sarpanch Details
    sarpanch_name: str = Field(..., description="Name of the Sarpanch")
    sarpanch_contact: str = Field(..., description="Contact number of the Sarpanch")

    # 3. No. of Ward Panchs
    num_ward_panchs: int = Field(..., description="Number of Ward Panchs")

    # 4. Bidder Name (Sanitation activities)
    agency_id: int = Field(..., description="ID of the Agency")

    # 5. Work Order Details
    work_order: Optional[WorkOrderDetailsRequest] = Field(
        None, description="Work order details"
    )

    # 6. Fund Sanctioned
    fund_sanctioned: Optional[FundSanctionedRequest] = None

    # 7. Door to Door Collection
    door_to_door_collection: Optional[DoorToDoorCollectionRequest] = None

    # 8. Road Sweeping
    road_sweeping: Optional[RoadSweepingDetailsRequest] = None

    # 9. Drain Cleaning
    drain_cleaning: Optional[DrainCleaningDetailsRequest] = None

    # 10. CSC
    csc_details: Optional[CSCDetailsRequest] = None

    # 11. SWM Assets
    swm_assets: Optional[SWMAssetsRequest] = None

    # 12. SBMG Year Targets
    sbmg_targets: Optional[SBMGYearTargetsRequest] = None

    # 13. Village Data (multiple villages)
    village_data: Optional[List[VillageDataRequest]] = Field(
        None, description="List of village data"
    )


class UpdateAnnualSurveyRequest(BaseModel):
    """Request model for updating an annual survey."""

    survey_date: Optional[date] = None

    # 1. VDO Details
    vdo_name: Optional[str] = None
    vdo_contact: Optional[str] = None

    # 2. Sarpanch Details
    sarpanch_name: Optional[str] = None
    sarpanch_contact: Optional[str] = None

    # 3. No. of Ward Panchs
    num_ward_panchs: Optional[int] = None

    # 4. Bidder Name
    bidder_name: Optional[str] = None

    # 5. Work Order Details
    work_order: Optional[WorkOrderDetailsRequest] = None

    # 6. Fund Sanctioned
    fund_sanctioned: Optional[FundSanctionedRequest] = None

    # 7. Door to Door Collection
    door_to_door_collection: Optional[DoorToDoorCollectionRequest] = None

    # 8. Road Sweeping
    road_sweeping: Optional[RoadSweepingDetailsRequest] = None

    # 9. Drain Cleaning
    drain_cleaning: Optional[DrainCleaningDetailsRequest] = None

    # 10. CSC
    csc_details: Optional[CSCDetailsRequest] = None

    # 11. SWM Assets
    swm_assets: Optional[SWMAssetsRequest] = None

    # 12. SBMG Year Targets
    sbmg_targets: Optional[SBMGYearTargetsRequest] = None

    # 13. Village Data (multiple villages)
    village_data: Optional[List[VillageDataRequest]] = None
