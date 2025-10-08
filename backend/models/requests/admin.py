from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CreateUserRequest(BaseModel):
    username: str
    email: Optional[str]
    password: str
    is_active: bool = True


class CreatePositionHolderRequest(BaseModel):
    user_id: int
    role_name: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    village_id: Optional[int] = None
    block_id: Optional[int] = None
    district_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class CreateRoleRequest(BaseModel):
    name: str
    description: Optional[str] = None

