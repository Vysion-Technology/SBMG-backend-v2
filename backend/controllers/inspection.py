"""
Inspection Controller
Handles API endpoints for inspection management
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth_utils import UserRole, require_staff_role
from database import get_db
from models.database.auth import PositionHolder, User
from models.database.geography import GramPanchayat
from models.database.inspection import (
    CommunitySanitationInspectionItem,
    HouseHoldWasteCollectionAndDisposalInspectionItem,
    Inspection,
    OtherInspectionItem,
    RoadAndDrainCleaningInspectionItem,
)
from models.internal import GeoTypeEnum
from models.requests.inspection import CreateInspectionRequest
from models.response.inspection import (
    CommunitySanitationResponse,
    HouseHoldWasteCollectionResponse,
    InspectionAnalyticsResponse,
    InspectionListItemResponse,
    InspectionResponse,
    OtherInspectionItemsResponse,
    PaginatedInspectionResponse,
    RoadAndDrainCleaningResponse,
)
from services.inspection import InspectionService

router = APIRouter()


@router.post(
    "/", response_model=InspectionResponse, status_code=status.HTTP_201_CREATED
)
async def create_inspection(
    request: CreateInspectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """
    Create a new inspection.

    - Officers (CEO, BDO, WORKER) can create inspections in villages within their jurisdiction
    - VDO cannot create inspections
    - Admin can create inspections anywhere
    """
    # Check if user is VDO (not allowed to inspect)
    user_roles = [pos.role.name for pos in current_user.positions if pos.role]
    if UserRole.VDO in user_roles and len(user_roles) == 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="VDO cannot create inspections",
        )

    service = InspectionService(db)

    try:
        inspection = await service.create_inspection(current_user, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    # Load the inspection with all details to return
    inspection_detail = await get_inspection_detail(inspection.id, db)

    return inspection_detail


@router.get("/analytics", response_model=InspectionAnalyticsResponse)
async def get_inspection_analytics(
    district_id: Optional[int] = None,
    block_id: Optional[int] = None,
    gp_id: Optional[int] = None,
    level: GeoTypeEnum = GeoTypeEnum.DISTRICT,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
) -> InspectionAnalyticsResponse:
    """
    Get inspection analytics aggregated by geographic level.
    Returns inspection statistics for each geographic unit at the specified level.

    level: The geographic level to aggregate data at (district, block, gp)
    """
    # Permission checks based on user's jurisdiction
    if current_user.block_id is not None and level == GeoTypeEnum.DISTRICT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access district-level analytics",
        )
    if current_user.gp_id is not None and level in [
        GeoTypeEnum.DISTRICT,
        GeoTypeEnum.BLOCK,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access district or block-level analytics",
        )

    # Validate query parameters
    if (district_id and block_id) or (district_id and gp_id) or (block_id and gp_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide only one of district_id, block_id, or gp_id",
        )
    if level == GeoTypeEnum.DISTRICT and (district_id or block_id or gp_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Do not provide specific IDs when level is DISTRICT",
        )
    if level == GeoTypeEnum.BLOCK and (block_id or gp_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Do not provide block_id or gp_id when level is BLOCK",
        )

    inspection_service = InspectionService(db)
    result = await inspection_service.inspection_analytics(
        district_id=district_id,
        block_id=block_id,
        gp_id=gp_id,
        level=level,
        start_date=start_date,
        end_date=end_date,
    )

    return InspectionAnalyticsResponse(**result)


@router.get("/{inspection_id}", response_model=InspectionResponse)
async def get_inspection(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """
    Get detailed information about a specific inspection.

    Officers can only view inspections within their jurisdiction.
    """
    inspection_detail = await get_inspection_detail(inspection_id, db)

    if not inspection_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found"
        )

    # Check if user has access to this inspection
    service = InspectionService(db)

    # If not admin, check jurisdiction
    user_roles = [pos.role.name for pos in current_user.positions if pos.role]
    if UserRole.ADMIN not in user_roles and UserRole.SUPERADMIN not in user_roles:
        # Verify the inspection is within jurisdiction
        result = await db.execute(
            select(Inspection).where(Inspection.id == inspection_id)
        )
        inspection = result.scalar_one_or_none()

        if not inspection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found"
            )

        # Check jurisdiction
        can_access = await service.can_inspect_village(
            current_user, inspection.gp_id
        )
        if not can_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this inspection",
            )

    return inspection_detail


@router.get("/", response_model=PaginatedInspectionResponse)
async def get_inspections(
    page: int = 1,
    page_size: int = 20,
    village_id: Optional[int] = None,
    block_id: Optional[int] = None,
    district_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """
    Get paginated list of inspections within user's jurisdiction.

    Filters:
    - village_id: Filter by specific village
    - block_id: Filter by specific block
    - district_id: Filter by specific district
    - start_date: Filter inspections from this date onwards
    - end_date: Filter inspections up to this date
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be greater than 0",
        )

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be between 1 and 100",
        )

    if current_user.gp_id and (block_id or district_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Block or District filter not allowed for Village-level users",
        )

    if current_user.block_id and district_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="District filter not allowed for Block-level users",
        )

    service = InspectionService(db)

    inspections = await service.get_inspections(
        page=page,
        page_size=page_size,
        village_id=village_id,
        block_id=block_id,
        district_id=district_id,
        start_date=start_date,
        end_date=end_date,
    )
    total = await service.get_total_count(
        village_id=village_id,
        block_id=block_id,
        district_id=district_id,
        start_date=start_date,
        end_date=end_date,
    )

    # Load position holder details for each inspection
    inspection_items: List[InspectionListItemResponse] = []
    for inspection in inspections:
        # Get position holder
        pos_result = await db.execute(
            select(PositionHolder)
            .options(
                selectinload(PositionHolder.role),
                selectinload(PositionHolder.user),
            )
            .where(PositionHolder.id == inspection.position_holder_id)
        )
        position = pos_result.scalar_one_or_none()

        officer_name = (
            f"{position.first_name} {position.last_name}" if position else "Unknown"
        )
        officer_role = position.role.name if position and position.role else "Unknown"

        inspection_items.append(
            InspectionListItemResponse(
                id=inspection.id,
                village_id=inspection.gp_id,
                village_name=inspection.gp.name
                if inspection.gp
                else "Unknown",
                block_name=inspection.gp.block.name
                if inspection.gp and inspection.gp.block
                else "Unknown",
                district_name=inspection.gp.district.name
                if inspection.gp and inspection.gp.district
                else "Unknown",
                date=inspection.date,
                officer_name=officer_name,
                officer_role=officer_role,
                remarks=inspection.remarks,
            )
        )

    total_pages = (total + page_size - 1) // page_size

    return PaginatedInspectionResponse(
        items=inspection_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )



# Helper function to get inspection details
async def get_inspection_detail(
    inspection_id: int, db: AsyncSession
) -> Optional[InspectionResponse]:
    """Get full inspection details with all related data."""
    # Get inspection with relationships
    result = await db.execute(
        select(Inspection)
        .options(
            selectinload(Inspection.gp).selectinload(GramPanchayat.block),
            selectinload(Inspection.gp).selectinload(GramPanchayat.district),
            selectinload(Inspection.media),
        )
        .where(Inspection.id == inspection_id)
    )
    inspection = result.scalar_one_or_none()

    if not inspection:
        return None

    # Get position holder details
    pos_result = await db.execute(
        select(PositionHolder)
        .options(
            selectinload(PositionHolder.role),
            selectinload(PositionHolder.user),
        )
        .where(PositionHolder.id == inspection.position_holder_id)
    )
    position = pos_result.scalar_one_or_none()

    officer_name = (
        f"{position.first_name} {position.last_name}" if position else "Unknown"
    )
    officer_role = position.role.name if position and position.role else "Unknown"

    # Get household waste items
    household_result = await db.execute(
        select(HouseHoldWasteCollectionAndDisposalInspectionItem).where(
            HouseHoldWasteCollectionAndDisposalInspectionItem.id == inspection.id
        )
    )
    household = household_result.scalar_one_or_none()

    # Get road and drain items
    road_result = await db.execute(
        select(RoadAndDrainCleaningInspectionItem).where(
            RoadAndDrainCleaningInspectionItem.id == inspection.id
        )
    )
    road = road_result.scalar_one_or_none()

    # Get community sanitation items
    community_result = await db.execute(
        select(CommunitySanitationInspectionItem).where(
            CommunitySanitationInspectionItem.id == inspection.id
        )
    )
    community = community_result.scalar_one_or_none()

    # Get other items
    other_result = await db.execute(
        select(OtherInspectionItem).where(OtherInspectionItem.id == inspection.id)
    )
    other = other_result.scalar_one_or_none()

    # Build response
    return InspectionResponse(
        id=inspection.id,
        remarks=inspection.remarks,
        position_holder_id=inspection.position_holder_id,
        village_id=inspection.gp_id,
        date=inspection.date,
        start_time=inspection.start_time,
        lat=inspection.lat,
        long=inspection.long,
        register_maintenance=inspection.register_maintenance,
        officer_name=officer_name,
        officer_role=officer_role,
        village_name=inspection.gp.name if inspection.gp else "Unknown",
        block_name=inspection.gp.block.name
        if inspection.gp and inspection.gp.block
        else "Unknown",
        district_name=inspection.gp.district.name
        if inspection.gp and inspection.gp.district
        else "Unknown",
        household_waste=HouseHoldWasteCollectionResponse.model_validate(household)
        if household
        else None,
        road_and_drain=RoadAndDrainCleaningResponse.model_validate(road)
        if road
        else None,
        community_sanitation=CommunitySanitationResponse.model_validate(community)
        if community
        else None,
        other_items=OtherInspectionItemsResponse.model_validate(other)
        if other
        else None,
    )
