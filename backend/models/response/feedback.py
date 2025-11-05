"""Feedback response models."""


from pydantic import BaseModel

class FeedbackResponse(BaseModel):
    """Response model for feedback."""

    id: int
    auth_user_id: int | None
    public_user_id: int | None
    rating: int
    comment: str | None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class FeedbackStatsResponse(BaseModel):
    """Response model for feedback statistics."""

    total_feedback: int
    average_rating: float
    auth_user_avg_rating: float
    public_user_avg_rating: float
