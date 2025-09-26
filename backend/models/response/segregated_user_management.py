"""
Response Models for Segregated User Management
"""

from typing import List, Optional
from datetime import date

from pydantic import BaseModel


# Login User Management Response Models
class LoginUserResponse(BaseModel):
    """Response model for login user information."""

    id: int
    username: str
    email: Optional[str]
    is_active: bool


class TokenResponse(BaseModel):
    """Response model for authentication token."""

    access_token: str
    token_type: str


# Person Management Response Models
class RoleResponse(BaseModel):
    """Response model for role information."""

    id: int
    name: str
    description: Optional[str]


class PersonResponse(BaseModel):
    """Response model for person information."""

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


class PersonWithLoginResponse(BaseModel):
    """Response model for person with associated login information."""

    person: PersonResponse
    login_user: LoginUserResponse


# Position History Models
class PositionHistoryResponse(BaseModel):
    """Response model for position history."""

    position_id: int
    person_name: str
    role_name: str
    start_date: Optional[date]
    end_date: Optional[date]
    is_current: bool
    location: str  # Combined district, block, village


# Generic Response Models
class MessageResponse(BaseModel):
    """Generic message response."""

    message: str


class PaginatedResponse(BaseModel):
    """Generic paginated response."""

    items: List[dict]
    total: int
    skip: int
    limit: int


# Dashboard/Summary Models
class UserSummaryResponse(BaseModel):
    """Summary of user statistics."""

    total_login_users: int
    active_login_users: int
    total_persons: int
    active_positions: int
    roles_count: int


class RoleSummaryResponse(BaseModel):
    """Summary of role assignments."""

    role_id: int
    role_name: str
    current_holders: int
    total_assignments_ever: int
    locations_covered: int
