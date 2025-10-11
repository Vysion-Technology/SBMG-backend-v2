from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from services.geography import GeographyService
from database import get_db
from models.database.geography import District, Block, GramPanchayat
from models.response.geography import (
    DistrictResponse,
    BlockResponse,
    VillageResponse as GramPanchayatResponse,
)
from models.database.contractor import Agency, Contractor
from models.response.contractor import AgencyResponse, ContractorResponse
from services.contractor import ContractorService


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


@router.get("/villages", response_model=List[GramPanchayatResponse])
async def list_villages(
    block_id: Optional[int] = None,
    district_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List all villages with pagination (Admin only)."""
    query = select(GramPanchayat)

    if block_id:
        query = query.where(GramPanchayat.block_id == block_id)
    elif district_id:
        query = query.where(GramPanchayat.district_id == district_id)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    villages = result.scalars().all()

    return [
        GramPanchayatResponse(
            id=village.id,
            name=village.name,
            description=village.description,
            block_id=village.block_id,
            district_id=village.district_id,
        )
        for village in villages
    ]


@router.get("/villages/{village_id}", response_model=GramPanchayatResponse)
async def get_village(
    village_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific village by ID (Admin only)."""
    result = await db.execute(
        select(GramPanchayat).where(GramPanchayat.id == village_id)
    )
    village = result.scalar_one_or_none()

    if not village:
        raise HTTPException(status_code=404, detail="GramPanchayat not found")

    return GramPanchayatResponse(
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
    geo_service = GeographyService(db)
    # First check if village exists
    village = await geo_service.get_village(village_id)

    if not village:
        raise HTTPException(status_code=404, detail="GramPanchayat not found")

    # Get contractors for this village with related data
    query = select(Contractor).where(Contractor.village_id == village_id)

    result = await db.execute(query)
    contractor = result.unique().scalar_one_or_none()
    if not contractor:
        raise HTTPException(
            status_code=404, detail="No contractors found for this village"
        )
    agency: Agency = (
        await db.execute(select(Agency).where(Agency.id == contractor.agency_id))
    ).scalar_one()
    contractor_service: ContractorService = ContractorService(db)

    # agency, village = await asyncio.gather(
    #     contractor_service.get_agency_by_id(contractor.agency_id),
    #     geo_service.get_village(village_id)
    # )
    agency = await contractor_service.get_agency_by_id(contractor.agency_id)
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
        village_name=village.name if village else None,
        block_name=village.block.name if village and village.block else None,
        district_name=village.block.district.name
        if village and village.block
        else None,
        contract_start_date=contractor.contract_start_date,
        contract_end_date=contractor.contract_end_date,
    )
