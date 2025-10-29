"""Request model for creating a new scheme."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CreateSchemeRequest(BaseModel):
    """Request model for creating a new scheme."""

    name: str
    description: Optional[str] = None
    eligibility: Optional[str] = None
    benefits: Optional[str] = None
    start_time: datetime
    end_time: datetime


class SchemeUpdateRequest(BaseModel):
    """Request model for updating an existing scheme."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    eligibility: Optional[str] = None
    benefits: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    active: Optional[bool] = None
