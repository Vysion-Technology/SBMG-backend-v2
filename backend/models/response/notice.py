from typing import Optional, List
from datetime import date
from pydantic import BaseModel


class NoticeMediaResponse(BaseModel):
    """Response model for notice media."""

    id: int
    notice_id: int
    media_url: str

    class Config:
        from_attributes = True


class PositionHolderBasicInfo(BaseModel):
    """Basic position holder information for notice."""

    id: int
    first_name: str
    middle_name: Optional[str]
    last_name: str
    role_name: str
    district_name: Optional[str]
    block_name: Optional[str]
    village_name: Optional[str]


class NoticeDetailResponse(BaseModel):
    """Detailed response model for a notice with sender/receiver info."""

    id: int
    sender_id: int
    receiver_id: Optional[int]
    title: str
    date: date
    text: Optional[str]
    media: List[NoticeMediaResponse] = []
    sender_info: Optional[PositionHolderBasicInfo] = None
    receiver_info: Optional[PositionHolderBasicInfo] = None

    class Config:
        from_attributes = True
