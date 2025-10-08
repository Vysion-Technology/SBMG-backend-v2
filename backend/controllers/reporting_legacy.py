from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from database import get_db
from models.database.auth import User
from models.database.complaint import (
    Complaint,
    ComplaintStatus,
    ComplaintAssignment,
    ComplaintMedia,
)
from models.database.geography import GramPanchayat, Block, District
from controllers.auth import get_current_active_user
from auth_utils import require_staff_role, UserRole, PermissionChecker

router = APIRouter()


# Response models
class AssignedComplaintResponse(BaseModel):
    id: int
    description: str
    status_name: str
    village_name: str
    block_name: str
    district_name: str
    created_at: datetime
    updated_at: Optional[datetime]
    media_urls: List[str] = []


class ComplaintListResponse(BaseModel):
    id: int
    description: str
    status_name: str
    village_name: str
    block_name: str
    district_name: str
    created_at: datetime
    updated_at: Optional[datetime]
    assigned_worker: Optional[str] = None


class MediaUploadResponse(BaseModel):
    id: int
    complaint_id: int
    media_url: str
    uploaded_at: datetime


class ComplaintStatusResponse(BaseModel):
    id: int
    description: str
    status_name: str
    village_name: str
    created_at: datetime


# Worker endpoints
@router.get(
    "/worker/assigned-complaints", response_model=List[AssignedComplaintResponse]
)
async def get_worker_assigned_complaints(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(require_staff_role)
):
    """Get complaints assigned to the current worker."""
    # Check if user is a worker
    if not PermissionChecker.user_has_role(
        current_user,
        [UserRole.WORKER, UserRole.VDO, UserRole.BDO, UserRole.CEO, UserRole.ADMIN],
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workers can access assigned complaints",
        )

    # Get assigned complaints
    if current_user.positions and any(
        pos.role.name == UserRole.WORKER for pos in current_user.positions
    ):
        result = await db.execute(
            select(Complaint)
            .join(ComplaintAssignment)
            .join(ComplaintStatus)
            .options(
                selectinload(Complaint.village),
                selectinload(Complaint.block),
                selectinload(Complaint.district),
                selectinload(Complaint.status),
                selectinload(Complaint.media),
            )
            .where(ComplaintAssignment.user_id == current_user.id)
        )
        complaints = result.scalars().all()
    elif current_user.positions and any(
        pos.role.name == UserRole.VDO for pos in current_user.positions
    ):
        # VDOs can see all complaints in their village
        vdo_villages = [
            pos.village_id
            for pos in current_user.positions
            if pos.role.name == UserRole.VDO and pos.village_id
        ]
        if not vdo_villages:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="VDO position not properly configured",
            )

        result = await db.execute(
            select(Complaint)
            .options(
                selectinload(Complaint.village),
                selectinload(Complaint.block),
                selectinload(Complaint.district),
                selectinload(Complaint.status),
                selectinload(Complaint.media),
            )
            .where(Complaint.village_id.in_(vdo_villages))
        )
        complaints = result.scalars().all()
    elif current_user.positions and any(
        pos.role.name == UserRole.BDO for pos in current_user.positions
    ):
        # BDOs can see all complaints in their block
        bdo_blocks = [
            pos.block_id
            for pos in current_user.positions
            if pos.role.name == UserRole.BDO and pos.block_id
        ]
        if not bdo_blocks:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="BDO position not properly configured",
            )

        result = await db.execute(
            select(Complaint)
            .options(
                selectinload(Complaint.village),
                selectinload(Complaint.block),
                selectinload(Complaint.district),
                selectinload(Complaint.status),
                selectinload(Complaint.media),
            )
            .where(Complaint.block_id.in_(bdo_blocks))
        )
        complaints = result.scalars().all()
    elif current_user.positions and any(
        pos.role.name == UserRole.CEO for pos in current_user.positions
    ):
        # CEOs can see all complaints in their district
        ceo_districts = [
            pos.district_id
            for pos in current_user.positions
            if pos.role.name == UserRole.CEO and pos.district_id
        ]
        if not ceo_districts:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CEO position not properly configured",
            )

        result = await db.execute(
            select(Complaint)
            .options(
                selectinload(Complaint.village),
                selectinload(Complaint.block),
                selectinload(Complaint.district),
                selectinload(Complaint.status),
                selectinload(Complaint.media),
            )
            .where(Complaint.district_id.in_(ceo_districts))
        )
        complaints = result.scalars().all()
    elif current_user.positions and any(
        pos.role.name == UserRole.ADMIN for pos in current_user.positions
    ):
        # Admins can see all complaints
        result = await db.execute(
            select(Complaint).options(
                selectinload(Complaint.village),
                selectinload(Complaint.block),
                selectinload(Complaint.district),
                selectinload(Complaint.status),
                selectinload(Complaint.media),
            )
        )
        complaints = result.scalars().all()
    else:
        complaints = []

    return [
        AssignedComplaintResponse(
            id=complaint.id,
            description=complaint.description,
            status_name=complaint.status.name,
            village_name=complaint.village.name,
            block_name=complaint.block.name,
            district_name=complaint.district.name,
            created_at=complaint.created_at,
            updated_at=complaint.updated_at,
            media_urls=[media.media_url for media in complaint.media],
        )
        for complaint in complaints
    ]


@router.post(
    "/worker/complaints/{complaint_id}/media", response_model=MediaUploadResponse
)
async def upload_complaint_media(
    complaint_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """Upload before/after images for a complaint assigned to the worker."""
    # Check if user is a worker
    if not PermissionChecker.user_has_role(current_user, [UserRole.WORKER]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workers can upload media",
        )

    # Verify complaint exists and is assigned to the worker
    result = await db.execute(
        select(Complaint)
        .join(ComplaintAssignment)
        .where(
            and_(
                Complaint.id == complaint_id,
                ComplaintAssignment.user_id == current_user.id,
            )
        )
    )
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found or not assigned to you",
        )

    # For now, store a placeholder URL since we don't have actual file storage configured
    # In production, this would upload to MinIO/S3 and return the actual URL
    media_url = f"/media/complaints/{complaint_id}/{file.filename}"

    # Create media record
    media = ComplaintMedia(complaint_id=complaint_id, media_url=media_url)

    db.add(media)
    await db.commit()
    await db.refresh(media)

    return MediaUploadResponse(
        id=media.id,
        complaint_id=media.complaint_id,
        media_url=media.media_url,
        uploaded_at=media.uploaded_at,
    )


@router.patch("/worker/complaints/{complaint_id}/mark-done")
async def mark_complaint_done(
    complaint_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """Mark a complaint as completed by the worker."""
    # Check if user is a worker
    if not PermissionChecker.user_has_role(current_user, [UserRole.WORKER]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workers can mark complaints as done",
        )

    # Verify complaint exists and is assigned to the worker
    result = await db.execute(
        select(Complaint)
        .join(ComplaintAssignment)
        .where(
            and_(
                Complaint.id == complaint_id,
                ComplaintAssignment.user_id == current_user.id,
            )
        )
    )
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found or not assigned to you",
        )

    # Get "COMPLETED" status
    status_result = await db.execute(
        select(ComplaintStatus).where(ComplaintStatus.name == "COMPLETED")
    )
    completed_status = status_result.scalar_one_or_none()

    if not completed_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="COMPLETED status not found in system",
        )

    # Update complaint status
    complaint.status_id = completed_status.id
    complaint.updated_at = datetime.now(tz=timezone.utc)

    await db.commit()

    return {"message": "Complaint marked as completed successfully"}


# VDO endpoints
@router.patch("/vdo/complaints/{complaint_id}/verify")
async def verify_complaint(
    complaint_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """VDO verifies and closes a completed complaint."""
    # Check if user is a VDO
    if not PermissionChecker.user_has_role(current_user, [UserRole.VDO]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only VDOs can verify complaints",
        )

    # Get complaint with location info
    result = await db.execute(
        select(Complaint)
        .options(selectinload(Complaint.status))
        .where(Complaint.id == complaint_id)
    )
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found"
        )

    # Check if VDO can access this complaint based on location
    if not PermissionChecker.user_can_access_village(
        current_user, complaint.village_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only verify complaints in your jurisdiction",
        )

    # Check if complaint is in COMPLETED status
    if complaint.status.name != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only verify complaints that are marked as completed",
        )

    # Get "VERIFIED" status
    status_result = await db.execute(
        select(ComplaintStatus).where(ComplaintStatus.name == "VERIFIED")
    )
    verified_status = status_result.scalar_one_or_none()

    if not verified_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VERIFIED status not found in system",
        )

    # Update complaint status
    complaint.status_id = verified_status.id
    complaint.updated_at = datetime.now(tz=timezone.utc)

    await db.commit()

    return {"message": "Complaint verified and closed successfully"}


@router.get("/vdo/village-complaints", response_model=List[ComplaintListResponse])
async def get_village_complaints(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(require_staff_role)
):
    """Get all complaints in the VDO's village with all statuses."""
    # Check if user is a VDO
    if not PermissionChecker.user_has_role(current_user, [UserRole.VDO]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only VDOs can access village complaints",
        )

    # Get VDO's villages
    vdo_villages = []
    for position in current_user.positions:
        if position.role.name == UserRole.VDO and position.village_id:
            vdo_villages.append(position.village_id)

    if not vdo_villages:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="VDO position not properly configured",
        )

    # Get complaints in VDO's villages
    result = await db.execute(
        select(Complaint)
        .options(
            selectinload(Complaint.village),
            selectinload(Complaint.block),
            selectinload(Complaint.district),
            selectinload(Complaint.status),
            selectinload(Complaint.assignments),
        )
        .where(Complaint.village_id.in_(vdo_villages))
        .order_by(Complaint.created_at.desc())
    )
    complaints = result.scalars().all()

    return [
        ComplaintListResponse(
            id=complaint.id,
            description=complaint.description,
            status_name=complaint.status.name,
            village_name=complaint.village.name,
            block_name=complaint.block.name,
            district_name=complaint.district.name,
            created_at=complaint.created_at,
            updated_at=complaint.updated_at,
            assigned_worker=None,  # TODO: Load assignment user data properly
        )
        for complaint in complaints
    ]


# BDO/CEO/ADMIN endpoints
@router.get("/complaints", response_model=List[ComplaintListResponse])
async def get_complaints_by_jurisdiction(
    district_id: Optional[int] = Query(None, description="Filter by district"),
    block_id: Optional[int] = Query(None, description="Filter by block"),
    village_id: Optional[int] = Query(None, description="Filter by village"),
    status_name: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """Get complaints filtered by jurisdiction based on user role."""

    # Build query based on user permissions
    query = select(Complaint).options(
        selectinload(Complaint.village),
        selectinload(Complaint.block),
        selectinload(Complaint.district),
        selectinload(Complaint.status),
        selectinload(Complaint.assignments),
    )

    # Apply jurisdiction filters based on user role
    user_roles = [pos.role.name for pos in current_user.positions if pos.role]

    if UserRole.ADMIN not in user_roles:
        # Non-admin users can only see complaints in their jurisdiction
        jurisdiction_filter = []

        for position in current_user.positions:
            if position.role.name == UserRole.CEO and position.district_id:
                jurisdiction_filter.append(
                    Complaint.district_id == position.district_id
                )
            elif position.role.name == UserRole.BDO and position.block_id:
                jurisdiction_filter.append(Complaint.block_id == position.block_id)
            elif position.role.name == UserRole.VDO and position.village_id:
                jurisdiction_filter.append(Complaint.village_id == position.village_id)

        if jurisdiction_filter:
            query = query.where(or_(*jurisdiction_filter))
        else:
            # If no valid jurisdiction found, return empty result
            return []

    # Apply optional filters
    if district_id:
        query = query.where(Complaint.district_id == district_id)
    if block_id:
        query = query.where(Complaint.block_id == block_id)
    if village_id:
        query = query.where(Complaint.village_id == village_id)

    if status_name:
        query = query.join(ComplaintStatus).where(ComplaintStatus.name == status_name)

    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Complaint.created_at.desc())

    result = await db.execute(query)
    complaints = result.scalars().all()

    return [
        ComplaintListResponse(
            id=complaint.id,
            description=complaint.description,
            status_name=complaint.status.name,
            village_name=complaint.village.name,
            block_name=complaint.block.name,
            district_name=complaint.district.name,
            created_at=complaint.created_at,
            updated_at=complaint.updated_at,
            assigned_worker=None,  # TODO: Load assignment user data properly
        )
        for complaint in complaints
    ]


# Public endpoint (no authentication required)
@router.get("/public/complaints-status", response_model=List[ComplaintStatusResponse])
async def get_public_complaints_status(
    district_id: Optional[int] = Query(None, description="Filter by district"),
    block_id: Optional[int] = Query(None, description="Filter by block"),
    village_id: Optional[int] = Query(None, description="Filter by village"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of records to return"),
    db: AsyncSession = Depends(get_db),
):
    """Public API to see the status of all complaints."""

    query = select(Complaint).options(
        selectinload(Complaint.village), selectinload(Complaint.status)
    )

    # Apply optional filters
    if district_id:
        query = query.where(Complaint.district_id == district_id)
    if block_id:
        query = query.where(Complaint.block_id == block_id)
    if village_id:
        query = query.where(Complaint.village_id == village_id)

    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Complaint.created_at.desc())

    result = await db.execute(query)
    complaints = result.scalars().all()

    return [
        ComplaintStatusResponse(
            id=complaint.id,
            description=complaint.description,
            status_name=complaint.status.name,
            village_name=complaint.village.name,
            created_at=complaint.created_at,
        )
        for complaint in complaints
    ]


# Additional endpoints for detailed complaint views
@router.get("/complaints/{complaint_id}", response_model=AssignedComplaintResponse)
async def get_complaint_details(
    complaint_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """Get detailed information about a specific complaint (Staff only)."""
    # Get complaint with all related data
    result = await db.execute(
        select(Complaint)
        .options(
            selectinload(Complaint.village),
            selectinload(Complaint.block),
            selectinload(Complaint.district),
            selectinload(Complaint.status),
            selectinload(Complaint.media),
        )
        .where(Complaint.id == complaint_id)
    )
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found"
        )

    # Check permissions based on user role and jurisdiction
    user_roles = [pos.role.name for pos in current_user.positions if pos.role]

    if UserRole.ADMIN not in user_roles:
        has_access = False
        for position in current_user.positions:
            if (
                position.role.name == UserRole.CEO
                and position.district_id == complaint.district_id
            ):
                has_access = True
                break
            elif (
                position.role.name == UserRole.BDO
                and position.block_id == complaint.block_id
            ):
                has_access = True
                break
            elif (
                position.role.name == UserRole.VDO
                and position.village_id == complaint.village_id
            ):
                has_access = True
                break
            elif position.role.name == UserRole.WORKER:
                # Check if worker is assigned to this complaint
                assignment_result = await db.execute(
                    select(ComplaintAssignment).where(
                        and_(
                            ComplaintAssignment.complaint_id == complaint_id,
                            ComplaintAssignment.user_id == current_user.id,
                        )
                    )
                )
                if assignment_result.scalar_one_or_none():
                    has_access = True
                    break

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this complaint",
            )

    return AssignedComplaintResponse(
        id=complaint.id,
        description=complaint.description,
        status_name=complaint.status.name,
        village_name=complaint.village.name,
        block_name=complaint.block.name,
        district_name=complaint.district.name,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
        media_urls=[media.media_url for media in complaint.media],
    )
