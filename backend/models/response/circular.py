"""Response models for circulars."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CircularResponse(BaseModel):
    """Response model for a circular."""

    id: int
    title: str
    description: str
    pdf_url: str
    image_url: Optional[str] = None
    created_at: datetime
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    class Config:
        """Pydantic config for CircularResponse."""

        from_attributes = True
