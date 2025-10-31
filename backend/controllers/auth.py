from services.auth import UserRole
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


class PasswordResetOTPRequest(BaseModel):
    user_id: int


class PasswordResetVerifyRequest(BaseModel):
    user_id: int
    otp: str
    new_password: str


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
    village_id: Optional[int]
    block_id: Optional[int]
    district_id: Optional[int]
    role: UserRole = UserRole.WORKER
    positions: list[PositionInfo] = []


class AuthController:
    """Controller for authentication-related operations."""
    def __init__(self, db: AsyncSession):
        self.auth_service = AuthService(db)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return await self.auth_service.get_user_by_username(username)

    async def get_all_users(self, username_like: str = "", skip: int = 0, limit: int = 100) -> list[User]:
        """Get all users with optional username filter and pagination."""
        return await self.auth_service.get_all_users(username_like, skip, limit)

    async def get_users_by_geography(
        self,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        village_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PositionHolder]:
        """Get users filtered by geography with pagination."""
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

    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = auth_service.create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)

    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""

    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        village_id=current_user.gp_id,
        block_id=current_user.block_id,
        district_id=current_user.district_id,
        role=AuthService.get_role_by_user(current_user) or UserRole.WORKER,
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


@router.get("/user", response_model=UserResponse)
async def get_user_info(
    username: str,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Get user information by username."""
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        village_id=user.gp_id,
        block_id=user.block_id,
        district_id=user.district_id,
        role=AuthService.get_role_by_user(user) or UserRole.WORKER,
        positions=[],
    )


@router.post("/password-reset/send-otp")
async def send_password_reset_otp(request: PasswordResetOTPRequest, db: AsyncSession = Depends(get_db)):
    """Send OTP to user for password reset."""
    auth_service = AuthService(db)
    try:
        otp_sent = await auth_service.send_password_reset_otp(request.user_id)
        if not otp_sent:
            raise HTTPException(status_code=500, detail="Failed to send OTP")
        return {"detail": "OTP sent successfully", "user_id": request.user_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/password-reset/verify-otp")
async def verify_password_reset_otp(request: PasswordResetVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verify OTP and update user's password."""
    auth_service = AuthService(db)
    try:
        success = await auth_service.verify_password_reset_otp(request.user_id, request.otp, request.new_password)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to reset password")
        return {"detail": "Password reset successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
