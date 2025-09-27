"""
Person User Management Service
Handles person profiles, designations, role assignments, and position history.
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import ClauseElement, select, update, and_, or_
from sqlalchemy.orm import selectinload

from models.database.auth import Role, PositionHolder
from models.database.geography import District, Block, Village
from auth_utils import UserRole


class PersonManagementService:
    """Service dedicated to person management - profiles, roles, and position assignments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # Username Generation for Login Users
    async def generate_username(
        self,
        role_name: str,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        village_id: Optional[int] = None,
        contractor_name: Optional[str] = None,
    ) -> str:
        """
        Generate username based on role and geography for creating login accounts.
        CEO: district@example.com
        BDO: district.block@example.com
        VDO: district.block.village@example.com
        Worker: district.block.village-sbmg-contractor@example.com
        """
        username_parts: List[str] = []

        # Get district name
        if district_id:
            district_result = await self.db.execute(select(District).where(District.id == district_id))
            district = district_result.scalar_one_or_none()
            if district:
                username_parts.append(district.name.lower().replace(" ", "."))

        # Get block name for BDO, VDO, Worker
        if role_name in [UserRole.BDO, UserRole.VDO, UserRole.WORKER] and block_id:
            block_result = await self.db.execute(select(Block).where(Block.id == block_id))
            block = block_result.scalar_one_or_none()
            if block:
                username_parts.append(block.name.lower().replace(" ", "."))

        # Get village name for VDO, Worker
        if role_name in [UserRole.VDO, UserRole.WORKER] and village_id:
            village_result = await self.db.execute(select(Village).where(Village.id == village_id))
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

    # Role Management
    async def create_role(self, name: str, description: Optional[str] = None) -> Role:
        """Create a new role."""
        # Check if role already exists
        existing_role = await self.get_role_by_name(name)
        if existing_role:
            raise ValueError(f"Role '{name}' already exists")

        role = Role(name=name, description=description)
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        result = await self.db.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    async def get_role_by_id(self, role_id: int) -> Optional[Role]:
        """Get role by ID."""
        result = await self.db.execute(select(Role).where(Role.id == role_id))
        return result.scalar_one_or_none()

    async def get_all_roles(self) -> List[Role]:
        """Get all roles."""
        result = await self.db.execute(select(Role))
        return list(result.scalars().all())

    async def update_role(
        self, role_id: int, name: Optional[str] = None, description: Optional[str] = None
    ) -> Optional[Role]:
        """Update an existing role."""
        role = await self.get_role_by_id(role_id)
        if not role:
            return None

        update_data = {}
        if name is not None:
            # Check if new name already exists
            existing_role = await self.get_role_by_name(name)
            if existing_role and existing_role.id != role_id:
                raise ValueError(f"Role name '{name}' already exists")
            update_data["name"] = name

        if description is not None:
            update_data["description"] = description

        if update_data:
            await self.db.execute(update(Role).where(Role.id == role_id).values(**update_data))
            await self.db.commit()
            await self.db.refresh(role)

        return role

    # Position Holder Management (Person Profile & Designations)
    async def create_position_holder(
        self,
        user_id: int,
        role_id: int,
        first_name: str,
        last_name: str,
        middle_name: Optional[str] = None,
        date_of_joining: Optional[date] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        village_id: Optional[int] = None,
    ) -> PositionHolder:
        """Create a new position holder (person with a designation)."""
        position = PositionHolder(
            user_id=user_id,
            role_id=role_id,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            date_of_joining=date_of_joining,
            start_date=start_date,
            end_date=end_date,
            district_id=district_id,
            block_id=block_id,
            village_id=village_id,
        )
        self.db.add(position)
        await self.db.commit()
        await self.db.refresh(position)
        return position

    async def get_position_holder_by_id(self, position_id: int) -> Optional[PositionHolder]:
        """Get position holder by ID with all related data."""
        result = await self.db.execute(
            select(PositionHolder)
            .options(
                selectinload(PositionHolder.user),
                selectinload(PositionHolder.role),
                selectinload(PositionHolder.district),
                selectinload(PositionHolder.block),
                selectinload(PositionHolder.village),
            )
            .where(PositionHolder.id == position_id)
        )
        return result.scalar_one_or_none()

    async def get_all_position_holders(
        self,
        role_id: Optional[int] = None,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        village_id: Optional[int] = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PositionHolder]:
        """Get position holders with optional filters."""
        query = select(PositionHolder).options(
            selectinload(PositionHolder.user),
            selectinload(PositionHolder.role),
            selectinload(PositionHolder.district),
            selectinload(PositionHolder.block),
            selectinload(PositionHolder.village),
        )

        # Apply filters
        conditions: List[ClauseElement] = []
        if role_id:
            conditions.append(PositionHolder.role_id == role_id)
        if district_id:
            conditions.append(PositionHolder.district_id == district_id)
        if block_id:
            conditions.append(PositionHolder.block_id == block_id)
        if village_id:
            conditions.append(PositionHolder.village_id == village_id)

        if active_only:
            # Consider active if no end_date or end_date is in the future
            conditions.append(or_(PositionHolder.end_date.is_(None), PositionHolder.end_date >= date.today()))

        if conditions:
            query = query.where(and_(*conditions))  # type: ignore

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_position_holders_by_user(self, user_id: int) -> List[PositionHolder]:
        """Get all position holders for a specific user (historical and current)."""
        result = await self.db.execute(
            select(PositionHolder)
            .options(
                selectinload(PositionHolder.role),
                selectinload(PositionHolder.district),
                selectinload(PositionHolder.block),
                selectinload(PositionHolder.village),
            )
            .where(PositionHolder.user_id == user_id)
            .order_by(PositionHolder.start_date.desc())
        )
        return list(result.scalars().all())

    async def update_position_holder(
        self,
        position_id: int,
        first_name: Optional[str] = None,
        middle_name: Optional[str] = None,
        last_name: Optional[str] = None,
        date_of_joining: Optional[date] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Optional[PositionHolder]:
        """Update position holder information."""
        position = await self.get_position_holder_by_id(position_id)
        if not position:
            return None

        update_data = {}
        if first_name is not None:
            update_data["first_name"] = first_name
        if middle_name is not None:
            update_data["middle_name"] = middle_name
        if last_name is not None:
            update_data["last_name"] = last_name
        if date_of_joining is not None:
            update_data["date_of_joining"] = date_of_joining
        if start_date is not None:
            update_data["start_date"] = start_date
        if end_date is not None:
            update_data["end_date"] = end_date

        if update_data:
            await self.db.execute(update(PositionHolder).where(PositionHolder.id == position_id).values(**update_data))
            await self.db.commit()
            await self.db.refresh(position)

        return position

    async def transfer_position(
        self,
        current_position_id: int,
        new_user_id: int,
        transfer_date: date,
        new_first_name: str,
        new_last_name: str,
        new_middle_name: Optional[str] = None,
    ) -> PositionHolder:
        """
        Transfer a position from one person to another.
        This maintains the historical record by ending the current position
        and creating a new position for the new person.
        """
        # Get current position
        current_position = await self.get_position_holder_by_id(current_position_id)
        if not current_position:
            raise ValueError("Position not found")

        # End the current position
        await self.db.execute(
            update(PositionHolder).where(PositionHolder.id == current_position_id).values(end_date=transfer_date)
        )

        # Create new position for the new person
        new_position = PositionHolder(
            user_id=new_user_id,
            role_id=current_position.role_id,
            first_name=new_first_name,
            middle_name=new_middle_name,
            last_name=new_last_name,
            start_date=transfer_date,
            district_id=current_position.district_id,
            block_id=current_position.block_id,
            village_id=current_position.village_id,
        )

        self.db.add(new_position)
        await self.db.commit()
        await self.db.refresh(new_position)
        return new_position

    # Position History and Reporting
    async def get_position_history(
        self,
        role_id: Optional[int] = None,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        village_id: Optional[int] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> List[PositionHolder]:
        """Get historical data of who held which positions during what periods."""
        query = select(PositionHolder).options(
            selectinload(PositionHolder.user),
            selectinload(PositionHolder.role),
            selectinload(PositionHolder.district),
            selectinload(PositionHolder.block),
            selectinload(PositionHolder.village),
        )

        conditions: List[ClauseElement] = []
        if role_id:
            conditions.append(PositionHolder.role_id == role_id)
        if district_id:
            conditions.append(PositionHolder.district_id == district_id)
        if block_id:
            conditions.append(PositionHolder.block_id == block_id)
        if village_id:
            conditions.append(PositionHolder.village_id == village_id)

        # Date range filtering
        if from_date:
            conditions.append(or_(PositionHolder.end_date.is_(None), PositionHolder.end_date >= from_date))
        if to_date:
            conditions.append(or_(PositionHolder.start_date.is_(None), PositionHolder.start_date <= to_date))

        if conditions:
            query = query.where(and_(*conditions))  # type: ignore

        query = query.order_by(PositionHolder.start_date.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_current_position_holders(
        self,
        role_id: Optional[int] = None,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        village_id: Optional[int] = None,
    ) -> List[PositionHolder]:
        """Get currently active position holders."""
        return await self.get_all_position_holders(
            role_id=role_id, district_id=district_id, block_id=block_id, village_id=village_id, active_only=True
        )

    # Person Search and Lookup
    async def search_persons_by_name(self, name_query: str, skip: int = 0, limit: int = 100) -> List[PositionHolder]:
        """Search persons by first, middle, or last name."""
        search_pattern = f"%{name_query}%"
        result = await self.db.execute(
            select(PositionHolder)
            .options(
                selectinload(PositionHolder.user),
                selectinload(PositionHolder.role),
                selectinload(PositionHolder.district),
                selectinload(PositionHolder.block),
                selectinload(PositionHolder.village),
            )
            .where(
                or_(
                    PositionHolder.first_name.ilike(search_pattern),
                    PositionHolder.middle_name.ilike(search_pattern),
                    PositionHolder.last_name.ilike(search_pattern),
                )
            )
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
