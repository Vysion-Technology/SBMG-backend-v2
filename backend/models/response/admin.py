"""Admin Response Models."""

from typing import Optional

from pydantic import BaseModel


class Role(BaseModel):
    """Role information."""

    id: int
    name: str
    description: str | None


class User(BaseModel):
    """User information."""

    id: int
    username: str
    email: str
    is_active: bool
    role: Role | None


class PositionHolder(BaseModel):
    """Basic position holder information."""

    id: int
    user_id: int
    first_name: str
    last_name: str
    middle_name: str | None
    start_date: str | None
    end_date: str | None


class UserResponse(BaseModel):
    """User information response model."""

    id: int
    username: str
    email: Optional[str]
    is_active: bool


class RoleResponse(BaseModel):
    """Role information response model."""

    id: int
    name: str
    description: Optional[str]
