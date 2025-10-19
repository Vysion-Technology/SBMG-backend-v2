"""Authentication and user management service."""

from enum import Enum
import random  # pylint: disable=C0415,W0611

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, date, timezone
import uuid

import requests
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, delete, update
from sqlalchemy.orm import selectinload
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from models.database.auth import (
    PositionHolder,
    User,
    Role,
    PublicUser,
    PublicUserOTP,
    PublicUserToken,
)
from config import settings

# Password hashing
pwd_hasher = PasswordHasher()


class UserRole(str, Enum):
    """User roles in the system."""

    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    SMD = "SMD"  # State Mission Director
    CEO = "CEO"  # District Collector
    BDO = "BDO"  # Block Development Officer
    VDO = "VDO"  # Village Development Officer
    WORKER = "WORKER"
    PUBLIC = "PUBLIC"


class AuthService:
    """Service for authentication and user management."""

    def __init__(self, db: AsyncSession):
        self.db = db

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

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode: Dict[str, Any] = data.copy()  # type: ignore
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt

    async def get_current_user_from_token(self, token: str) -> Optional[User]:
        """Get current user from JWT token."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            username: str = payload.get("sub")  # type: ignore
            if username is None:  # type: ignore
                return None
        except JWTError:
            return None

        user = await self.get_user_by_username(username)
        return user

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username with positions loaded."""
        result = await self.db.execute(
            select(User)
            .options(
                selectinload(User.positions).selectinload(PositionHolder.role),
                selectinload(User.positions).selectinload(PositionHolder.village),
                selectinload(User.positions).selectinload(PositionHolder.block),
                selectinload(User.positions).selectinload(PositionHolder.district),
            )
            .where(User.username == username)
        )
        user = result.scalar_one_or_none()
        return user

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID with positions loaded."""
        result = await self.db.execute(
            select(User)
            .options(
                selectinload(User.positions).selectinload(PositionHolder.role),
                selectinload(User.positions).selectinload(PositionHolder.village),
                selectinload(User.positions).selectinload(PositionHolder.block),
                selectinload(User.positions).selectinload(PositionHolder.district),
            )
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        return user

    async def create_user(
        self,
        username: str,
        email: Optional[str],
        password: str,
        is_active: bool = True,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        village_id: Optional[int] = None,
    ) -> User:
        """Create a new user."""
        hashed_password = self.get_password_hash(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=is_active,
            district_id=district_id,
            block_id=block_id,
            village_id=village_id,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_all_users(self, username_like: str = "", skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with optional username filtering."""
        query = select(User).options(selectinload(User.positions).selectinload(PositionHolder.role))

        if username_like:
            query = query.where(User.username.ilike(f"%{username_like}%"))

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        users = result.scalars().all()
        return list(users)

    async def get_users_by_geography(
        self,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        village_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PositionHolder]:
        """Get position holders by geographical location."""
        query = select(PositionHolder).options(
            selectinload(PositionHolder.user),
            selectinload(PositionHolder.role),
            selectinload(PositionHolder.village),
            selectinload(PositionHolder.block),
            selectinload(PositionHolder.district),
        )

        if district_id is not None:
            query = query.where(PositionHolder.district_id == district_id)
        if block_id is not None:
            query = query.where(PositionHolder.block_id == block_id)
        if village_id is not None:
            query = query.where(PositionHolder.village_id == village_id)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        position_holders: List[PositionHolder] = list(result.scalars().all())
        return position_holders

    async def get_role_by_name(self, role_name: str) -> Optional[Role]:
        """Get role by name."""
        result = await self.db.execute(select(Role).where(Role.name == role_name))
        role = result.scalar_one_or_none()
        # If role does not exist, create it
        if not role:
            role = Role(name=role_name, description=f"Auto-created role {role_name}")
            self.db.add(role)
            await self.db.commit()
            await self.db.refresh(role)
        return role

    async def create_position_holder(
        self,
        user_id: int,
        role_id: int,
        first_name: str,
        last_name: str,
        middle_name: Optional[str] = None,
        village_id: Optional[int] = None,
        block_id: Optional[int] = None,
        district_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        date_of_joining: Optional[date] = None,
    ) -> PositionHolder:
        """Create a new position holder."""
        position = PositionHolder(
            user_id=user_id,
            role_id=role_id,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            village_id=village_id,
            block_id=block_id,
            district_id=district_id,
            start_date=start_date,
            end_date=end_date,
            date_of_joining=date_of_joining,
        )
        self.db.add(position)
        await self.db.commit()
        await self.db.refresh(position)
        return position

    async def send_otp(self, mobile_number: str) -> bool:
        """Send OTP to the given phone number."""
        # Placeholder implementation - integrate with actual SMS service

        otp = 123456  # For testing, use a fixed OTP
        # Check if the OTP exists for the phone number
        existing_otp = (
            await self.db.execute(
                select(PublicUserOTP).where(PublicUserOTP.public_user.has(mobile_number=mobile_number))
            )
        ).scalar_one_or_none()
        if existing_otp:
            otp = existing_otp.otp  # Reuse existing OTP

        print(f"Sending OTP {otp} to phone number {mobile_number}")
        # Check if phone number exists in PublicUser table
        public_user = await self.db.execute(select(PublicUser).where(PublicUser.mobile_number == mobile_number))
        public_user = public_user.scalar_one_or_none()
        if not public_user:
            await self.db.execute(insert(PublicUser).values(mobile_number=mobile_number))
            await self.db.commit()
            public_user = await self.db.execute(select(PublicUser).where(PublicUser.mobile_number == mobile_number))
            public_user = public_user.scalar_one_or_none()
        # Insert OTP into PublicUserOTP table
        # Delete all the existing OTPs for this user
        assert public_user is not None, "The user could not be created due to internal errors"
        await self.db.execute(delete(PublicUserOTP).where(PublicUserOTP.public_user_id == public_user.id))
        await self.db.execute(
            insert(PublicUserOTP).values(
                id=public_user.id,
                public_user_id=int(public_user.id),
                otp=str(otp),
                is_verified=False,
                expires_at=datetime.now(tz=timezone.utc) + timedelta(days=365),
            )
        )
        await self.db.commit()
        # Here, you would integrate with an SMS gateway to send the OTP
        send_otp(mobile_number, otp)

        return True

    async def verify_otp(self, mobile_number: str, otp: str) -> str:
        """Verify the OTP for the given phone number."""
        # Placeholder implementation - in real scenario, verify against stored OTP
        print(f"Verifying OTP {otp} for phone number {mobile_number}")
        # Get the OTP from the database and compare
        public_user = await self.db.execute(select(PublicUser).where(PublicUser.mobile_number == mobile_number))
        public_user = public_user.scalar_one_or_none()
        if not public_user:
            raise ValueError("Phone number not registered")
        stored_otp = await self.db.execute(select(PublicUserOTP).where(PublicUserOTP.public_user_id == public_user.id))
        stored_otp = stored_otp.scalar_one_or_none()
        if not stored_otp or stored_otp.otp != otp:
            raise ValueError("You had not requested an OTP earlier or OTP is incorrect")
        # Check if a token already exists for this public user
        existing_token = await self.db.execute(
            select(PublicUserToken).where(PublicUserToken.public_user_id == public_user.id)
        )
        existing_token = existing_token.scalar_one_or_none()
        if existing_token:
            return existing_token.token
        # Create a token for the public user
        token = await self.db.execute(
            insert(PublicUserToken)
            .values(
                id=public_user.id,
                public_user_id=public_user.id,
                token=str(uuid.uuid4()),
                created_at=datetime.now(tz=timezone.utc),
                expires_at=datetime.now(tz=timezone.utc) + timedelta(days=365),
            )
            .returning(PublicUserToken.token)
        )
        # Change the OTP to verified
        await self.db.execute(update(PublicUserOTP).where(PublicUserOTP.id == stored_otp.id).values(is_verified=True))
        token = token.scalar_one()
        await self.db.commit()
        return token

    @staticmethod
    def get_role_by_user(user: User) -> Optional[UserRole]:
        """Extract roles from user's positions."""
        if not (user.village_id and user.block_id and user.district_id):
            return UserRole.ADMIN
        if not user.block_id and user.district_id:
            return UserRole.CEO
        if user.block_id and not user.village_id:
            return UserRole.BDO
        if user.village_id and "contractor" in user.username.lower():
            return UserRole.WORKER
        if user.village_id:
            return UserRole.VDO
        return None

    @staticmethod
    async def get_user_active_position(user: User) -> Optional[PositionHolder]:
        """Get the active position of the user."""
        # Get the first active position
        for position in user.positions:
            return position
        return None

    async def get_public_user_by_token(self, token: str) -> Optional[PublicUser]:
        """Retrieve a public user based on the provided token."""
        result = await self.db.execute(select(PublicUserToken).where(PublicUserToken.token == token))
        public_user_token = result.scalar_one_or_none()
        if not public_user_token:
            return None

        result = await self.db.execute(select(PublicUser).where(PublicUser.id == public_user_token.public_user_id))
        public_user = result.scalar_one_or_none()
        return public_user


def send_otp(mobile_number: str, otp: int | str) -> bool:
    """Send OTP to the given phone number."""

    url = "https://www.fast2sms.com/dev/bulkV2"

    # payload = f"variables_values={otp}&route=otp&numbers={mobile_number}"
    headers = {
        "authorization": "wGrmheyagfiXCqP7sVAD2n8zURu5B6l1jZT4OLS9t3WKHbYNoJy6CTDn1XlmMYLeBsGOjfxVHi07apkE",
        "Content-Type": "application/json",
        # "Content-Type": "application/x-www-form-urlencoded",
        # "Cache-Control": "no-cache",
    }

    response = requests.request(
        "POST",
        url,
        headers=headers,
        json={
            "route": "otp",
            "variables_values": otp,
            "numbers": mobile_number,
        },
        timeout=30,
    )

    print(response.text)
    return True
