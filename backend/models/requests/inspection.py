"""
Request Models for Inspection Management
"""

from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field
from models.database.inspection import (
    WasteCollectionFrequency,
    RoadCleaningFrequency,
    DrainCleaningFrequency,
    CSCCleaningFrequency,
)


class HouseHoldWasteCollectionRequest(BaseModel):
    """Request model for household waste collection inspection items."""

    waste_collection_frequency: Optional[WasteCollectionFrequency] = None
    dry_wet_vehicle_segregation: Optional[bool] = None
    covered_collection_in_vehicles: Optional[bool] = None
    waste_disposed_at_rrc: Optional[bool] = None
    rrc_waste_collection_and_disposal_arrangement: Optional[bool] = None
    waste_collection_vehicle_functional: Optional[bool] = None


class RoadAndDrainCleaningRequest(BaseModel):
    """Request model for road and drain cleaning inspection items."""

    road_cleaning_frequency: Optional[RoadCleaningFrequency] = None
    drain_cleaning_frequency: Optional[DrainCleaningFrequency] = None
    disposal_of_sludge_from_drains: Optional[bool] = None
    drain_waste_colllected_on_roadside: Optional[bool] = None


class CommunitySanitationRequest(BaseModel):
    """Request model for community sanitation inspection items."""

    csc_cleaning_frequency: Optional[CSCCleaningFrequency] = None
    electricity_and_water: Optional[bool] = None
    csc_used_by_community: Optional[bool] = None
    pink_toilets_cleaning: Optional[bool] = None
    pink_toilets_used: Optional[bool] = None


class OtherInspectionItemsRequest(BaseModel):
    """Request model for other inspection items."""

    firm_paid_regularly: Optional[bool] = None
    cleaning_staff_paid_regularly: Optional[bool] = None
    firm_provided_safety_equipment: Optional[bool] = None
    regular_feedback_register_entry: Optional[bool] = None
    chart_prepared_for_cleaning_work: Optional[bool] = None
    village_visibly_clean: Optional[bool] = None
    rate_chart_displayed: Optional[bool] = None


class InspectionImageRequest(BaseModel):
    """Request model for inspection image."""

    image_url: str = Field(..., description="URL of the uploaded image")


class CreateInspectionRequest(BaseModel):
    """Request model for creating a new inspection."""

    gp_id: int = Field(..., description="ID of the village being inspected")
    village_name: str = Field(..., description="Name of the village being inspected")
    remarks: Optional[str] = Field(
        None, description="General remarks about the inspection"
    )
    inspection_date: Optional[date] = Field(
        None, description="Date of inspection (defaults to today)"
    )
    start_time: Optional[datetime] = Field(None, description="Start time of inspection")
    lat: str = Field(..., description="Latitude of inspection location")
    long: str = Field(..., description="Longitude of inspection location")
    register_maintenance: Optional[bool] = Field(
        None, description="Whether registers are properly maintained"
    )

    # Inspection items
    household_waste: Optional[HouseHoldWasteCollectionRequest] = None
    road_and_drain: Optional[RoadAndDrainCleaningRequest] = None
    community_sanitation: Optional[CommunitySanitationRequest] = None
    other_items: Optional[OtherInspectionItemsRequest] = None
