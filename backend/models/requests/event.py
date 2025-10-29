"""CreateEventRequest model definition."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CreateEventRequest(BaseModel):
    """Request model for creating a new event."""

    name: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime


class EventUpdateRequest(BaseModel):
    """Request model for updating an existing event."""

    name: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    active: Optional[bool] = None
