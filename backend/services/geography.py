from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException

from models.database.geography import District, Block, Village
from models.database.complaint import Complaint


class GeographyService:
    """Service layer for geography operations."""

    @staticmethod
    async def validate_district_exists(db: AsyncSession, district_id: int) -> District:
        """Validate that a district exists."""
        result = await db.execute(select(District).where(District.id == district_id))
        district = result.scalar_one_or_none()
        if not district:
            raise HTTPException(status_code=400, detail="District not found")
        return district

    @staticmethod
    async def validate_block_exists(db: AsyncSession, block_id: int, district_id: Optional[int] = None) -> Block:
        """Validate that a block exists and optionally belongs to a district."""
        query = select(Block).where(Block.id == block_id)
        if district_id:
            query = query.where(Block.district_id == district_id)

        result = await db.execute(query)
        block = result.scalar_one_or_none()

        if not block:
            if district_id:
                raise HTTPException(
                    status_code=400, detail="Block not found or doesn't belong to the specified district"
                )
            else:
                raise HTTPException(status_code=400, detail="Block not found")

        return block

    @staticmethod
    async def validate_village_exists(db: AsyncSession, village_id: int) -> Village:
        """Validate that a village exists."""
        result = await db.execute(select(Village).where(Village.id == village_id))
        village = result.scalar_one_or_none()
        if not village:
            raise HTTPException(status_code=400, detail="Village not found")
        return village

    @staticmethod
    async def check_district_name_unique(db: AsyncSession, name: str, exclude_id: Optional[int] = None) -> bool:
        """Check if district name is unique."""
        query = select(District).where(District.name == name)
        if exclude_id:
            query = query.where(District.id != exclude_id)

        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        return existing is None

    @staticmethod
    async def check_block_name_unique(
        db: AsyncSession, name: str, district_id: int, exclude_id: Optional[int] = None
    ) -> bool:
        """Check if block name is unique within a district."""
        query = select(Block).where(Block.name == name, Block.district_id == district_id)
        if exclude_id:
            query = query.where(Block.id != exclude_id)

        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        return existing is None

    @staticmethod
    async def check_village_name_unique(
        db: AsyncSession, name: str, block_id: int, exclude_id: Optional[int] = None
    ) -> bool:
        """Check if village name is unique within a block."""
        query = select(Village).where(Village.name == name, Village.block_id == block_id)
        if exclude_id:
            query = query.where(Village.id != exclude_id)

        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        return existing is None

    @staticmethod
    async def can_delete_district(db: AsyncSession, district_id: int) -> bool:
        """Check if a district can be safely deleted."""
        # Check for blocks
        blocks_result = await db.execute(select(func.count(Block.id)).where(Block.district_id == district_id))
        blocks_count = blocks_result.scalar() or 0

        # Check for complaints
        complaints_result = await db.execute(
            select(func.count(Complaint.id)).where(Complaint.district_id == district_id)
        )
        complaints_count = complaints_result.scalar() or 0

        return blocks_count == 0 and complaints_count == 0

    @staticmethod
    async def can_delete_block(db: AsyncSession, block_id: int) -> bool:
        """Check if a block can be safely deleted."""
        # Check for villages
        villages_result = await db.execute(select(func.count(Village.id)).where(Village.block_id == block_id))
        villages_count = villages_result.scalar() or 0

        # Check for complaints
        complaints_result = await db.execute(select(func.count(Complaint.id)).where(Complaint.block_id == block_id))
        complaints_count = complaints_result.scalar() or 0

        return villages_count == 0 and complaints_count == 0

    @staticmethod
    async def can_delete_village(db: AsyncSession, village_id: int) -> bool:
        """Check if a village can be safely deleted."""
        # Check for complaints
        complaints_result = await db.execute(select(func.count(Complaint.id)).where(Complaint.village_id == village_id))
        complaints_count = complaints_result.scalar() or 0

        return complaints_count == 0

    @staticmethod
    async def get_district_with_counts(db: AsyncSession, district_id: int) -> Dict[str, Any]:
        """Get district with associated counts."""
        district = await GeographyService.validate_district_exists(db, district_id)

        # Count blocks
        blocks_result = await db.execute(select(func.count(Block.id)).where(Block.district_id == district_id))
        blocks_count = blocks_result.scalar() or 0

        # Count villages
        villages_result = await db.execute(select(func.count(Village.id)).where(Village.district_id == district_id))
        villages_count = villages_result.scalar() or 0

        # Count complaints
        complaints_result = await db.execute(
            select(func.count(Complaint.id)).where(Complaint.district_id == district_id)
        )
        complaints_count = complaints_result.scalar() or 0

        return {
            "district": district,
            "blocks_count": blocks_count,
            "villages_count": villages_count,
            "complaints_count": complaints_count,
        }

    @staticmethod
    async def get_block_with_counts(db: AsyncSession, block_id: int) -> Dict[str, Any]:
        """Get block with associated counts."""
        block = await GeographyService.validate_block_exists(db, block_id)

        # Count villages
        villages_result = await db.execute(select(func.count(Village.id)).where(Village.block_id == block_id))
        villages_count = villages_result.scalar() or 0

        # Count complaints
        complaints_result = await db.execute(select(func.count(Complaint.id)).where(Complaint.block_id == block_id))
        complaints_count = complaints_result.scalar() or 0

        return {
            "block": block,
            "villages_count": villages_count,
            "complaints_count": complaints_count,
        }

    @staticmethod
    async def get_village_with_counts(db: AsyncSession, village_id: int) -> Dict[str, Any]:
        """Get village with associated counts."""
        village = await GeographyService.validate_village_exists(db, village_id)

        # Count complaints
        complaints_result = await db.execute(select(func.count(Complaint.id)).where(Complaint.village_id == village_id))
        complaints_count = complaints_result.scalar() or 0

        return {
            "village": village,
            "complaints_count": complaints_count,
        }
