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
    WorkFrequency,
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


# --- New Asset Category Response Models ---

class ODFSustainabilityResponse(BaseModel):
    """Response model for ODF sustainability details."""
    id: int
    ihhl: int
    retrofitting: int
    csc: int
    csc_shala_darpan: int

    class Config:
        from_attributes = True


class SWMAssetsCategoryResponse(BaseModel):
    """Response model for SWM assets details."""
    id: int
    bins_hh_level: int
    bins_public_places: int
    community_compost_pits: int
    hh_compost_pit: int
    segregation_sheds: int
    tricycles_manual: int
    e_rickshaws: int
    motorized_vehicles: int

    class Config:
        from_attributes = True


class LWMAssetsResponse(BaseModel):
    """Response model for LWM assets details."""
    id: int
    pits_hh_level: int
    community_pits: int
    wsp: int
    dewats: int
    wetlands: int
    other_treatments: int
    drainage_channels: int

    class Config:
        from_attributes = True


class PWMUDetailsResponse(BaseModel):
    """Response model for PWMU details."""
    id: int
    established_pwmu: int
    blocks_covered_pwmu: int
    urban_mrfs: int
    blocks_covered_urban_mrf: int

    class Config:
        from_attributes = True


class FSMDetailsResponse(BaseModel):
    """Response model for FSM details."""
    id: int
    twin_pit_toilets: int
    single_pit_toilets: int
    septic_tank_toilets: int
    retrofitted_toilets: int
    mechanized_desludging: int
    fstps_rural: int
    fstps_urban: int

    class Config:
        from_attributes = True


class GobardhanProjectResponse(BaseModel):
    """Response model for Gobar-dhan project details."""
    id: int
    total_sanctioned: int
    total_functional: int
    gas_production: float

    class Config:
        from_attributes = True


class D2DActivitiesResponse(BaseModel):
    """Response model for D2D activities details."""
    id: int
    is_active: bool
    work_frequency: Optional[WorkFrequency]
    sanctioned_tender: int
    sanctioned_self_gp: int
    sanctioned_csr_ngo: int
    sanctioned_shg: int
    sanctioned_mixed_model: int
    total_expenditure: float
    vehicles_deployed: int
    persons_deployed: int
    households_covered: int
    status_start: int
    status_running: int
    status_completed: int

    class Config:
        from_attributes = True


class BartanBankResponse(BaseModel):
    """Response model for Bartan Bank details."""
    id: int
    established_banks: int

    class Config:
        from_attributes = True


class VehicleAssetsResponse(BaseModel):
    """Response model for categorized vehicle assets."""
    id: int
    owned_tricycles: int
    owned_e_rickshaws: int
    owned_motorized_vehicles: int
    contractor_tricycles: int
    contractor_e_rickshaws: int
    contractor_motorized_vehicles: int

    class Config:
        from_attributes = True

# --- End of New Asset Category Response Models ---


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
    village_id: int
    village_name: str
    population: Optional[int]
    num_households: Optional[int]
    sbmg_assets: Optional[VillageSBMGAssetsResponse] = None
    gwm_assets: Optional[VillageGWMAssetsResponse] = None

    class Config:
        from_attributes = True


class AnnualSurveyFYResponse(BaseModel):
    """Response model for annual survey financial year."""

    id: int
    fy: str
    active: bool

    class Config:
        from_attributes = True


class AnnualSurveyResponse(BaseModel):
    """Response model for annual survey details."""

    id: int
    fy_id: int
    gp_id: int
    survey_date: date

    # Geography details
    gp_name: str
    block_name: str
    district_name: str

    # 1. VDO Details
    vdo_id: int
    vdo_name: Optional[str] = None
    vdo_contact_number: Optional[str] = None

    # 2. Sarpanch Details
    sarpanch_name: str
    sarpanch_contact: str

    # 3. No. of Ward Panchs
    num_ward_panchs: int

    # 4. Bidder Name
    agency_id: int
    agency_name: str

    # Sub-sections (optional - only included if they exist)
    vdo: Optional[PositionHolderResponse] = None
    work_order: Optional[WorkOrderDetailsResponse] = None
    fund_sanctioned: Optional[FundSanctionedResponse] = None
    door_to_door_collection: Optional[DoorToDoorCollectionResponse] = None
    road_sweeping: Optional[RoadSweepingDetailsResponse] = None
    drain_cleaning: Optional[DrainCleaningDetailsResponse] = None
    csc_details: Optional[CSCDetailsResponse] = None
    
    # Categorized assets
    odf_sustainability: Optional[ODFSustainabilityResponse] = None
    swm_assets: Optional[SWMAssetsCategoryResponse] = None
    lwm_assets: Optional[LWMAssetsResponse] = None
    pwmu_details: Optional[PWMUDetailsResponse] = None
    fsm_details: Optional[FSMDetailsResponse] = None
    gobardhan_projects: Optional[GobardhanProjectResponse] = None
    d2d_activities: Optional[D2DActivitiesResponse] = None
    bartan_bank: Optional[BartanBankResponse] = None
    vehicle_assets: Optional[VehicleAssetsResponse] = None
    
    sbmg_targets: Optional[SBMGYearTargetsResponse] = None

    # Village data (list)
    village_data: List[VillageDataResponse] = []

    # Timestamps
    last_reconfirmed_at: datetime
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
