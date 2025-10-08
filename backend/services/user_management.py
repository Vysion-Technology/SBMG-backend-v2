from datetime import date
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models.database.auth import User, Role, PositionHolder
from models.database.geography import District, Block, GramPanchayat
from services.auth import AuthService
from auth_utils import UserRole


class UserManagementService:
    """Service for managing users, roles, and position holders."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.auth_service = AuthService(db)

    async def generate_username(
        self,
        role_name: str,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        village_id: Optional[int] = None,
        contractor_name: Optional[str] = None,
    ) -> str:
        """
        Generate username based on role and geography.
        CEO: district@example.com
        BDO: district.block@example.com
        VDO: district.block.village@example.com
        Worker: district.block.village-sbmg-contractor@example.com
        """
        username_parts = []

        # Get district name
        if district_id:
            district_result = await self.db.execute(
                select(District).where(District.id == district_id)
            )
            district = district_result.scalar_one_or_none()
            if district:
                username_parts.append(district.name.lower().replace(" ", "."))

        # Get block name for BDO, VDO, Worker
        if role_name in [UserRole.BDO, UserRole.VDO, UserRole.WORKER] and block_id:
            block_result = await self.db.execute(
                select(Block).where(Block.id == block_id)
            )
            block = block_result.scalar_one_or_none()
            if block:
                username_parts.append(block.name.lower().replace(" ", "."))

        # Get village name for VDO, Worker
        if role_name in [UserRole.VDO, UserRole.WORKER] and village_id:
            village_result = await self.db.execute(
                select(GramPanchayat).where(GramPanchayat.id == village_id)
            )
            village = village_result.scalar_one_or_none()
            if village:
                username_parts.append(village.name.lower().replace(" ", "."))

        # Add contractor suffix for Worker
        if role_name == UserRole.WORKER and contractor_name:
            contractor_suffix = f"sbmg-{contractor_name.lower().replace(' ', '-')}"
            username_parts.append(contractor_suffix)

        # Join parts and add domain
        if username_parts:
            username = ".".join(username_parts) + "@example.com"
        else:
            # Fallback for roles without geography (like ADMIN)
            username = role_name.lower() + "@example.com"

        return username

    async def create_role(self, name: str, description: Optional[str] = None) -> Role:
        """Create a new role."""
        # Check if role already exists
        existing_role = await self.auth_service.get_role_by_name(name)
        if existing_role:
            raise ValueError(f"Role '{name}' already exists")

        role = Role(name=name, description=description)
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def get_role_by_id(self, role_id: int) -> Optional[Role]:
        """Get role by ID."""
        result = await self.db.execute(select(Role).where(Role.id == role_id))
        return result.scalar_one_or_none()

    async def get_all_roles(self) -> List[Role]:
        """Get all roles."""
        result = await self.db.execute(select(Role))
        return list(result.scalars().all())

    async def update_role(
        self,
        role_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Role]:
        """Update an existing role."""
        role = await self.get_role_by_id(role_id)
        if not role:
            return None

        if name is not None:
            # Check if new name already exists (exclude current role)
            existing_role = await self.auth_service.get_role_by_name(name)
            if existing_role and existing_role.id != role_id:
                raise ValueError(f"Role '{name}' already exists")
            role.name = name

        if description is not None:
            role.description = description

        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def create_user_with_position(
        self,
        role_name: str,
        first_name: str,
        last_name: str,
        middle_name: Optional[str] = None,
        date_of_joining: Optional[str] = None,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        village_id: Optional[int] = None,
        contractor_name: Optional[str] = None,
        password: Optional[date] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> tuple[User, PositionHolder]:
        """Create a new user with position holder."""
        # Get role
        role = await self.auth_service.get_role_by_name(role_name)
        if not role:
            raise ValueError(f"Role '{role_name}' not found")

        # Generate username
        username = await self.generate_username(
            role_name, district_id, block_id, village_id, contractor_name
        )

        # Generate email from username
        email = username

        # Use default password if not provided
        if not password:
            password = "DefaultPassword123!"  # Should be changed on first login

        # Create user
        user = await self.auth_service.create_user(
            username=username, email=email, password=password, is_active=True
        )

        # Create position holder
        position = await self.auth_service.create_position_holder(
            user_id=user.id,
            role_id=role.id,
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

        return user, position

    async def get_position_holder_by_id(
        self, position_id: int
    ) -> Optional[PositionHolder]:
        """Get position holder by ID with all relationships loaded."""
        result = await self.db.execute(
            select(PositionHolder)
            .options(
                selectinload(PositionHolder.user),
                selectinload(PositionHolder.role),
                selectinload(PositionHolder.village),
                selectinload(PositionHolder.block),
                selectinload(PositionHolder.district),
            )
            .where(PositionHolder.id == position_id)
        )
        return result.scalar_one_or_none()

    async def update_position_holder(
        self,
        position_id: int,
        first_name: Optional[str] = None,
        middle_name: Optional[str] = None,
        last_name: Optional[str] = None,
        date_of_joining: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        is_admin_update: bool = False,
    ) -> Optional[PositionHolder]:
        """Update position holder. Only admins can update critical fields."""
        position = await self.get_position_holder_by_id(position_id)
        if not position:
            return None

        # Update fields that anyone can modify
        if start_date is not None:
            position.start_date = start_date
        if end_date is not None:
            position.end_date = end_date

        # Critical fields only admins can update
        if is_admin_update:
            if first_name is not None:
                position.first_name = first_name
            if middle_name is not None:
                position.middle_name = middle_name
            if last_name is not None:
                position.last_name = last_name
            if date_of_joining is not None:
                position.date_of_joining = date_of_joining

        await self.db.commit()
        await self.db.refresh(position)
        return position

    async def get_all_position_holders(
        self, skip: int = 0, limit: int = 100
    ) -> List[PositionHolder]:
        """Get all position holders with relationships loaded."""
        result = await self.db.execute(
            select(PositionHolder)
            .options(
                selectinload(PositionHolder.user),
                selectinload(PositionHolder.role),
                selectinload(PositionHolder.village),
                selectinload(PositionHolder.block),
                selectinload(PositionHolder.district),
            )
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_position_holders_by_role(
        self, role_name: str, skip: int = 0, limit: int = 100
    ) -> List[PositionHolder]:
        """Get position holders by role name."""
        result = await self.db.execute(
            select(PositionHolder)
            .join(Role)
            .options(
                selectinload(PositionHolder.user),
                selectinload(PositionHolder.role),
                selectinload(PositionHolder.village),
                selectinload(PositionHolder.block),
                selectinload(PositionHolder.district),
            )
            .where(Role.name == role_name)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def change_user_password(self, user_id: int, new_password: str) -> bool:
        """Change user password (Admin only operation)."""
        if not new_password or len(new_password.strip()) < 8:
            raise ValueError("Password must be at least 8 characters long")

        # Get the user
        user = await self.auth_service.get_user_by_id(user_id)
        if not user:
            return False

        # Hash the new password
        hashed_password = self.auth_service.get_password_hash(new_password)

        # Update the user's password
        user.hashed_password = hashed_password
        await self.db.commit()
        await self.db.refresh(user)

        return True
