"""GPS Tracking Response Models."""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class GPSTrackingResponse(BaseModel):
    """Response model for GPS tracking data."""

    id: int = Field(..., description="GPS tracking record ID")
    vehicle_no: str = Field(..., description="Vehicle registration number")
    imei: str = Field(..., description="Device IMEI number")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    speed: float = Field(..., description="Speed in km/h")
    ignition: bool = Field(..., description="Ignition status")
    total_gps_odometer: float = Field(..., description="Total GPS odometer reading in km")
    timestamp: datetime = Field(..., description="Timestamp of the GPS reading")


class UniqueVehiclesResponse(BaseModel):
    """Response model for unique vehicles list."""

    vehicles: List[str] = Field(..., description="List of unique vehicle numbers")
    total_count: int = Field(..., description="Total count of unique vehicles")


class VehicleTrackingResponse(BaseModel):
    """Response model for vehicle tracking data."""

    vehicle_no: str = Field(..., description="Vehicle registration number")
    tracking_data: List[GPSTrackingResponse] = Field(..., description="List of GPS tracking records")
    total_records: int = Field(..., description="Total number of tracking records")


class VehicleBaseResponse(BaseModel):
    """Base response model for a vehicle."""

    vehicle_no: str = Field(..., description="Vehicle registration number")
    imei: str = Field(..., description="Device IMEI number")


class VehicleResponse(VehicleBaseResponse):
    """Response model for a single vehicle."""

    id: int = Field(..., description="Vehicle ID")
    gp_id: int = Field(..., description="Gram Panchayat ID")


class GPVehiclesListResponse(BaseModel):
    """Response model for list of vehicles."""

    vehicles: List[VehicleResponse] = Field(..., description="List of vehicles")
    gp_id: int = Field(..., description="Gram Panchayat ID")
    total_count: int = Field(..., description="Total count of vehicles")
