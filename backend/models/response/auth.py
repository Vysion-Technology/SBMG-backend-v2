"""Response model for position holder."""

from datetime import date
from typing import Optional
from pydantic import BaseModel


class PositionHolderResponse(BaseModel):
    """Response model for position holder."""

    id: int
    user_id: int
    first_name: str
    last_name: str
    username: str
    middle_name: Optional[str] = None
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    date_of_joining: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    email: Optional[str] = None
    district_id: Optional[int] = None
    district_name: Optional[str] = None
    block_id: Optional[int] = None
    block_name: Optional[str] = None
    village_id: Optional[int] = None
    village_name: Optional[str] = None
