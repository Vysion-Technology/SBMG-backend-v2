"""
Response Models for Inspection Management
"""

from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel
from models.database.inspection import (
    WasteCollectionFrequency,
    RoadCleaningFrequency,
    DrainCleaningFrequency,
    CSCCleaningFrequency,
)


class InspectionImageResponse(BaseModel):
    """Response model for inspection image."""

    id: int
    inspection_id: int
    image_url: str

    class Config:
        from_attributes = True


class HouseHoldWasteCollectionResponse(BaseModel):
    """Response model for household waste collection inspection items."""

    id: int
    waste_collection_frequency: Optional[WasteCollectionFrequency]
    dry_wet_vehicle_segregation: Optional[bool]
    covered_collection_in_vehicles: Optional[bool]
    waste_disposed_at_rrc: Optional[bool]
    rrc_waste_collection_and_disposal_arrangement: Optional[bool]
    waste_collection_vehicle_functional: Optional[bool]

    class Config:
        from_attributes = True


class RoadAndDrainCleaningResponse(BaseModel):
    """Response model for road and drain cleaning inspection items."""

    id: int
    road_cleaning_frequency: Optional[RoadCleaningFrequency]
    drain_cleaning_frequency: Optional[DrainCleaningFrequency]
    disposal_of_sludge_from_drains: Optional[bool]
    drain_waste_colllected_on_roadside: Optional[bool]

    class Config:
        from_attributes = True


class CommunitySanitationResponse(BaseModel):
    """Response model for community sanitation inspection items."""

    id: int
    csc_cleaning_frequency: Optional[CSCCleaningFrequency]
    electricity_and_water: Optional[bool]
    csc_used_by_community: Optional[bool]
    pink_toilets_cleaning: Optional[bool]
    pink_toilets_used: Optional[bool]

    class Config:
        from_attributes = True


class OtherInspectionItemsResponse(BaseModel):
    """Response model for other inspection items."""

    id: int
    firm_paid_regularly: Optional[bool]
    cleaning_staff_paid_regularly: Optional[bool]
    firm_provided_safety_equipment: Optional[bool]
    regular_feedback_register_entry: Optional[bool]
    chart_prepared_for_cleaning_work: Optional[bool]
    village_visibly_clean: Optional[bool]
    rate_chart_displayed: Optional[bool]

    class Config:
        from_attributes = True


class InspectionResponse(BaseModel):
    """Response model for inspection details."""

    id: int
    remarks: Optional[str]
    position_holder_id: int
    village_id: int
    date: date
    start_time: Optional[datetime]
    lat: Optional[str]
    long: Optional[str]
    register_maintenance: Optional[bool]

    # Officer details
    officer_name: str
    officer_role: str

    # Geography details
    village_name: str
    block_name: str
    district_name: str

    # Inspection items (optional - only included if they exist)
    household_waste: Optional[HouseHoldWasteCollectionResponse] = None
    road_and_drain: Optional[RoadAndDrainCleaningResponse] = None
    community_sanitation: Optional[CommunitySanitationResponse] = None
    other_items: Optional[OtherInspectionItemsResponse] = None

    # Images
    images: List[InspectionImageResponse] = []

    class Config:
        from_attributes = True


class InspectionListItemResponse(BaseModel):
    """Response model for inspection list item (summary view)."""

    id: int
    village_id: int
    village_name: str
    block_name: str
    district_name: str
    date: date
    officer_name: str
    officer_role: str
    remarks: Optional[str]

    class Config:
        from_attributes = True


class PaginatedInspectionResponse(BaseModel):
    """Paginated response for inspections list."""

    items: List[InspectionListItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class InspectionStatsResponse(BaseModel):
    """Response model for inspection statistics."""

    total_inspections: int
    inspections_this_month: int
    inspections_this_week: int
    inspections_today: int
    villages_inspected: int
