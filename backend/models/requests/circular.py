"""Request models for circulars."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CreateCircularRequest(BaseModel):
    """Request model for creating a new circular."""

    title: str
    description: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class CircularUpdateRequest(BaseModel):
    """Request model for updating an existing circular."""

    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
