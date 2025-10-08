from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database import get_db
from models.database.geography import District, Block, Village
from models.database.contractor import Contractor
from models.response.geography import (
    DistrictResponse,
    BlockResponse,
    VillageResponse,
)
from models.response.contractor import AgencyResponse, ContractorResponse


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


@router.get("/villages/{village_id}/contractor", response_model=ContractorResponse)
async def get_contractors_by_village(
    village_id: int,
    db: AsyncSession = Depends(get_db),
) -> ContractorResponse:
    """Get all contractors for a specific village."""
    # First check if village exists
    village_result = await db.execute(select(Village).where(Village.id == village_id))
    village = village_result.scalar_one_or_none()

    if not village:
        raise HTTPException(status_code=404, detail="Village not found")

    # Get contractors for this village with related data
    query = (
        select(Contractor)
        .options(
            joinedload(Contractor.agency),
            joinedload(Contractor.village)
            .joinedload(Village.block)
            .joinedload(Block.district),
        )
        .where(Contractor.village_id == village_id)
    )

    result = await db.execute(query)
    contractor = result.unique().scalar_one_or_none()
    if not contractor:
        raise HTTPException(status_code=404, detail="No contractors found for this village")
    agency = contractor.agency if contractor else None

    return ContractorResponse(
        id=contractor.id,
        agency=AgencyResponse(
            id=agency.id,
            name=agency.name,
            phone=agency.phone,
            email=agency.email,
            address=agency.address,
        )
        if agency
        else None,
        person_name=contractor.person_name,
        person_phone=contractor.person_phone,
        village_id=contractor.village_id,
        village_name=contractor.village.name if contractor.village else None,
        block_name=contractor.village.block.name
        if contractor.village and contractor.village.block
        else None,
        district_name=contractor.village.block.district.name
        if contractor.village
        and contractor.village.block
        and contractor.village.block.district
        else None,
        contract_start_date=contractor.contract_start_date,
        contract_end_date=contractor.contract_end_date,
    )
