"""
Annual Survey Controller
Handles API endpoints for annual survey management
"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession

from auth_utils import require_staff_role
from database import get_db


from models.database.auth import User

from models.requests.survey import CreateAnnualSurveyRequest
from models.response.annual_survey import (
    AnnualSurveyResponse,
)

from services.geography import GeographyService
from services.annual_survey import AnnualSurveyService



router = APIRouter()


@router.post(
    "/fill", response_model=AnnualSurveyResponse, status_code=status.HTTP_201_CREATED
)
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
        survey = await service.create_survey(current_user, survey_request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

    return survey


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
        if any(
            [current_user.gp_id, current_user.block_id, current_user.district_id]
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only ADMIN users can delete surveys.",
            )
        await service.delete_survey(survey_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

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
        if any(
            [current_user.gp_id, current_user.block_id, current_user.district_id]
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only ADMIN users can view surveys.",
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

    return survey


@router.get("analytics")
async def get_annual_survey_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
    district_id: int | None = None,
    block_id: int | None = None,
    gp_id: int | None = None,
):
    """
    Get annual survey analytics.

    Users can only view analytics within their jurisdiction.
    """
    geo_svc = GeographyService(db)
    if district_id:
        if not any(
            [
                not current_user.district_id,
                current_user.district_id != district_id,
            ]
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view analytics for this district",
            )
    if block_id:
        block = await geo_svc.get_block(block_id)
        if not any(
            [
                not current_user.block_id
                and not current_user.district_id
                and not current_user.gp_id,
                not current_user.block_id
                and current_user.district_id == block.district_id,
                current_user.block_id != block_id,
            ]
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view analytics for this block",
            )
    if gp_id:
        gp = await geo_svc.get_village(gp_id)
        if not any(
            [
                not current_user.gp_id
                and not current_user.block_id
                and not current_user.district_id,
                not current_user.gp_id and current_user.block_id == gp.block_id,
                current_user.gp_id != gp_id,
            ]
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view analytics for this GP",
            )
    raise NotImplementedError("Analytics endpoint is not yet implemented.")
