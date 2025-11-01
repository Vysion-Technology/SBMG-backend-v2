"""Response models for notices."""

from typing import Optional, List
from datetime import date, datetime

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
    role_id: int
    middle_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class NoticeReplyResponse(BaseModel):
    """Response model for notice reply."""

    id: int
    notice_id: int
    replier_id: int
    reply_text: str
    reply_datetime: datetime
    replier: Optional[PositionHolderBasicInfo] = None

    class Config:
        """Pydantic config for model serialization."""
        from_attributes = True


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
    replies: List[NoticeReplyResponse] = []

    class Config:
        """Pydantic config for model serialization."""
        from_attributes = True
