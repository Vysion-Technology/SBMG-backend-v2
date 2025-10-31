"""Position Holder service - CRUD operations without access control."""

from typing import List, Optional
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from exceptions.position_holders import ActivePositionHolderExistsError
from models.database.auth import PositionHolder, Role


class PositionHolderService:
    """Service for position holder management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_position_holders_by_geo_ids(
        self,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        village_id: Optional[int] = None,
    ) -> List[PositionHolder]:
        """Get active position holders filtered by geographic IDs."""
        query = select(PositionHolder).options(
            selectinload(PositionHolder.user),
            selectinload(PositionHolder.role),
            selectinload(PositionHolder.gp),
            selectinload(PositionHolder.block),
            selectinload(PositionHolder.district),
        ).where(
            PositionHolder.end_date.is_(None)
        )

        if district_id is not None:
            query = query.where(PositionHolder.district_id == district_id)
        if block_id is not None:
            query = query.where(PositionHolder.block_id == block_id)
        if village_id is not None:
            query = query.where(PositionHolder.gp_id == village_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

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
        pos_holders = await self.get_active_position_holders_by_geo_ids(
            district_id=district_id,
            block_id=block_id,
            village_id=village_id,
        )
        if pos_holders:
            raise ActivePositionHolderExistsError("An active position holder already exists for the given geographic assignment.")
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

    async def get_position_holder_by_id(self, position_id: int) -> Optional[PositionHolder]:
        """Get position holder by ID with all relationships loaded."""
        result = await self.db.execute(
            select(PositionHolder)
            .options(
                selectinload(PositionHolder.user),
                selectinload(PositionHolder.role),
                selectinload(PositionHolder.gp),
                selectinload(PositionHolder.block),
                selectinload(PositionHolder.district),
            )
            .where(PositionHolder.id == position_id)
        )
        return result.scalar_one_or_none()

    async def get_all_position_holders(
        self,
        role_id: Optional[int] = None,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        gp_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PositionHolder]:
        """Get all position holders with optional filtering."""
        query = select(PositionHolder).options(
            selectinload(PositionHolder.user),
            selectinload(PositionHolder.role),
            selectinload(PositionHolder.gp),
            selectinload(PositionHolder.block),
            selectinload(PositionHolder.district),
        )

        if role_id is not None:
            query = query.where(PositionHolder.role_id == role_id)
        if district_id is not None:
            query = query.where(PositionHolder.district_id == district_id)
        if block_id is not None:
            query = query.where(PositionHolder.block_id == block_id)
        if gp_id is not None:
            query = query.where(PositionHolder.gp_id == gp_id)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_position_holder(
        self,
        position_id: int,
        first_name: Optional[str] = None,
        middle_name: Optional[str] = None,
        last_name: Optional[str] = None,
        role_id: Optional[int] = None,
        village_id: Optional[int] = None,
        block_id: Optional[int] = None,
        district_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        date_of_joining: Optional[date] = None,
    ) -> Optional[PositionHolder]:
        """Update position holder details."""
        # Build update dict with only provided values
        update_data = {}
        if first_name is not None:
            update_data["first_name"] = first_name
        if middle_name is not None:
            update_data["middle_name"] = middle_name
        if last_name is not None:
            update_data["last_name"] = last_name
        if role_id is not None:
            update_data["role_id"] = role_id
        if village_id is not None:
            update_data["village_id"] = village_id
        if block_id is not None:
            update_data["block_id"] = block_id
        if district_id is not None:
            update_data["district_id"] = district_id
        if start_date is not None:
            update_data["start_date"] = start_date
        if end_date is not None:
            update_data["end_date"] = end_date
        if date_of_joining is not None:
            update_data["date_of_joining"] = date_of_joining

        if not update_data:
            # No updates provided, just return existing
            return await self.get_position_holder_by_id(position_id)

        await self.db.execute(
            update(PositionHolder)
            .where(PositionHolder.id == position_id)
            .values(**update_data)
        )
        await self.db.commit()

        return await self.get_position_holder_by_id(position_id)

    async def delete_position_holder(self, position_id: int) -> bool:
        """Delete a position holder."""
        result = await self.db.execute(
            delete(PositionHolder).where(PositionHolder.id == position_id)
        )
        await self.db.commit()
        return result.rowcount > 0  # type: ignore

    async def get_role_by_name(self, role_name: str) -> Optional[Role]:
        """Get role by name."""
        result = await self.db.execute(select(Role).where(Role.name == role_name))
        return result.scalar_one_or_none()

    async def get_position_holder_ids_by_user(self, user_id: int) -> List[int]:
        """Get position holder IDs associated with a user."""
        result = await self.db.execute(
            select(PositionHolder.id).where(PositionHolder.user_id == user_id)
        )
        return [row[0] for row in result.all()]
