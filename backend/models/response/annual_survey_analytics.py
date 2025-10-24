"""
Response Models for Annual Survey Analytics
"""

from typing import List, Optional
from pydantic import BaseModel


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
