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
from auth_utils import require_staff_role, UserRole


router = APIRouter()


@router.post(
    "/", response_model=AnnualSurveyResponse, status_code=status.HTTP_201_CREATED
)
async def create_annual_survey(
    request: CreateAnnualSurveyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
) -> AnnualSurveyResponse:
    """
    Create a new annual survey.

    - All staff members can create surveys for GPs within their jurisdiction
    - Admin can create surveys anywhere
    """
    service = AnnualSurveyService(db)

    try:
        survey = await service.create_survey(current_user, request)
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
