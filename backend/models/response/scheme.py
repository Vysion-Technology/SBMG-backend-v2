"""Response models for schemes and their associated media."""
from datetime import datetime
from pydantic import BaseModel


class SchemeMedia(BaseModel):
    """Response model for scheme media."""

    id: int
    scheme_id: int
    media_url: str

    class Config:
        """Pydantic config for SchemeMedia."""

        from_attributes = True


class SchemeResponse(BaseModel):
    """Response model for a scheme."""
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
        """Pydantic config for SchemeResponse."""

        from_attributes = True
