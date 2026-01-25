"""GPS Tracking Response Models."""

from datetime import date, datetime
from typing import List

from pydantic import BaseModel, Field

from models.internal import GeoTypeEnum


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
    name: str | None = Field(None, description="Name of the vehicle")


class VehicleResponse(VehicleBaseResponse):
    """Response model for a single vehicle."""

    id: int = Field(..., description="Vehicle ID")
    gp_id: int = Field(..., description="Gram Panchayat ID")


class GPVehiclesListResponse(BaseModel):
    """Response model for list of vehicles."""

    vehicles: List[VehicleResponse] = Field(..., description="List of vehicles")
    gp_id: int = Field(..., description="Gram Panchayat ID")
    total_count: int = Field(..., description="Total count of vehicles")


class CoordinatesResponse(BaseModel):
    """Response model for vehicle coordinates."""

    lat: float = Field(..., description="Latitude coordinate")
    long: float = Field(..., description="Longitude coordinate")


class RunningVehiclesResponse(BaseModel):
    """Response model for running vehicles."""

    vehicle_id: int = Field(..., description="Vehicle ID")
    name: str = Field(..., description="Vehicle name")
    vehicle_no: str = Field(..., description="Vehicle registration number")
    status: str = Field(..., description="Running status of the vehicle")
    speed: float = Field(..., description="Current speed of the vehicle in km/h")
    last_updated: datetime = Field(..., description="Timestamp of the last update")
    coordinates: CoordinatesResponse = Field(..., description="Current coordinates of the vehicle")
    route: List[CoordinatesResponse] = Field(..., description="Route coordinates of the vehicle")


class LocationLineItem(BaseModel):
    """Model for location line item."""

    type: GeoTypeEnum = Field(..., description="Geographical type (e.g., district, block, GP)")
    district: str = Field(..., description="District name")
    block: str = Field(..., description="Block name")
    gp: str = Field(..., description="Gram Panchayat name")


class RunningVehicleSummaryResponse(BaseModel):
    """Response model for running vehicle summary."""

    total: int = Field(..., description="Total number of vehicles")
    running: int = Field(..., description="Number of running vehicles")
    stopped: int = Field(..., description="Number of stopped vehicles")
    active: int = Field(..., description="Number of active vehicles")
    inactive: int = Field(..., description="Number of inactive vehicles")


class RunningVehiclesListResponse(BaseModel):
    """Response model for list of running vehicles."""

    date_: date = Field(..., description="Date of the report")
    location: LocationLineItem = Field(..., description="Location details")
    summary: RunningVehicleSummaryResponse = Field(..., description="Summary of running vehicles")
    vehicles: List[RunningVehiclesResponse] = Field(..., description="List of running vehicles")
