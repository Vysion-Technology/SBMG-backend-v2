"""
Annual Survey Controller
Handles API endpoints for annual survey management
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import get_db

from controllers.user_management import PositionHolderResponse

from models.database.auth import User, PositionHolder
from models.database.geography import GramPanchayat
from models.database.survey_master import (
    AnnualSurvey,
    VillageSBMGAssets,
    VillageGWMAssets,
)

from models.requests.survey import CreateAnnualSurveyRequest, UpdateAnnualSurveyRequest
from models.response.annual_survey import (
    AnnualSurveyResponse,
    AnnualSurveyListItemResponse,
    PaginatedAnnualSurveyResponse,
    AnnualSurveyStatsResponse,
    WorkOrderDetailsResponse,
    FundSanctionedResponse,
    DoorToDoorCollectionResponse,
    RoadSweepingDetailsResponse,
    DrainCleaningDetailsResponse,
    CSCDetailsResponse,
    SWMAssetsResponse,
    SBMGYearTargetsResponse,
    VillageDataResponse,
    VillageSBMGAssetsResponse,
    VillageGWMAssetsResponse,
)

from services.annual_survey import AnnualSurveyService
from services.auth import AuthService
from auth_utils import require_staff_role, UserRole


router = APIRouter()


@router.get("/", response_model=PaginatedAnnualSurveyResponse)
async def get_annual_surveys(
    limit: int = 20,
    skip: int = 0,
    gp_id: Optional[int] = None,
    block_id: Optional[int] = None,
    district_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """
    Get paginated list of annual surveys within user's jurisdiction.

    Filters:
    - gp_id: Filter by specific Gram Panchayat
    - block_id: Filter by specific block
    - district_id: Filter by specific district
    - start_date: Filter surveys from this date onwards
    - end_date: Filter surveys up to this date
    """
    if limit <= 0 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100",
        )

    if skip < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skip must be a non-negative integer",
        )

    service = AnnualSurveyService(db)

    surveys, total = await service.get_surveys_list(
        gp_id=gp_id,
        block_id=block_id,
        district_id=district_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )

    # Build response items
    survey_items: List[AnnualSurveyListItemResponse] = []
    for survey in surveys:
        # Get position holder
        pos_result = await db.execute(
            select(PositionHolder)
            .options(
                selectinload(PositionHolder.role),
                selectinload(PositionHolder.user),
            )
            .where(PositionHolder.id == survey.vdo_id)
        )
        position = pos_result.scalar_one_or_none()

        surveyor_name = (
            f"{position.first_name} {position.last_name}" if position else "Unknown"
        )
        surveyor_role = position.role.name if position and position.role else "Unknown"

        # Count villages
        num_villages = len(survey.village_data) if survey.village_data else 0

        survey_items.append(
            AnnualSurveyListItemResponse(
                id=survey.id,
                gp_id=survey.gp_id,
                gp_name=survey.gp.name if survey.gp else "Unknown",
                block_name=survey.gp.block.name
                if survey.gp and survey.gp.block
                else "Unknown",
                district_name=survey.gp.district.name
                if survey.gp and survey.gp.district
                else "Unknown",
                survey_date=survey.survey_date,
                surveyor_name=surveyor_name,
                surveyor_role=surveyor_role,
                num_villages=num_villages,
            )
        )

    total_pages = (total + limit - 1) // limit

    return PaginatedAnnualSurveyResponse(
        items=survey_items,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        total_pages=total_pages,
    )


@router.post(
    "/", response_model=AnnualSurveyResponse, status_code=status.HTTP_201_CREATED
)
async def create_annual_survey(
    request: CreateAnnualSurveyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """
    Create a new annual survey.

    - All staff members can create surveys for GPs within their jurisdiction
    - Admin can create surveys anywhere
    """
    service = AnnualSurveyService(db)

    try:
        survey = await service.create_survey(current_user, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Load the survey with all details to return
    survey_detail = await get_survey_detail(survey.id, db)

    return survey_detail


@router.get("/{survey_id}", response_model=AnnualSurveyResponse)
async def get_annual_survey(
    survey_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """
    Get detailed information about a specific annual survey.

    Users can only view surveys within their jurisdiction.
    """
    survey_detail = await get_survey_detail(survey_id, db)

    if not survey_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found"
        )

    # Check if user has access to this survey
    service = AnnualSurveyService(db)

    # If not admin, check jurisdiction
    user_roles = [pos.role.name for pos in current_user.positions if pos.role]
    if UserRole.ADMIN not in user_roles and UserRole.SUPERADMIN not in user_roles:
        # Verify the survey is within jurisdiction
        result = await db.execute(
            select(AnnualSurvey).where(AnnualSurvey.id == survey_id)
        )
        survey = result.scalar_one_or_none()

        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found"
            )

        # Check jurisdiction
        can_access = await service.can_survey_gp(current_user, survey.gp_id)
        if not can_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this survey",
            )

    return survey_detail


@router.put("/{survey_id}", response_model=AnnualSurveyResponse)
async def update_annual_survey(
    survey_id: int,
    request: UpdateAnnualSurveyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """
    Update an existing annual survey.

    Users can only update surveys within their jurisdiction.
    """
    service = AnnualSurveyService(db)

    try:
        survey = await service.update_survey(survey_id, current_user, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Load the survey with all details to return
    survey_detail = await get_survey_detail(survey.id, db)

    return survey_detail


@router.delete("/{survey_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_annual_survey(
    survey_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """
    Delete an annual survey.

    Users can only delete surveys within their jurisdiction.
    """
    service = AnnualSurveyService(db)

    try:
        await service.delete_survey(survey_id, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return None


@router.get("/stats/summary", response_model=AnnualSurveyStatsResponse)
async def get_annual_survey_stats(
    district_id: Optional[int] = None,
    block_id: Optional[int] = None,
    gp_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """
    Get annual survey statistics for the user's jurisdiction.
    """
    service = AnnualSurveyService(db)
    stats = await service.get_survey_statistics(
        user=current_user,
        district_id=district_id,
        block_id=block_id,
        gp_id=gp_id,
        start_date=start_date,
        end_date=end_date,
    )

    return AnnualSurveyStatsResponse(**stats)


# Helper function to get survey details
async def get_survey_detail(
    survey_id: int, db: AsyncSession
) -> Optional[AnnualSurveyResponse]:
    """Get full annual survey details with all related data."""
    # Get survey with relationships
    result = await db.execute(
        select(AnnualSurvey)
        .options(
            selectinload(AnnualSurvey.gp).selectinload(GramPanchayat.block),
            selectinload(AnnualSurvey.gp).selectinload(GramPanchayat.district),
            selectinload(AnnualSurvey.work_order),
            selectinload(AnnualSurvey.fund_sanctioned),
            selectinload(AnnualSurvey.door_to_door_collection),
            selectinload(AnnualSurvey.road_sweeping),
            selectinload(AnnualSurvey.drain_cleaning),
            selectinload(AnnualSurvey.csc_details),
            selectinload(AnnualSurvey.swm_assets),
            selectinload(AnnualSurvey.sbmg_targets),
            selectinload(AnnualSurvey.village_data),
        )
        .where(AnnualSurvey.id == survey_id)
    )
    survey = result.scalar_one_or_none()

    if not survey:
        return None

    # Get position holder details
    pos_result = await db.execute(
        select(PositionHolder)
        .options(
            selectinload(PositionHolder.role),
            selectinload(PositionHolder.user),
        )
        .where(PositionHolder.id == survey.vdo_id)
    )
    position = pos_result.scalar_one_or_none()

    if not position:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Survey position holder not found",
        )

    surveyor_name = (
        f"{position.first_name} {position.last_name}" if position else "Unknown"
    )
    surveyor_role = position.role.name if position and position.role else "Unknown"

    # Get village data with assets
    village_data_list: List[VillageDataResponse] = []
    if survey.village_data:
        for village in survey.village_data:
            # Get SBMG assets
            sbmg_result = await db.execute(
                select(VillageSBMGAssets).where(VillageSBMGAssets.id == village.id)
            )
            sbmg_assets = sbmg_result.scalar_one_or_none()

            # Get GWM assets
            gwm_result = await db.execute(
                select(VillageGWMAssets).where(VillageGWMAssets.id == village.id)
            )
            gwm_assets = gwm_result.scalar_one_or_none()

            village_data_list.append(
                VillageDataResponse(
                    id=village.id,
                    survey_id=village.survey_id,
                    village_name=village.village_name,
                    population=village.population,
                    num_households=village.num_households,
                    sbmg_assets=VillageSBMGAssetsResponse.model_validate(sbmg_assets)
                    if sbmg_assets
                    else None,
                    gwm_assets=VillageGWMAssetsResponse.model_validate(gwm_assets)
                    if gwm_assets
                    else None,
                )
            )

    # Build response
    return AnnualSurveyResponse(
        id=survey.id,
        gp_id=survey.gp_id,
        survey_date=survey.survey_date,
        surveyed_by_id=survey.vdo_id,
        surveyor_name=surveyor_name,
        surveyor_role=surveyor_role,
        gp_name=survey.gp.name if survey.gp else "Unknown",
        block_name=survey.gp.block.name if survey.gp and survey.gp.block else "Unknown",
        district_name=survey.gp.district.name
        if survey.gp and survey.gp.district
        else "Unknown",
        vdo=PositionHolderResponse.model_validate(position),
        vdo_id=survey.vdo_id,
        sarpanch_name=survey.sarpanch_name or "",
        sarpanch_contact=survey.sarpanch_contact or "",
        num_ward_panchs=survey.num_ward_panchs or 0,
        agency_id=survey.agency_id,
        work_order=WorkOrderDetailsResponse.model_validate(survey.work_order)
        if survey.work_order
        else None,
        fund_sanctioned=FundSanctionedResponse.model_validate(survey.fund_sanctioned)
        if survey.fund_sanctioned
        else None,
        door_to_door_collection=DoorToDoorCollectionResponse.model_validate(
            survey.door_to_door_collection
        )
        if survey.door_to_door_collection
        else None,
        road_sweeping=RoadSweepingDetailsResponse.model_validate(survey.road_sweeping)
        if survey.road_sweeping
        else None,
        drain_cleaning=DrainCleaningDetailsResponse.model_validate(
            survey.drain_cleaning
        )
        if survey.drain_cleaning
        else None,
        csc_details=CSCDetailsResponse.model_validate(survey.csc_details)
        if survey.csc_details
        else None,
        swm_assets=SWMAssetsResponse.model_validate(survey.swm_assets)
        if survey.swm_assets
        else None,
        sbmg_targets=SBMGYearTargetsResponse.model_validate(survey.sbmg_targets)
        if survey.sbmg_targets
        else None,
        village_data=village_data_list,
        created_at=survey.created_at,
        updated_at=survey.updated_at,
    )
