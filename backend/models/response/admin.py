from typing import Optional
from pydantic import BaseModel


class Role(BaseModel):
    id: int
    name: str
    description: str | None

class User(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    role: Role | None

class PositionHolder(BaseModel):
    id: int
    user_id: int
    first_name: str
    middle_name: str | None
    last_name: str
    start_date: str | None
    end_date: str | None


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    is_active: bool


class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]