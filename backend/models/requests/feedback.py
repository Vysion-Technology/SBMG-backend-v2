"""Request models for feedback operations."""

from typing import Dict
from pydantic import BaseModel, Field


class FeedbackCreateRequest(BaseModel):
    """Request model for creating feedback."""

    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: str | None = Field(None, description="Optional comment for the feedback")

    class Config:
        """Pydantic configuration."""

        json_schema_extra: Dict[str, Dict[str, str | int]] = {
            "example": {
                "rating": 5,
                "comment": "Great service!",
            }
        }


class FeedbackUpdateRequest(BaseModel):
    """Request model for updating feedback."""

    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: str | None = Field(None, description="Optional comment for the feedback")

    class Config:
        """Pydantic configuration."""

        json_schema_extra: Dict[str, Dict[str, str | int]] = {
            "example": {
                "rating": 4,
                "comment": "Updated feedback comment",
            }
        }
