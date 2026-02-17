"""
Response Models for Contractor Analytics
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from models.response.annual_survey_analytics import VillageMasterDataCoverage


class ContractorSummary(BaseModel):
    """Summary of a single contractor assigned to a GP."""

    contractor_id: int
    person_name: Optional[str] = None
    person_phone: Optional[str] = None
    agency_name: Optional[str] = None
    contract_amount: float
    contract_start_date: Optional[datetime] = None
    contract_end_date: Optional[datetime] = None
    contract_frequency: Optional[str] = None

    class Config:
        from_attributes = True


class ContractorStateAnalytics(BaseModel):
    """Response model for state-level contractor analytics."""

    total_gps: int
    gps_with_contractor_data: int
    coverage_percentage: float
    total_contractors: int
    total_contract_amount: float

    # Geographic breakdown
    district_wise_coverage: List[VillageMasterDataCoverage]

    class Config:
        from_attributes = True


class ContractorDistrictAnalytics(BaseModel):
    """Response model for district-level contractor analytics."""

    district_id: int
    district_name: str
    total_gps: int
    gps_with_contractor_data: int
    coverage_percentage: float
    total_contractors: int
    total_contract_amount: float

    # Geographic breakdown
    block_wise_coverage: List[VillageMasterDataCoverage]

    class Config:
        from_attributes = True


class ContractorBlockAnalytics(BaseModel):
    """Response model for block-level contractor analytics."""

    block_id: int
    block_name: str
    district_id: int
    district_name: str
    total_gps: int
    gps_with_contractor_data: int
    coverage_percentage: float
    total_contractors: int
    total_contract_amount: float

    # Geographic breakdown
    gp_wise_coverage: List[VillageMasterDataCoverage]

    class Config:
        from_attributes = True


class ContractorGPAnalytics(BaseModel):
    """Response model for GP-level contractor analytics."""

    gp_id: int
    gp_name: str
    block_id: int
    block_name: str
    district_id: int
    district_name: str
    has_contractor: bool
    contractor_data_status: str  # "Available" or "Not Available"
    total_contractors: int
    total_contract_amount: float

    # Contractor details
    contractors: List[ContractorSummary]

    class Config:
        from_attributes = True
