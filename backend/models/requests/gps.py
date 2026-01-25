"""Request models for GPS tracking operations."""

from pydantic import BaseModel, Field


class AddVehicleRequest(BaseModel):
    """Request model for adding a new vehicle."""

    gp_id: int = Field(..., description="Gram Panchayat ID")
    vehicle_no: str = Field(..., description="Vehicle number to add")
    imei: str = Field(..., description="IMEI number of the vehicle GPS device")
    name: str = Field(..., description="Name of the vehicle")
