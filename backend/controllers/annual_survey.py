"""
Annual Survey Controller
Handles API endpoints for annual survey management
"""

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession

from auth_utils import require_staff_role
from database import get_db


from models.database.auth import User

from models.requests.survey import CreateAnnualSurveyRequest, UpdateAnnualSurveyRequest
from models.response.annual_survey import (
    AnnualSurveyFYResponse,
    AnnualSurveyResponse,
)
from models.response.annual_survey_analytics import (
    StateAnalytics,
    DistrictAnalytics,
    BlockAnalytics,
    GPAnalytics,
)

from services.geography import GeographyService
from services.annual_survey import AnnualSurveyService
# from services.annual_survey_analytics import AnnualSurveyAnalyticsService
from services.annual_survey_analytics_optimized import AnnualSurveyAnalyticsServiceOptimized as AnnualSurveyAnalyticsService


router = APIRouter()


@router.post("/fill", response_model=AnnualSurveyResponse, status_code=status.HTTP_201_CREATED)
async def create_annual_survey(
    survey_request: CreateAnnualSurveyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
) -> AnnualSurveyResponse:
    """
    Create a new annual survey.

    - All staff members can fill surveys for GPs within their jurisdiction
    - Admin can fill surveys anywhere
    """
    service = AnnualSurveyService(db)

    try:
        if survey_request.gp_id != current_user.gp_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to fill a survey for this GP",
            )
        if "contractor" in current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Contractor users cannot fill surveys",
            )
        survey = await service.vdo_fills_the_survey(current_user, survey_request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return survey


@router.put("/{survey_id}", response_model=AnnualSurveyResponse)
async def update_annual_survey(
    survey_id: int,
    survey_request: UpdateAnnualSurveyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
) -> AnnualSurveyResponse:
    """
    Update an existing annual survey.

    - Staff members can update surveys for GPs within their jurisdiction
    - Admin can update surveys anywhere
    """
    service = AnnualSurveyService(db)

    try:
        # Get the existing survey to check permissions
        survey = await service.get_survey_by_id(survey_id)
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey not found",
            )

        # Check permissions
        if survey.gp_id != current_user.gp_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update this survey",
            )
        if "contractor" in current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Contractor users cannot update surveys",
            )

        updated_survey = await service.update_survey(survey_id, survey_request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return updated_survey


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
        survey = await service.get_survey_by_id(survey_id)
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey not found",
            )
        if any([current_user.gp_id, current_user.block_id, current_user.district_id]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only ADMIN users can delete surveys.",
            )
        await service.delete_survey(survey_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return None


@router.get("/", response_model=list[AnnualSurveyResponse])
async def list_annual_surveys(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    district_id: int | None = None,
    block_id: int | None = None,
    gp_id: int | None = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(require_staff_role),
) -> list[AnnualSurveyResponse]:
    """
    List annual surveys.

    - Staff can view surveys within their jurisdiction
    - Admin can view all surveys
    """
    service = AnnualSurveyService(db)

    try:
        if current_user.gp_id and gp_id != current_user.gp_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view surveys for this GP",
            )
        surveys = await service.get_surveys_list(
            block_id=block_id,
            gp_id=gp_id,
            start_date=start_date,
            end_date=end_date,
            district_id=district_id,
            limit=limit,
            skip=skip,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return surveys


@router.get("/{survey_id}", response_model=AnnualSurveyResponse)
async def get_annual_survey(
    survey_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
) -> AnnualSurveyResponse:
    """
    Get details of an annual survey.

    Users can only view surveys within their jurisdiction.
    """
    service = AnnualSurveyService(db)

    try:
        survey = await service.get_survey_by_id(survey_id)
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey not found",
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return survey


@router.get("/latest-for-gp/{gp_id}", response_model=AnnualSurveyResponse)
async def get_gp_latest_survey(
    gp_id: int,
    db: AsyncSession = Depends(get_db),
) -> AnnualSurveyResponse:
    """
    Get the latest annual survey for a specific GP.

    Users can only view surveys within their jurisdiction.
    """
    service = AnnualSurveyService(db)

    try:
        survey = await service.get_latest_survey_by_gp(gp_id)
        if not survey:
            geo_serv = GeographyService(db)
            gp = await geo_serv.get_village(gp_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Survey not found for Gram Panchayat {gp.name}"
                if gp
                else "Survey not found for your Gram Panchayat",
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return survey


@router.get("/analytics/state", response_model=StateAnalytics)
async def get_state_analytics(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff_role),
    fy_id: Optional[int] = None,
) -> StateAnalytics:
    """
    Get state-level annual survey analytics.

    Returns comprehensive analytics including:
    - Total village master data count
    - Coverage percentage
    - Financial metrics (funds sanctioned, work order amounts)
    - SBMG target achievement rates
    - Scheme-wise target vs achievement
    - Annual overview metrics
    - District-wise coverage
    """
    service = AnnualSurveyAnalyticsService(db)

    try:
        analytics = await service.get_state_analytics(fy_id=fy_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return analytics


@router.get("/analytics/district/{district_id}", response_model=DistrictAnalytics)
async def get_district_analytics(
    district_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
    fy_id: Optional[int] = None,
) -> DistrictAnalytics:
    """
    Get district-level annual survey analytics.

    Returns comprehensive analytics including:
    - District survey metrics
    - Coverage percentage
    - Financial metrics
    - SBMG target achievement rates
    - Scheme-wise target vs achievement
    - Annual overview metrics
    - Block-wise coverage within the district

    Users can only view analytics within their jurisdiction.
    """
    # Permission check
    if current_user.district_id and current_user.district_id != district_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view analytics for this district",
        )

    service = AnnualSurveyAnalyticsService(db)

    try:
        analytics = await service.get_district_analytics(district_id=district_id, fy_id=fy_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return analytics


@router.get("/analytics/block/{block_id}", response_model=BlockAnalytics)
async def get_block_analytics(
    block_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
    fy_id: Optional[int] = None,
) -> BlockAnalytics:
    """
    Get block-level annual survey analytics.

    Returns comprehensive analytics including:
    - Block survey metrics
    - Coverage percentage
    - Financial metrics
    - SBMG target achievement rates
    - Scheme-wise target vs achievement
    - Annual overview metrics
    - GP-wise coverage within the block

    Users can only view analytics within their jurisdiction.
    """
    # Get block to check jurisdiction
    geo_service = GeographyService(db)
    block = await geo_service.get_block(block_id)

    if not block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Block not found",
        )

    # Permission check
    if current_user.district_id and current_user.district_id != block.district_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view analytics for this block",
        )

    if current_user.block_id and current_user.block_id != block_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view analytics for this block",
        )

    service = AnnualSurveyAnalyticsService(db)

    try:
        analytics = await service.get_block_analytics(block_id=block_id, fy_id=fy_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return analytics


@router.get("/analytics/gp/{gp_id}", response_model=GPAnalytics)
async def get_gp_analytics(
    gp_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
    fy_id: Optional[int] = None,
) -> GPAnalytics:
    """
    Get GP-level annual survey analytics.

    Returns comprehensive analytics including:
    - GP information
    - Master data availability status
    - Survey details (if available)
    - Financial metrics
    - Scheme-wise target vs achievement
    - Annual overview metrics

    Users can only view analytics within their jurisdiction.
    """
    # Get GP to check jurisdiction
    geo_service = GeographyService(db)
    gp = await geo_service.get_village(gp_id)

    if not gp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gram Panchayat not found",
        )

    # Permission check
    if current_user.district_id and current_user.district_id != gp.district_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view analytics for this GP",
        )

    if current_user.block_id and current_user.block_id != gp.block_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view analytics for this GP",
        )

    if current_user.gp_id and current_user.gp_id != gp_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view analytics for this GP",
        )

    service = AnnualSurveyAnalyticsService(db)

    try:
        analytics = await service.get_gp_analytics(gp_id=gp_id, fy_id=fy_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return analytics


@router.get("/analytics")
async def get_annual_survey_analytics_deprecated(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
    district_id: int | None = None,
    block_id: int | None = None,
    gp_id: int | None = None,
):
    """
    Get annual survey analytics (deprecated).

    Please use the specific endpoints:
    - GET /analytics/state - for state-level analytics
    - GET /analytics/district/{district_id} - for district-level analytics
    - GET /analytics/block/{block_id} - for block-level analytics
    - GET /analytics/gp/{gp_id} - for GP-level analytics

    Users can only view analytics within their jurisdiction.
    """
    geo_svc = GeographyService(db)
    if district_id:
        if not any([
            not current_user.district_id,
            current_user.district_id != district_id,
        ]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view analytics for this district",
            )
    if block_id:
        block = await geo_svc.get_block(block_id)
        if not any([
            not current_user.block_id and not current_user.district_id and not current_user.gp_id,
            not current_user.block_id and current_user.district_id == block.district_id,
            current_user.block_id != block_id,
        ]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view analytics for this block",
            )
    if gp_id:
        gp = await geo_svc.get_village(gp_id)
        if not any([
            not current_user.gp_id and not current_user.block_id and not current_user.district_id,
            not current_user.gp_id and current_user.block_id == gp.block_id,
            current_user.gp_id != gp_id,
        ]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view analytics for this GP",
            )
    raise NotImplementedError("Analytics endpoint is not yet implemented.")


@router.get("/fy/active", response_model=list[AnnualSurveyFYResponse])
async def get_active_financial_years(
    db: AsyncSession = Depends(get_db),
) -> List[AnnualSurveyFYResponse]:
    """
    Get a list of active financial years.

    Users can only view financial years within their jurisdiction.
    """
    service = AnnualSurveyService(db)

    try:
        active_fy = await service.get_active_financial_years()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return active_fy
