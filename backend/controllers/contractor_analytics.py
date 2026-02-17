"""
Contractor Analytics Controller
Handles API endpoints for contractor coverage analytics at state, district, block, and GP levels
"""

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession

from auth_utils import require_staff_role
from database import get_db

from models.database.auth import User
from models.response.contractor_analytics import (
    ContractorStateAnalytics,
    ContractorDistrictAnalytics,
    ContractorBlockAnalytics,
    ContractorGPAnalytics,
)

from services.geography import GeographyService
from services.contractor_analytics import ContractorAnalyticsService

router = APIRouter()


@router.get("/analytics/state", response_model=ContractorStateAnalytics)
async def get_contractor_state_analytics(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff_role),
) -> ContractorStateAnalytics:
    """
    Get state-level contractor analytics.

    Returns:
    - Total GP master data count
    - GPs with contractor data filled
    - Coverage percentage
    - Total contractors
    - Total contract amount
    - District-wise coverage breakdown
    """
    service = ContractorAnalyticsService(db)

    try:
        analytics = await service.get_state_analytics()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return analytics


@router.get("/analytics/district/{district_id}", response_model=ContractorDistrictAnalytics)
async def get_contractor_district_analytics(
    district_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
) -> ContractorDistrictAnalytics:
    """
    Get district-level contractor analytics.

    Returns:
    - District contractor metrics
    - Coverage percentage
    - Total contractors and contract amount
    - Block-wise coverage breakdown

    Users can only view analytics within their jurisdiction.
    """
    # Permission check
    if current_user.district_id and current_user.district_id != district_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view analytics for this district",
        )

    service = ContractorAnalyticsService(db)

    try:
        analytics = await service.get_district_analytics(district_id=district_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return analytics


@router.get("/analytics/block/{block_id}", response_model=ContractorBlockAnalytics)
async def get_contractor_block_analytics(
    block_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
) -> ContractorBlockAnalytics:
    """
    Get block-level contractor analytics.

    Returns:
    - Block contractor metrics
    - Coverage percentage
    - Total contractors and contract amount
    - GP-wise coverage breakdown

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

    service = ContractorAnalyticsService(db)

    try:
        analytics = await service.get_block_analytics(block_id=block_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return analytics


@router.get("/analytics/gp/{gp_id}", response_model=ContractorGPAnalytics)
async def get_contractor_gp_analytics(
    gp_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
) -> ContractorGPAnalytics:
    """
    Get GP-level contractor analytics.

    Returns:
    - GP information
    - Contractor data availability status
    - Total contractors and contract amount
    - Detailed contractor list with agency info

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

    service = ContractorAnalyticsService(db)

    try:
        analytics = await service.get_gp_analytics(gp_id=gp_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return analytics
