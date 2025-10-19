from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, insert
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from models.database.geography import District, Block, GramPanchayat
from models.database.complaint import Complaint
from models.requests.geography import (
    CreateDistrictRequest,
    CreateBlockRequest,
    CreateGPRequest,
)


class GeographyService:
    """Service layer for geography operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def validate_district_exists(self, district_id: int) -> District:
        """Validate that a district exists."""
        result = await self.db.execute(
            select(District).where(District.id == district_id)
        )
        district = result.scalar_one_or_none()
        if not district:
            raise HTTPException(status_code=400, detail="District not found")
        return district

    async def validate_block_exists(
        self,
        block_id: int,
        district_id: Optional[int] = None,
    ) -> Block:
        """Validate that a block exists and optionally belongs to a district."""
        query = select(Block).where(Block.id == block_id)
        if district_id:
            query = query.where(Block.district_id == district_id)

        result = await self.db.execute(query)
        block = result.scalar_one_or_none()

        if not block:
            if district_id:
                print(f"Block {block_id} not found in district {district_id}")
                raise HTTPException(
                    status_code=400,
                    detail="Block not found or doesn't belong to the specified district",
                )
            else:
                raise HTTPException(status_code=400, detail="Block not found")

        return block

    async def validate_village_exists(self, village_id: int) -> GramPanchayat:
        """Validate that a village exists."""
        result = await self.db.execute(
            select(GramPanchayat)
            .join(Block, GramPanchayat.block_id == Block.id)
            .join(District, Block.district_id == District.id)
            .options(
                selectinload(GramPanchayat.block),
                selectinload(GramPanchayat.district),
            )
            .where(GramPanchayat.id == village_id)
        )
        village = result.scalar_one_or_none()
        if not village:
            raise HTTPException(status_code=400, detail="Village not found")
        return village

    async def check_district_name_unique(
        self,
        name: str,
        exclude_id: Optional[int] = None,
    ) -> bool:
        """Check if district name is unique."""
        query = select(District).where(District.name == name)
        if exclude_id:
            query = query.where(District.id != exclude_id)

        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()
        return existing is None

    async def check_block_name_unique(
        self,
        name: str,
        district_id: int,
        exclude_id: Optional[int] = None,
    ) -> bool:
        """Check if block name is unique within a district."""
        query = select(Block).where(
            Block.name == name, Block.district_id == district_id
        )
        if exclude_id:
            query = query.where(Block.id != exclude_id)

        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()
        return existing is None

    async def check_village_name_unique(
        self,
        name: str,
        block_id: int,
        exclude_id: Optional[int] = None,
    ) -> bool:
        """Check if village name is unique within a block."""
        query = select(GramPanchayat).where(
            GramPanchayat.name == name, GramPanchayat.block_id == block_id
        )
        if exclude_id:
            query = query.where(GramPanchayat.id != exclude_id)

        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()
        return existing is None

    async def can_delete_district(self, district_id: int) -> bool:
        """Check if a district can be safely deleted."""
        # Check for blocks
        blocks_result = await self.db.execute(
            select(func.count(Block.id)).where(Block.district_id == district_id)
        )
        blocks_count = blocks_result.scalar() or 0

        # Check for complaints
        complaints_result = await self.db.execute(
            select(func.count(Complaint.id)).where(Complaint.district_id == district_id)
        )
        complaints_count = complaints_result.scalar() or 0

        return blocks_count == 0 and complaints_count == 0

    async def can_delete_block(self, block_id: int) -> bool:
        """Check if a block can be safely deleted."""
        # Check for villages
        villages_result = await self.db.execute(
            select(func.count(GramPanchayat.id)).where(
                GramPanchayat.block_id == block_id
            )
        )
        villages_count = villages_result.scalar() or 0

        # Check for complaints
        complaints_result = await self.db.execute(
            select(func.count(Complaint.id)).where(Complaint.block_id == block_id)
        )
        complaints_count = complaints_result.scalar() or 0

        return villages_count == 0 and complaints_count == 0

    async def can_delete_village(self, village_id: int) -> bool:
        """Check if a village can be safely deleted."""
        # Check for complaints
        complaints_result = await self.db.execute(
            select(func.count(Complaint.id)).where(Complaint.village_id == village_id)
        )
        complaints_count = complaints_result.scalar() or 0

        return complaints_count == 0

    async def get_district_with_counts(self, district_id: int) -> Dict[str, Any]:
        """Get district with associated counts."""
        district = await self.validate_district_exists(district_id)

        # Count blocks
        blocks_result = await self.db.execute(
            select(func.count(Block.id)).where(Block.district_id == district_id)
        )
        blocks_count = blocks_result.scalar() or 0

        # Count villages
        villages_result = await self.db.execute(
            select(func.count(GramPanchayat.id)).where(
                GramPanchayat.district_id == district_id
            )
        )
        villages_count = villages_result.scalar() or 0

        # Count complaints
        complaints_result = await self.db.execute(
            select(func.count(Complaint.id)).where(Complaint.district_id == district_id)
        )
        complaints_count = complaints_result.scalar() or 0

        return {
            "district": district,
            "blocks_count": blocks_count,
            "villages_count": villages_count,
            "complaints_count": complaints_count,
        }

    async def get_block_with_counts(self, block_id: int) -> Dict[str, Any]:
        """Get block with associated counts."""
        block = await self.validate_block_exists(block_id)

        # Count villages
        villages_result = await self.db.execute(
            select(func.count(GramPanchayat.id)).where(
                GramPanchayat.block_id == block_id
            )
        )
        villages_count = villages_result.scalar() or 0

        # Count complaints
        complaints_result = await self.db.execute(
            select(func.count(Complaint.id)).where(Complaint.block_id == block_id)
        )
        complaints_count = complaints_result.scalar() or 0

        return {
            "block": block,
            "villages_count": villages_count,
            "complaints_count": complaints_count,
        }

    async def get_village(self, village_id: int) -> GramPanchayat:
        """Get village details."""
        village = await self.validate_village_exists(village_id)
        return village

    async def get_block(self, block_id: int) -> Block:
        """Get block details."""
        block = await self.validate_block_exists(block_id)
        return block

    async def get_district(self, district_id: int) -> District:
        """Get district details."""
        district = await self.validate_district_exists(district_id)
        return district

    async def get_village_with_counts(self, village_id: int) -> Dict[str, Any]:
        """Get village with associated counts."""
        village = await self.validate_village_exists(village_id)

        # Count complaints
        complaints_result = await self.db.execute(
            select(func.count(Complaint.id)).where(Complaint.village_id == village_id)
        )
        complaints_count = complaints_result.scalar() or 0

        return {
            "village": village,
            "complaints_count": complaints_count,
        }

    async def list_districts(self) -> list[District]:
        """List all districts."""
        result = await self.db.execute(select(District).order_by(District.name))
        return list(result.scalars().all())

    async def list_blocks(self, district_id: Optional[int] = None) -> list[Block]:
        """List all blocks, optionally filtered by district."""
        query = select(Block).order_by(Block.name)
        if district_id:
            query = query.where(Block.district_id == district_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_villages(
        self,
        block_id: Optional[int] = None,
        district_id: Optional[int] = None,
    ) -> list[GramPanchayat]:
        """List all villages, optionally filtered by block or district."""
        query = select(GramPanchayat).order_by(GramPanchayat.id)
        if block_id:
            query = query.where(GramPanchayat.block_id == block_id)
        if district_id:
            query = query.where(GramPanchayat.district_id == district_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_district(self, district_req: CreateDistrictRequest) -> District:
        """Create a new district."""
        is_unique = await self.check_district_name_unique(district_req.name)
        if not is_unique:
            print(f"District name must be unique: {district_req.name}")
            raise HTTPException(status_code=400, detail="District name must be unique")

        new_district = await self.db.execute(
            insert(District)
            .values(name=district_req.name, description=district_req.description)
            .returning(District)
        )
        await self.db.commit()
        return new_district.scalar_one()

    async def create_block(self, block_req: CreateBlockRequest) -> Block:
        """Create a new block."""
        # Validate district exists
        await self.validate_district_exists(block_req.district_id)

        is_unique = await self.check_block_name_unique(
            block_req.name, block_req.district_id
        )
        if not is_unique:
            raise HTTPException(
                status_code=400,
                detail="Block name must be unique within the district",
            )

        new_block = await self.db.execute(
            insert(Block)
            .values(
                name=block_req.name,
                description=block_req.description,
                district_id=block_req.district_id,
            )
            .returning(Block)
        )
        await self.db.commit()
        return new_block.scalar_one()

    async def create_gp(self, village_req: CreateGPRequest) -> GramPanchayat:
        """Create a new gram panchayat."""
        # Validate block and district exist
        await self.validate_block_exists(village_req.block_id, village_req.district_id)

        is_unique = await self.check_village_name_unique(
            village_req.name, village_req.block_id
        )
        if not is_unique:
            raise HTTPException(
                status_code=400,
                detail="Village name must be unique within the block",
            )

        new_village = await self.db.execute(
            insert(GramPanchayat)
            .values(
                name=village_req.name,
                description=village_req.description,
                block_id=village_req.block_id,
                district_id=village_req.district_id,
            )
            .returning(GramPanchayat)
        )
        await self.db.commit()
        return new_village.scalar_one()
