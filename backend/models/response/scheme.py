from datetime import datetime
from pydantic import BaseModel


class SchemeMedia(BaseModel):
    id: int
    scheme_id: int
    media_url: str

    class Config:
        from_attributes = True


class SchemeResponse(BaseModel):
    id: int
    name: str
    description: str | None
    eligibility: str | None
    benefits: str | None
    start_time: datetime
    end_time: datetime
    active: bool

    media: list[SchemeMedia] = []

    class Config:
        from_attributes = True