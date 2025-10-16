"""
Response Models for Annual Survey Management
"""

from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel
from models.response.auth import PositionHolderResponse
from models.database.survey_master import (
    FundHead,
    CollectionFrequency,
    CleaningFrequency,
)


class UserWithPositionResponse(BaseModel):
    user: Dict[str, Any]
    position: PositionHolderResponse


class WorkOrderDetailsResponse(BaseModel):
    """Response model for work order details."""

    id: int
    work_order_no: Optional[str]
    work_order_date: Optional[date]
    work_order_amount: Optional[float]

    class Config:
        from_attributes = True


class FundSanctionedResponse(BaseModel):
    """Response model for fund sanctioned details."""

    id: int
    amount: Optional[float]
    head: Optional[FundHead]

    class Config:
        from_attributes = True


class DoorToDoorCollectionResponse(BaseModel):
    """Response model for door to door collection details."""

    id: int
    num_households: Optional[int]
    num_shops: Optional[int]
    collection_frequency: Optional[CollectionFrequency]

    class Config:
        from_attributes = True


class RoadSweepingDetailsResponse(BaseModel):
    """Response model for road sweeping details."""

    id: int
    width: Optional[float]
    length: Optional[float]
    cleaning_frequency: Optional[CleaningFrequency]

    class Config:
        from_attributes = True


class DrainCleaningDetailsResponse(BaseModel):
    """Response model for drain cleaning details."""

    id: int
    length: Optional[float]
    cleaning_frequency: Optional[CleaningFrequency]

    class Config:
        from_attributes = True


class CSCDetailsResponse(BaseModel):
    """Response model for CSC details."""

    id: int
    numbers: Optional[int]
    cleaning_frequency: Optional[CleaningFrequency]

    class Config:
        from_attributes = True


class SWMAssetsResponse(BaseModel):
    """Response model for SWM assets."""

    id: int
    rrc: Optional[int]
    pwmu: Optional[int]
    compost_pit: Optional[int]
    collection_vehicle: Optional[int]

    class Config:
        from_attributes = True


class SBMGYearTargetsResponse(BaseModel):
    """Response model for SBMG year targets."""

    id: int
    ihhl: Optional[int]
    csc: Optional[int]
    rrc: Optional[int]
    pwmu: Optional[int]
    soak_pit: Optional[int]
    magic_pit: Optional[int]
    leach_pit: Optional[int]
    wsp: Optional[int]
    dewats: Optional[int]

    class Config:
        from_attributes = True


class VillageSBMGAssetsResponse(BaseModel):
    """Response model for village SBMG assets."""

    id: int
    ihhl: Optional[int]
    csc: Optional[int]

    class Config:
        from_attributes = True


class VillageGWMAssetsResponse(BaseModel):
    """Response model for village GWM assets."""

    id: int
    soak_pit: Optional[int]
    magic_pit: Optional[int]
    leach_pit: Optional[int]
    wsp: Optional[int]
    dewats: Optional[int]

    class Config:
        from_attributes = True


class VillageDataResponse(BaseModel):
    """Response model for village data."""

    id: int
    survey_id: int
    village_name: str
    population: Optional[int]
    num_households: Optional[int]
    sbmg_assets: Optional[VillageSBMGAssetsResponse] = None
    gwm_assets: Optional[VillageGWMAssetsResponse] = None

    class Config:
        from_attributes = True


class AnnualSurveyResponse(BaseModel):
    """Response model for annual survey details."""

    id: int
    gp_id: int
    survey_date: date
    surveyed_by_id: int

    # Surveyor details
    surveyor_name: str
    surveyor_role: str

    # Geography details
    gp_name: str
    block_name: str
    district_name: str

    # 1. VDO Details
    vdo_id: int

    # 2. Sarpanch Details
    sarpanch_name: str
    sarpanch_contact: str

    # 3. No. of Ward Panchs
    num_ward_panchs: int

    # 4. Bidder Name
    agency_id: int

    # Sub-sections (optional - only included if they exist)
    vdo: PositionHolderResponse
    work_order: Optional[WorkOrderDetailsResponse] = None
    fund_sanctioned: Optional[FundSanctionedResponse] = None
    door_to_door_collection: Optional[DoorToDoorCollectionResponse] = None
    road_sweeping: Optional[RoadSweepingDetailsResponse] = None
    drain_cleaning: Optional[DrainCleaningDetailsResponse] = None
    csc_details: Optional[CSCDetailsResponse] = None
    swm_assets: Optional[SWMAssetsResponse] = None
    sbmg_targets: Optional[SBMGYearTargetsResponse] = None

    # Village data (list)
    village_data: List[VillageDataResponse] = []

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnnualSurveyListItemResponse(BaseModel):
    """Response model for annual survey list item (summary view)."""

    id: int
    gp_id: int
    gp_name: str
    block_name: str
    district_name: str
    survey_date: date
    surveyor_name: str
    surveyor_role: str
    num_villages: int  # Number of villages in this survey

    class Config:
        from_attributes = True


class PaginatedAnnualSurveyResponse(BaseModel):
    """Paginated response for annual surveys list."""

    items: List[AnnualSurveyListItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AnnualSurveyStatsResponse(BaseModel):
    """Response model for annual survey statistics."""

    total_surveys: int
    total_gps_surveyed: int
    total_villages_covered: int
    total_population_covered: int
    total_households_covered: int

    # Asset summaries
    total_ihhl: int
    total_csc: int
    total_rrc: int
    total_pwmu: int
    total_soak_pit: int
    total_magic_pit: int
    total_leach_pit: int
    total_wsp: int
    total_dewats: int


class AnnualSurveyAnalyticsResponse(BaseModel):
    """Response model for annual survey analytics."""

    stats: AnnualSurveyStatsResponse
    by_district: Optional[List[Dict[str, Any]]] = None
    by_block: Optional[List[Dict[str, Any]]] = None
    by_gp: Optional[List[Dict[str, Any]]] = None
