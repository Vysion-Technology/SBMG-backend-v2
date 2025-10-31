"""Request models for position holder operations."""

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class CreateEmployeeRequest(BaseModel):
    """Request model for creating an employee."""

    first_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    employee_id: str = Field(..., max_length=50)
    mobile_number: str = Field(..., max_length=15)


class UpdateEmployeeRequest(BaseModel):
    """Request model for updating an employee."""

    email: Optional[str] = Field(None, max_length=255)
    mobile_number: Optional[str] = Field(None, max_length=15)

class CreatePositionHolderRequest(BaseModel):
    """Request model for creating a position holder."""

    user_id: int = Field(..., description="ID of the user to assign position")
    role_name: str = Field(..., description="Role name (CEO/BDO/VDO)")
    first_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    village_id: Optional[int] = Field(None, description="Village ID (required for VDO)")
    block_id: Optional[int] = Field(None, description="Block ID (required for BDO/VDO)")
    district_id: Optional[int] = Field(None, description="District ID (required for CEO/BDO/VDO)")
    start_date: Optional[date] = Field(None, description="Position start date")
    end_date: Optional[date] = Field(None, description="Position end date")
    date_of_joining: Optional[date] = Field(None, description="Date of joining")


class UpdatePositionHolderRequest(BaseModel):
    """Request model for updating a position holder."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role_name: Optional[str] = Field(None, description="Role name (CEO/BDO/VDO)")
    village_id: Optional[int] = Field(None, description="Village ID")
    block_id: Optional[int] = Field(None, description="Block ID")
    district_id: Optional[int] = Field(None, description="District ID")
    start_date: Optional[date] = Field(None, description="Position start date")
    end_date: Optional[date] = Field(None, description="Position end date")
    date_of_joining: Optional[date] = Field(None, description="Date of joining")
