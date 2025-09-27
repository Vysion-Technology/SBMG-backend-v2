from datetime import datetime
from pydantic import BaseModel


class EventMedia(BaseModel):
    id: int
    event_id: int
    media_url: str

    class Config:
        from_attributes = True


class EventResponse(BaseModel):
    id: int
    name: str
    description: str | None
    start_time: datetime
    end_time: datetime
    active: bool

    media: list[EventMedia] = []

    class Config:
        from_attributes = True
