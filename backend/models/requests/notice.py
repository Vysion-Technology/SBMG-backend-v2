from typing import Optional, List
from pydantic import BaseModel, Field


class CreateNoticeRequest(BaseModel):
    """Request model for creating a notice."""

    district_id: int = Field(..., description="District ID (required)")
    block_id: Optional[int] = Field(
        None, description="Block ID (optional - to target specific block)"
    )
    village_id: Optional[int] = Field(
        None, description="Village ID (optional - to target specific village)"
    )
    title: str = Field(..., min_length=1, max_length=500, description="Notice title")
    text: Optional[str] = Field(None, description="Notice text content")
    media_urls: Optional[List[str]] = Field(
        None, description="List of media URLs attached to the notice"
    )
