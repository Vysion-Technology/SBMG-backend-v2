"""
Login User Management Service
Handles authentication, credentials, and login-related operations only.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from models.database.auth import User
from config import settings

# Password hashing
pwd_hasher = PasswordHasher()


class LoginUserService:
    """Service dedicated to login user management - authentication and credentials only."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # Authentication Methods
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against a hashed password."""
        try:
            pwd_hasher.verify(hashed_password, plain_password)
            return True
        except VerifyMismatchError:
            return False

    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return pwd_hasher.hash(password)

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password."""
        user = await self.get_user_by_username(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    # Token Management
    def create_access_token(
        self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        to_encode: dict[str, Any] = data.copy()  # type: ignore
        if expires_delta:
            expire = datetime.now(tz=timezone.utc) + expires_delta
        else:
            expire = datetime.now(tz=timezone.utc) + timedelta(
                minutes=settings.access_token_expire_minutes
            )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.secret_key, algorithm=settings.algorithm
        )
        return encoded_jwt

    async def get_current_user_from_token(self, token: str) -> Optional[User]:
        """Get current user from JWT token."""
        try:
            payload = jwt.decode(
                token, settings.secret_key, algorithms=[settings.algorithm]
            )
            username = payload.get("sub")
            if username is None:
                return None
        except JWTError:
            return None

        user = await self.get_user_by_username(username)
        return user

    # Login User CRUD Operations (credentials only)
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username for authentication purposes."""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID for authentication purposes."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email for authentication purposes."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create_login_user(
        self, username: str, email: Optional[str], password: str, is_active: bool = True
    ) -> User:
        """Create a new login user with credentials only."""
        # Check if username already exists
        existing_user = await self.get_user_by_username(username)
        if existing_user:
            raise ValueError(f"Username '{username}' already exists")

        # Check if email already exists (if provided)
        if email:
            existing_email = await self.get_user_by_email(email)
            if existing_email:
                raise ValueError(f"Email '{email}' already exists")

        hashed_password = self.get_password_hash(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=is_active,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_login_credentials(
        self,
        user_id: int,
        username: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[User]:
        """Update login credentials only."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        update_data = {}

        if username is not None and username != user.username:
            # Check if new username already exists
            existing_user = await self.get_user_by_username(username)
            if existing_user and existing_user.id != user_id:
                raise ValueError(f"Username '{username}' already exists")
            update_data["username"] = username

        if email is not None and email != user.email:
            # Check if new email already exists
            existing_email = await self.get_user_by_email(email)
            if existing_email and existing_email.id != user_id:
                raise ValueError(f"Email '{email}' already exists")
            update_data["email"] = email

        if password is not None:
            update_data["hashed_password"] = self.get_password_hash(password)

        if is_active is not None:
            update_data["is_active"] = is_active

        if update_data:
            await self.db.execute(
                update(User).where(User.id == user_id).values(**update_data)
            )
            await self.db.commit()
            # Refresh user object
            await self.db.refresh(user)

        return user

    async def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user account."""
        result = await self.db.execute(
            update(User).where(User.id == user_id).values(is_active=False)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def activate_user(self, user_id: int) -> bool:
        """Activate a user account."""
        result = await self.db.execute(
            update(User).where(User.id == user_id).values(is_active=True)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def get_all_login_users(
        self,
        username_like: str = "",
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> List[User]:
        """Get all login users for management purposes."""
        query = select(User)

        if username_like:
            query = query.where(User.username.ilike(f"%{username_like}%"))

        if not include_inactive:
            query = query.where(User.is_active)

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def change_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> bool:
        """Change user password with old password verification."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        # Verify old password
        if not self.verify_password(old_password, user.hashed_password):
            return False

        # Update to new password
        new_hashed_password = self.get_password_hash(new_password)
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(hashed_password=new_hashed_password)
        )
        await self.db.commit()
        return True

    async def reset_password(self, user_id: int, new_password: str) -> bool:
        """Admin function to reset user password without old password."""
        result = await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(hashed_password=self.get_password_hash(new_password))
        )
        await self.db.commit()
        return result.rowcount > 0
