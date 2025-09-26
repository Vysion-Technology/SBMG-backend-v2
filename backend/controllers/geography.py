from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.database.auth import User
from models.database.geography import District, Block, Village
from models.response.geography import (
    DistrictResponse,
    BlockResponse,
    VillageResponse,
)
from auth_utils import require_admin


router = APIRouter()


# List endpoints with pagination
@router.get("/districts", response_model=List[DistrictResponse])
async def list_districts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List all districts with pagination (Admin only)."""
    result = await db.execute(select(District).offset(skip).limit(limit))
    districts = result.scalars().all()

    return [
        DistrictResponse(
            id=district.id, name=district.name, description=district.description
        )
        for district in districts
    ]


@router.get("/blocks", response_model=List[BlockResponse])
async def list_blocks(
    district_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List all blocks with pagination (Admin only)."""
    query = select(Block)

    if district_id:
        query = query.where(Block.district_id == district_id)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    blocks = result.scalars().all()

    return [
        BlockResponse(
            id=block.id,
            name=block.name,
            description=block.description,
            district_id=block.district_id,
        )
        for block in blocks
    ]


@router.get("/villages", response_model=List[VillageResponse])
async def list_villages(
    block_id: Optional[int] = None,
    district_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List all villages with pagination (Admin only)."""
    query = select(Village)

    if block_id:
        query = query.where(Village.block_id == block_id)
    elif district_id:
        query = query.where(Village.district_id == district_id)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    villages = result.scalars().all()

    return [
        VillageResponse(
            id=village.id,
            name=village.name,
            description=village.description,
            block_id=village.block_id,
            district_id=village.district_id,
        )
        for village in villages
    ]


@router.get("/villages/{village_id}", response_model=VillageResponse)
async def get_village(
    village_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific village by ID (Admin only)."""
    result = await db.execute(select(Village).where(Village.id == village_id))
    village = result.scalar_one_or_none()

    if not village:
        raise HTTPException(status_code=404, detail="Village not found")

    return VillageResponse(
        id=village.id,
        name=village.name,
        description=village.description,
        block_id=village.block_id,
        district_id=village.district_id,
    )


@router.get("/blocks/{block_id}", response_model=BlockResponse)
async def get_block(
    block_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific block by ID (Admin only)."""
    result = await db.execute(select(Block).where(Block.id == block_id))
    block = result.scalar_one_or_none()

    if not block:
        raise HTTPException(status_code=404, detail="Block not found")

    return BlockResponse(
        id=block.id,
        name=block.name,
        description=block.description,
        district_id=block.district_id,
    )


@router.get("/districts/{district_id}", response_model=DistrictResponse)
async def get_district(
    district_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific district by ID (Admin only)."""
    result = await db.execute(select(District).where(District.id == district_id))
    district = result.scalar_one_or_none()

    if not district:
        raise HTTPException(status_code=404, detail="District not found")

    return DistrictResponse(
        id=district.id, name=district.name, description=district.description
    )
