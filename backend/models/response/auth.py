from datetime import date
from typing import Optional
from pydantic import BaseModel


class PositionHolderResponse(BaseModel):
    id: int
    user_id: int
    role_id: int
    role_name: str
    first_name: str
    middle_name: Optional[str]
    last_name: str
    username: str
    date_of_joining: Optional[date]
    start_date: Optional[date]
    end_date: Optional[date]
    email: Optional[str]
    district_id: Optional[int]
    district_name: Optional[str]
    block_id: Optional[int]
    block_name: Optional[str]
    village_id: Optional[int]
    village_name: Optional[str]
