"""Response models for notices."""

from typing import Optional, List
from datetime import date

from pydantic import BaseModel


class NoticeTypeResponse(BaseModel):
    """Response model for notice type."""

    id: int
    name: str
    description: Optional[str] = None

    class Config:
        """Pydantic config for model serialization."""
        from_attributes = True

class NoticeMediaResponse(BaseModel):
    """Response model for notice media."""

    id: int
    notice_id: int
    media_url: str

    class Config:
        """Pydantic config for model serialization."""
        from_attributes = True


class PositionHolderBasicInfo(BaseModel):
    """Basic position holder information for notice."""

    id: int
    user_id: int
    first_name: str
    last_name: str
    role_name: str
    middle_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class NoticeDetailResponse(BaseModel):
    """Detailed response model for a notice with sender/receiver info."""

    id: int
    sender_id: int
    receiver_id: Optional[int]
    title: str
    date: date
    text: Optional[str]
    media: List[NoticeMediaResponse] = []
    sender: Optional[PositionHolderBasicInfo] = None
    receiver: Optional[PositionHolderBasicInfo] = None

    class Config:
        """Pydantic config for model serialization."""
        from_attributes = True
