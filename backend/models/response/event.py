""""Event response models definition."""
from datetime import datetime
from pydantic import BaseModel


class EventMedia(BaseModel):
    """Response model for event media."""
    id: int
    event_id: int
    media_url: str

    class Config:
        """Pydantic config for EventMedia."""
        from_attributes = True


class EventResponse(BaseModel):
    """Response model for an event."""
    id: int
    name: str
    description: str | None
    start_time: datetime
    end_time: datetime
    active: bool

    media: list[EventMedia] = []

    class Config:
        """Pydantic config for EventResponse."""
        from_attributes = True
