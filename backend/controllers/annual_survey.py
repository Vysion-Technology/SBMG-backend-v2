"""
Annual Survey Controller
Handles API endpoints for annual survey management
"""

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db


from models.database.auth import User

from models.requests.survey import CreateAnnualSurveyRequest
from models.response.annual_survey import (
    AnnualSurveyResponse,
)

from services.annual_survey import AnnualSurveyService
from auth_utils import require_staff_role


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
        if survey_request.gp_id != current_user.village_id:
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
            [current_user.village_id, current_user.block_id, current_user.district_id]
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
            [current_user.village_id, current_user.block_id, current_user.district_id]
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
