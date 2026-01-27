"""Geography Controller."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.database.geography import District, Block, GramPanchayat, Village
from models.database.auth import User
from models.response.geography import (
    DistrictResponse,
    BlockResponse,
    GPResponse,
    VillageResponse,
)
from models.requests.geography import CreateVillageRequest
from models.database.contractor import Agency, Contractor
from models.response.contractor import AgencyResponse, ContractorResponse

from services.geography import GeographyService
from services.contractor import ContractorService
from services.permission import PermissionService
from controllers.auth import get_current_user


router = APIRouter()


# List endpoints with pagination
@router.get("/districts", response_model=List[DistrictResponse])
async def list_districts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List all districts with pagination."""
    result = await db.execute(select(District).offset(skip).limit(limit))
    districts = result.scalars().all()

    return [
        DistrictResponse(
            id=district.id,
            name=district.name,
            description=district.description,
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
    """List all blocks with pagination."""
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


@router.get("/grampanchayats", response_model=List[GPResponse])
async def list_grampanchayats(
    block_id: Optional[int] = None,
    district_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List all Gram Panchayats with pagination."""
    query = select(GramPanchayat)

    if block_id:
        query = query.where(GramPanchayat.block_id == block_id)
    elif district_id:
        query = query.where(GramPanchayat.district_id == district_id)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    villages = result.scalars().all()

    return [
        GPResponse(
            id=village.id,
            name=village.name,
            description=village.description,
            block_id=village.block_id,
            district_id=village.district_id,
        )
        for village in villages
    ]


@router.get("/grampanchayats/{village_id}", response_model=GPResponse)
async def get_grampanchayat(
    village_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific grampanchayat by ID."""
    result = await db.execute(select(GramPanchayat).where(GramPanchayat.id == village_id))
    village = result.scalar_one_or_none()

    if not village:
        raise HTTPException(status_code=404, detail="GramPanchayat not found")

    return GPResponse(
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
    """Get a specific block by ID."""
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

    return DistrictResponse(id=district.id, name=district.name, description=district.description)


@router.get("/grampanchayats/{village_id}/contractor", response_model=ContractorResponse)
async def get_contractors_by_gp(
    village_id: int,
    db: AsyncSession = Depends(get_db),
) -> ContractorResponse:
    """Get all contractors for a specific Gram Panchayat."""
    geo_service = GeographyService(db)
    # First check if village exists
    village = await geo_service.get_village(village_id)

    if not village:
        raise HTTPException(status_code=404, detail="GramPanchayat not found")

    # Get contractors for this GP using ContractorService
    # Note: Returns the first contractor for the GP (typically only one per GP)
    contractor_service = ContractorService(db)
    contractors = await contractor_service.list_contractors(gp_id=village_id, limit=1)
    
    if not contractors:
        raise HTTPException(status_code=404, detail="No contractors found for this village")
    
    # Return the first (and typically only) contractor for this GP
    return contractors[0]


# Village endpoints
@router.get("/villages", response_model=List[VillageResponse])
async def list_villages(
    gp_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> List[VillageResponse]:
    """List all villages with pagination, optionally filtered by Gram Panchayat."""
    query = select(Village)

    if gp_id:
        query = query.where(Village.gp_id == gp_id)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    villages = result.scalars().all()

    return [
        VillageResponse(
            id=village.id,
            name=village.name,
            description=village.description,
            gp_id=village.gp_id,
        )
        for village in villages
    ]


@router.get("/villages/{village_id}", response_model=VillageResponse)
async def get_village(
    village_id: int,
    db: AsyncSession = Depends(get_db),
) -> VillageResponse:
    """Get a specific village by ID."""
    result = await db.execute(select(Village).where(Village.id == village_id))
    village = result.scalar_one_or_none()

    if not village:
        raise HTTPException(status_code=404, detail="Village not found")

    return VillageResponse(
        id=village.id,
        name=village.name,
        description=village.description,
        gp_id=village.gp_id,
    )


@router.post("/villages", response_model=VillageResponse)
async def create_village(
    village_data: CreateVillageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VillageResponse:
    """Create a new village (VDO only)."""
    # Check if user is VDO
    permission_service = PermissionService(db)
    if not permission_service.is_vdo(current_user):
        raise HTTPException(
            status_code=403,
            detail="Only VDOs can create villages",
        )

    # Check if VDO is creating village in their own GP
    if current_user.gp_id != village_data.gp_id:
        raise HTTPException(
            status_code=403,
            detail="VDOs can only create villages within their own Gram Panchayat",
        )

    # Create the village
    geo_service = GeographyService(db)
    try:
        new_village = await geo_service.create_village(village_data)
        return VillageResponse(
            id=new_village.id,
            name=new_village.name,
            description=new_village.description,
            gp_id=new_village.gp_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating village: {str(e)}") from e

