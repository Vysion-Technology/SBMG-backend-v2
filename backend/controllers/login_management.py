"""
Login User Management Controller
Handles authentication, login credentials, and user account management.
"""

from typing import List, Optional
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from database import get_db
from models.database.auth import User
from services.login_user_service import LoginUserService
from auth_utils import require_admin, get_current_active_user
from config import settings

router = APIRouter()


# Pydantic models for Login User Management
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class CreateLoginUserRequest(BaseModel):
    username: str
    email: Optional[str] = None
    password: str
    is_active: bool = True


class UpdateLoginUserRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class ResetPasswordRequest(BaseModel):
    new_password: str


class LoginUserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    is_active: bool


# Authentication Endpoints
@router.post("/login", response_model=TokenResponse)
async def login_for_access_token(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT token."""
    login_service = LoginUserService(db)
    user = await login_service.authenticate_user(request.username, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = login_service.create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=LoginUserResponse)
async def get_current_login_user(
    current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
):
    """Get current authenticated user's login information."""
    return LoginUserResponse(
        id=current_user.id, username=current_user.username, email=current_user.email, is_active=current_user.is_active
    )


# Login User Management Endpoints (Admin only)
@router.post("/users", response_model=LoginUserResponse)
async def create_login_user(
    request: CreateLoginUserRequest, current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    """Create a new login user account (Admin only)."""
    try:
        login_service = LoginUserService(db)
        user = await login_service.create_login_user(
            username=request.username, email=request.email, password=request.password, is_active=request.is_active
        )
        return LoginUserResponse(id=user.id, username=user.username, email=user.email, is_active=user.is_active)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/users", response_model=List[LoginUserResponse])
async def get_all_login_users(
    username_like: str = "",
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = False,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get all login users (Admin only)."""
    login_service = LoginUserService(db)
    users = await login_service.get_all_login_users(
        username_like=username_like, skip=skip, limit=limit, include_inactive=include_inactive
    )
    return [
        LoginUserResponse(id=user.id, username=user.username, email=user.email, is_active=user.is_active)
        for user in users
    ]


@router.get("/users/{user_id}", response_model=LoginUserResponse)
async def get_login_user_by_id(
    user_id: int, current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    """Get login user by ID (Admin only)."""
    login_service = LoginUserService(db)
    user = await login_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return LoginUserResponse(id=user.id, username=user.username, email=user.email, is_active=user.is_active)


@router.put("/users/{user_id}", response_model=LoginUserResponse)
async def update_login_user(
    user_id: int,
    request: UpdateLoginUserRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update login user credentials (Admin only)."""
    try:
        login_service = LoginUserService(db)
        user = await login_service.update_login_credentials(
            user_id=user_id,
            username=request.username,
            email=request.email,
            password=request.password,
            is_active=request.is_active,
        )

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return LoginUserResponse(id=user.id, username=user.username, email=user.email, is_active=user.is_active)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/users/{user_id}/deactivate")
async def deactivate_login_user(
    user_id: int, current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    """Deactivate a login user account (Admin only)."""
    login_service = LoginUserService(db)
    success = await login_service.deactivate_user(user_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {"message": "User deactivated successfully"}


@router.post("/users/{user_id}/activate")
async def activate_login_user(
    user_id: int, current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    """Activate a login user account (Admin only)."""
    login_service = LoginUserService(db)
    success = await login_service.activate_user(user_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {"message": "User activated successfully"}


# Password Management
@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Change current user's password."""
    login_service = LoginUserService(db)
    success = await login_service.change_password(
        user_id=current_user.id, old_password=request.old_password, new_password=request.new_password
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid old password")

    return {"message": "Password changed successfully"}


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    request: ResetPasswordRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Reset user password (Admin only)."""
    login_service = LoginUserService(db)
    success = await login_service.reset_password(user_id=user_id, new_password=request.new_password)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {"message": "Password reset successfully"}
