from typing import List, Optional
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from database import get_db
from models.database.auth import PositionHolder, User
from services.auth import AuthService
from config import settings


# Security
security = HTTPBearer()

# Router
router = APIRouter()


# Pydantic models for request/response
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class PositionInfo(BaseModel):
    role: str
    role_id: int
    first_name: str
    middle_name: Optional[str]
    last_name: str
    district_name: Optional[str]
    block_name: Optional[str]
    village_name: Optional[str]


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    is_active: bool
    roles: list[str]
    positions: list[PositionInfo]


class AuthController:
    def __init__(self, db: AsyncSession):
        self.auth_service = AuthService(db)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        return await self.auth_service.get_user_by_username(username)

    async def get_all_users(self, username_like: str = "", skip: int = 0, limit: int = 100) -> list[User]:
        return await self.auth_service.get_all_users(username_like, skip, limit)

    async def get_users_by_geography(
        self,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        village_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PositionHolder]:
        return await self.auth_service.get_users_by_geography(district_id, block_id, village_id, skip, limit)


# Dependency to get current user from token
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current user from JWT token."""
    auth_service = AuthService(db)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        user = await auth_service.get_current_user_from_token(token)
        if user is None:
            raise credentials_exception
        return user
    except Exception:
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# Route handlers
@router.post("/login", response_model=TokenResponse)
async def login(login_request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT token."""
    auth_service = AuthService(db)

    user = await auth_service.authenticate_user(login_request.username, login_request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not exist",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = auth_service.create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)

    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    # Extract roles from positions
    # roles = [pos.role.name for pos in current_user.positions if pos.role]

    # Create position info
    # positions: List[PositionInfo] = []
    # for pos in current_user.positions:
    #     position_info = PositionInfo(
    #         role=pos.role.name if pos.role else "",
    #         role_id=pos.role.id if pos.role else 0,
    #         first_name=pos.first_name,
    #         middle_name=pos.middle_name,
    #         last_name=pos.last_name,
    #         district_name=pos.district.name if pos.district else None,
    #         block_name=pos.block.name if pos.block else None,
    #         village_name=pos.village.name if pos.village else None,
    #     )
    #     positions.append(position_info)

    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        roles=[],
        positions=[],
    )


@router.post("send-otp")
async def send_otp(mobile_number: str, db: AsyncSession = Depends(get_db)):
    """Send OTP to the given phone number."""
    auth_service = AuthService(db)
    otp_sent = await auth_service.send_otp(mobile_number)
    if not otp_sent:
        raise HTTPException(status_code=500, detail="Failed to send OTP")
    return {"detail": "OTP sent successfully"}


@router.post("verify-otp")
async def verify_otp(mobile_number: str, otp: str, db: AsyncSession = Depends(get_db)):
    """Verify OTP and return JWT token."""
    auth_service = AuthService(db)
    token = await auth_service.verify_otp(mobile_number, otp)
    return {"token": token}
