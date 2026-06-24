"""
Response Models for Annual Survey Analytics
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SchemeTargetAchievement(BaseModel):
    """Response model for scheme-wise target vs achievement."""

    scheme_code: str  # IHHL, CSC, RRC, PWMU, Soak pit, Magic pit, Leach pit, WSP, DEWATS
    scheme_name: str
    target: int
    achievement: int
    achievement_percentage: float

    class Config:
        from_attributes = True


class VillageMasterDataCoverage(BaseModel):
    """Response model for village master data coverage by geography."""

    geography_id: int
    geography_name: str
    total_gps: int
    gps_with_data: int
    coverage_percentage: float
    master_data_status: str  # "Available" or "Not Available"

    class Config:
        from_attributes = True


class AnnualOverview(BaseModel):
    """Response model for annual overview metrics."""

    fund_utilization_rate: float  # Percentage
    average_cost_per_household_d2d: Optional[float]  # Average cost for D2D collection
    households_covered_d2d: int  # Total households covered in D2D
    gps_with_asset_gaps: int  # GPs where targets > achievements
    active_sanitation_bidders: int  # Unique agencies

    class Config:
        from_attributes = True


class StateAnalytics(BaseModel):
    """Response model for state-level analytics."""

    total_village_master_data: int  # Total GP surveys
    village_master_data_coverage_percentage: float
    total_funds_sanctioned: float  # In Crores
    total_work_order_amount: float  # In Crores
    sbmg_target_achievement_rate: float  # Overall percentage

    # Detailed breakdowns
    scheme_wise_target_achievement: List[SchemeTargetAchievement]
    annual_overview: AnnualOverview
    district_wise_coverage: List[VillageMasterDataCoverage]

    class Config:
        from_attributes = True


class DistrictAnalytics(BaseModel):
    """Response model for district-level analytics."""

    district_id: int
    district_name: str
    total_village_master_data: int
    village_master_data_coverage_percentage: float
    total_funds_sanctioned: float
    total_work_order_amount: float
    sbmg_target_achievement_rate: float

    # Detailed breakdowns
    scheme_wise_target_achievement: List[SchemeTargetAchievement]
    annual_overview: AnnualOverview
    block_wise_coverage: List[VillageMasterDataCoverage]

    class Config:
        from_attributes = True


class BlockAnalytics(BaseModel):
    """Response model for block-level analytics."""

    block_id: int
    block_name: str
    district_id: int
    district_name: str
    total_village_master_data: int
    village_master_data_coverage_percentage: float
    total_funds_sanctioned: float
    total_work_order_amount: float
    sbmg_target_achievement_rate: float

    # Detailed breakdowns
    scheme_wise_target_achievement: List[SchemeTargetAchievement]
    annual_overview: AnnualOverview
    gp_wise_coverage: List[VillageMasterDataCoverage]

    class Config:
        from_attributes = True


class GPAnalytics(BaseModel):
    """Response model for GP-level analytics."""

    gp_id: int
    gp_name: str
    block_id: int
    block_name: str
    district_id: int
    district_name: str
    has_master_data: bool
    master_data_available: str  # "Available" or "Not Available"

    # Survey details if available
    survey_id: Optional[int] = None
    survey_date: Optional[str] = None
    total_funds_sanctioned: Optional[float] = None
    total_work_order_amount: Optional[float] = None

    # Scheme-wise data
    scheme_wise_target_achievement: List[SchemeTargetAchievement]

    # Annual overview
    fund_utilization_rate: Optional[float] = None
    households_covered_d2d: Optional[int] = None
    num_villages: Optional[int] = None
    active_agency_name: Optional[str] = None

    class Config:
        from_attributes = True


class VillageAnalytics(BaseModel):
    """Response model for village-level analytics within a GP survey."""

    village_id: int
    village_name: str
    gp_id: int
    gp_name: str
    population: Optional[int] = None
    num_households: Optional[int] = None

    # SBMG Assets
    ihhl: Optional[int] = None
    csc: Optional[int] = None

    # GWM Assets
    soak_pit: Optional[int] = None
    magic_pit: Optional[int] = None
    leach_pit: Optional[int] = None
    wsp: Optional[int] = None
    dewats: Optional[int] = None

    class Config:
        from_attributes = True


# --- Assets Dashboard Models ---

class ODFSustainabilityStats(BaseModel):
    ihhl: int
    retrofitting: int
    csc: int
    csc_shala_darpan: int


class SWMAssetsStats(BaseModel):
    bins_hh_level: int
    bins_public_places: int
    community_compost_pits: int
    hh_compost_pit: int
    segregation_sheds: int
    tricycles_manual: int
    e_rickshaws: int
    motorized_vehicles: int


class LWMAssetsStats(BaseModel):
    pits_hh_level: int
    community_pits: int
    wsp: int
    dewats: int
    wetlands: int
    other_treatments: int
    drainage_channels: int


class PWMUStats(BaseModel):
    established_pwmu: int
    blocks_covered_pwmu: int
    urban_mrfs: int
    blocks_covered_urban_mrf: int


class FSMStats(BaseModel):
    twin_pit_toilets: int
    single_pit_toilets: int
    septic_tank_toilets: int
    retrofitted_toilets: int
    mechanized_desludging: int
    fstps_rural: int
    fstps_urban: int


class GobardhanStats(BaseModel):
    total_sanctioned: int
    total_functional: int
    gas_production: float


class WorkFrequencyCount(BaseModel):
    daily: int = 0
    weekly: int = 0
    fifteen_days: int = Field(0, alias="15 days")
    monthly: int = 0

    class Config:
        populate_by_name = True


class D2DActivitiesStats(BaseModel):
    total_gps: int
    gps_with_d2d_active: int
    not_started_gps: int
    running_started_gps: int
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
    work_frequency_count: WorkFrequencyCount


class BartanBankStats(BaseModel):
    established_banks: int
    revenue: float


class VehicleStats(BaseModel):
    owned_tricycles: int
    owned_e_rickshaws: int
    owned_motorized_vehicles: int
    contractor_tricycles: int
    contractor_e_rickshaws: int
    contractor_motorized_vehicles: int


class AssetsDashboardResponse(BaseModel):
    """Unified response model for the Assets Dashboard."""
    odf_sustainability: ODFSustainabilityStats
    swm_assets: SWMAssetsStats
    lwm_assets: LWMAssetsStats
    pwmu: PWMUStats
    fsm: FSMStats
    gobardhan: GobardhanStats
    d2d_activities: D2DActivitiesStats
    bartan_bank: BartanBankStats
    vehicle_assets: VehicleStats
    contracts_ending_next_month: int = 0

    class Config:
        from_attributes = True


class GeographyAssetBreakdown(BaseModel):
    """Asset breakdown for a specific geography (District/Block/GP)."""
    geography_id: int
    geography_name: str
    assets: AssetsDashboardResponse


class HierarchicalAssetsResponse(BaseModel):
    """Response model for hierarchical asset analytics."""
    geography_type: str  # "district", "block", or "gp"
    items: List[GeographyAssetBreakdown]
