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


class VdoEventImageResponse(BaseModel):
    """Response model for VDO-uploaded event image."""
    id: int
    event_id: int
    vdo_id: int
    gp_id: int
    block_id: int
    district_id: int
    media_url: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class VdoEventImageTrackResponse(BaseModel):
    """Response model for tracking VDO-uploaded event images."""
    id: int
    event_id: int
    vdo_id: int
    vdo_username: str
    gp_id: int
    gp_name: str
    block_id: int
    block_name: str
    district_id: int
    district_name: str
    media_url: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

