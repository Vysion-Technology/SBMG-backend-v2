"""Controller for managing complaints in the SBM Rajasthan system."""

# pylint: disable=line-too-long
import logging
from typing import Any, Dict, List, Optional
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload


from database import get_db
from auth_utils import (
    require_staff_role,
    PermissionChecker,
    UserRole,
    require_worker_role,
)

from models.database.auth import User
from models.database.complaint import (
    Complaint,
    ComplaintStatus,
    ComplaintMedia,
    ComplaintComment,
)
from models.response.complaint import DetailedComplaintResponse, MediaResponse
from models.response.analytics import (
    ComplaintDateAnalyticsResponse,
    ComplaintGeoAnalyticsResponse,
    TopNGeographiesInDateRangeResponse,
)
from models.response.complaint import (
    ComplaintCommentResponse,
    ResolveComplaintResponse,
)
from models.internal import GeoTypeEnum
from models.requests.complaint import (
    UpdateComplaintStatusRequest,
    ResolveComplaintRequest,
)

from services.s3_service import s3_service
from services.auth import AuthService
from services.fcm_notification_service import notify_user_on_complaint_status_update
from services.complaints import ComplaintOrderByEnum, ComplaintService

router = APIRouter()


# Helper function to get public user by token


# Pydantic models


@router.get("/my", response_model=List[DetailedComplaintResponse])
async def get_my_complaints(
    db: AsyncSession = Depends(get_db),
    token: str = Header(..., description="Public user token"),
    skip: Optional[int] = None,
    limit: Optional[int] = 100,
    order_by: ComplaintOrderByEnum = ComplaintOrderByEnum.NEWEST,
) -> List[DetailedComplaintResponse]:
    """Get complaints created by the authenticated public user."""
    # Verify the public user token
    auth_service = AuthService(db)
    user = await auth_service.get_public_user_by_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing user token",
        )

    # Query complaints by mobile number
    query = (
        select(Complaint)
        .options(
            selectinload(Complaint.status),
            selectinload(Complaint.gp),
            selectinload(Complaint.block),
            selectinload(Complaint.district),
            selectinload(Complaint.complaint_type),
            selectinload(Complaint.media),
            selectinload(Complaint.comments),
        )
        .where(Complaint.public_user_id == user.id)
    )

    # Apply ordering
    if order_by == ComplaintOrderByEnum.NEWEST:
        query = query.order_by(Complaint.created_at.desc())
    elif order_by == ComplaintOrderByEnum.OLDEST:
        query = query.order_by(Complaint.created_at.asc())
    elif order_by == ComplaintOrderByEnum.STATUS:
        query = query.order_by(Complaint.status_id)
    elif order_by == ComplaintOrderByEnum.DISTRICT:
        query = query.order_by(Complaint.district_id)
    elif order_by == ComplaintOrderByEnum.BLOCK:
        query = query.order_by(Complaint.block_id)
    elif order_by == ComplaintOrderByEnum.GP:
        query = query.order_by(Complaint.gp_id)

    # Apply pagination
    if skip is not None:
        query = query.offset(skip)
    if limit is not None:
        query = query.limit(limit)

    # Execute query
    result = await db.execute(query)
    complaints = result.scalars().all()

    # Transform to response format
    return [
        DetailedComplaintResponse(
            id=complaint.id,
            description=complaint.description,
            complaint_type_id=complaint.complaint_type_id,
            mobile_number=complaint.mobile_number,
            created_at=complaint.created_at,
            updated_at=complaint.updated_at,
            status_id=complaint.status_id,
            lat=complaint.lat,
            long=complaint.long,
            location=complaint.location,
            resolved_at=complaint.resolved_at,
            verified_at=complaint.verified_at,
            closed_at=complaint.closed_at,
            complaint_type=complaint.complaint_type.name if complaint.complaint_type else None,
            status=complaint.status.name if complaint.status else None,
            village_name=complaint.gp.name if complaint.gp else None,
            block_name=complaint.block.name if complaint.block else None,
            district_name=complaint.district.name if complaint.district else None,
            media_urls=[media.media_url for media in complaint.media] if complaint.media else [],
            media=[
                MediaResponse(
                    id=media.id,
                    media_url=media.media_url,
                    uploaded_at=media.uploaded_at,
                )
                for media in complaint.media
            ]
            if complaint.media
            else [],
            comments=[
                ComplaintCommentResponse(
                    id=comment.id,
                    complaint_id=comment.complaint_id,
                    comment=comment.comment,
                    commented_at=comment.commented_at,
                    user_name=comment.user.name if comment.user else "",
                )
                for comment in complaint.comments
            ],
        )
        for complaint in complaints
    ]


@router.patch("/{complaint_id}/status")
async def update_complaint_status(
    complaint_id: int,
    status_request: UpdateComplaintStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),  # pylint: disable=unused-argument
):
    """Update complaint status (Staff only)."""
    # Get complaint
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    # Get status
    status_result = await db.execute(select(ComplaintStatus).where(ComplaintStatus.name == status_request.status_name))
    new_status = status_result.scalar_one_or_none()

    if not new_status:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status not found")

    # Update complaint
    complaint.status_id = new_status.id
    complaint.updated_at = datetime.now()  # type: ignore

    await db.commit()

    # Send notification to the user who created the complaint

    try:
        await notify_user_on_complaint_status_update(db, complaint, new_status.name)
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Log error but don't fail the request
        logging.error("Failed to send FCM notification: %s", e)

    return {"message": "Complaint status updated successfully"}


@router.post("/{complaint_id}/comments", response_model=ComplaintCommentResponse)
async def add_complaint_comment(
    complaint_id: int,
    comment_text: str = Form(...),
    photo: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """Add a comment to a complaint (Workers and VDOs only, within their village)."""
    # Check if user is a Worker or VDO
    if not PermissionChecker.user_has_role(current_user, [UserRole.WORKER, UserRole.VDO]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Workers and VDOs can comment on complaints",
        )

    # Get complaint with village information
    result = await db.execute(select(Complaint).options(selectinload(Complaint.gp)).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    if complaint.gp_id != current_user.gp_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only comment on complaints in your assigned village",
        )

    # Create comment
    comment = ComplaintComment(complaint_id=complaint_id, user_id=current_user.id, comment=comment_text)

    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    # Handle photo upload if provided
    if photo and photo.filename:
        try:
            # Upload photo to S3/MinIO
            s3_key = await s3_service.upload_file(
                file=photo,
                folder=f"complaints/{complaint_id}/comments/{comment.id}",
                filename=photo.filename,
            )

            # Get the media URL for database storage
            if s3_service.is_available():
                # Use S3 key for database storage
                media_url = s3_key
            else:
                # Fallback to local path
                media_url = f"/media/complaints/{complaint_id}/comments/{comment.id}/{photo.filename}"

            # Create media record
            media = ComplaintMedia(
                complaint_id=complaint_id,
                media_url=media_url,
                uploaded_by_user_id=current_user.id,
                uploaded_by_public_mobile=None,
            )
            db.add(media)
            await db.commit()
        except HTTPException:
            # If S3 upload fails, continue without photo
            pass

    # Get user name for response
    user_positions = current_user.positions
    user_name = "Unknown User"
    if user_positions:
        first_pos = user_positions[0]
        user_name = f"{first_pos.first_name} {first_pos.last_name}"

    return ComplaintCommentResponse(
        id=comment.id,
        complaint_id=comment.complaint_id,
        comment=comment.comment,
        commented_at=comment.commented_at,
        user_name=user_name,
    )


@router.post("/{complaint_id}/media", response_model=MediaResponse)
async def upload_complaint_media(
    complaint_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_worker_role),
):
    """Upload media to a complaint (Workers and VDOs only, within their village)."""
    # Check if user is a Worker or VDO
    if not PermissionChecker.user_has_role(current_user, [UserRole.WORKER, UserRole.VDO]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Workers and VDOs can upload media to complaints",
        )

    # Get complaint with village information
    result = await db.execute(select(Complaint).options(selectinload(Complaint.gp)).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    # Check village access
    if complaint.gp_id != current_user.gp_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only upload media to complaints in your assigned village",
        )

    try:
        # Upload file to S3/MinIO
        s3_key = await s3_service.upload_file(
            file=file,
            folder=f"complaints/{complaint_id}/media",
            filename=file.filename,
        )

        # Get the media URL for database storage
        if s3_service.is_available():
            # Use S3 key for database storage
            media_url = s3_key
        else:
            # Fallback to local path
            media_url = f"/media/complaints/{complaint_id}/media/{file.filename}"

        # Create media record
        media = ComplaintMedia(
            complaint_id=complaint_id,
            media_url=media_url,
            uploaded_by_user_id=current_user.id,
            uploaded_by_public_mobile=None,
        )
        db.add(media)
        await db.commit()
        await db.refresh(media)

        return MediaResponse(id=media.id, media_url=media.media_url, uploaded_at=media.uploaded_at)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload media",
        ) from e


@router.patch("/{complaint_id}/resolve", response_model=ResolveComplaintResponse)
async def resolve_complaint(
    complaint_id: int,
    resolve_request: ResolveComplaintRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_worker_role),
):
    """Mark complaint as resolved (Workers only, within their village)."""
    # Check if user is a Worker
    if not PermissionChecker.user_has_role(current_user, [UserRole.WORKER]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Workers can resolve complaints",
        )

    # Get complaint with village information
    result = await db.execute(select(Complaint).options(selectinload(Complaint.gp)).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    # Check if the user has access to the complaint's village
    if current_user.gp_id != complaint.gp_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only resolve complaints in your assigned village",
        )
    # Get or create "RESOLVED" status
    status_result = await db.execute(select(ComplaintStatus).where(ComplaintStatus.name == "RESOLVED"))
    resolved_status = status_result.scalar_one_or_none()
    assert resolved_status is not None, "Resolved status should not be None"
    if complaint.status_id == resolved_status.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complaint is already resolved",
        )
    if not resolved_status:
        resolved_status = ComplaintStatus(name="RESOLVED", description="Complaint has been resolved")
        db.add(resolved_status)
        await db.commit()
        await db.refresh(resolved_status)

    # Update complaint status
    complaint.status_id = resolved_status.id
    complaint.resolved_at = datetime.now(tz=timezone.utc)
    complaint.updated_at = datetime.now()  # type: ignore

    # Add resolution comment if provided
    if resolve_request.resolution_comment:
        comment = ComplaintComment(
            complaint_id=complaint_id,
            user_id=current_user.id,
            comment=f"[RESOLVED] {resolve_request.resolution_comment}",
        )
        db.add(comment)

    await db.commit()

    return ResolveComplaintResponse(message="Complaint resolved successfully", complaint_id=complaint_id)


# VDO-specific endpoints
@router.patch("/vdo/complaints/{complaint_id}/verify")
async def verify_complaint(
    complaint_id: int,
    comment: Optional[str] = Form(...),
    media: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
) -> Dict[str, Any]:
    """Verify a completed complaint (VDOs only, within their village)."""

    if not PermissionChecker.user_has_role(current_user, [UserRole.VDO]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only VDOs can verify complaints",
        )

    query = select(Complaint).options(selectinload(Complaint.status)).where(Complaint.id == complaint_id)
    result = await db.execute(query)
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found for the provided ID",
        )

    # Check if complaint is in COMPLETED status
    if complaint.status.name == "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only verify complaints that are marked as completed",
        )

    if complaint.status.name == "VERIFIED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complaint is already verified",
        )

    if complaint.status.name != "RESOLVED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only verify complaints that are marked as resolved",
        )

    # Get "VERIFIED" status
    status_query = select(ComplaintStatus).where(ComplaintStatus.name == "VERIFIED")
    status_result = await db.execute(status_query)
    verified_status = status_result.scalar_one_or_none()

    if not verified_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VERIFIED status not found in system",
        )

    if comment:
        # Add verification comment
        verification_comment = ComplaintComment(
            complaint_id=complaint_id,
            user_id=current_user.id,
            comment=f"[VERIFIED] {comment}",
            commented_at=datetime(
                datetime.now(timezone.utc).year,
                datetime.now(timezone.utc).month,
                datetime.now(timezone.utc).day,
            ),
        )
        db.add(verification_comment)
        await db.commit()

    error_msg = ""
    if media and media.filename:
        try:
            # Upload media to S3/MinIO
            s3_key = await s3_service.upload_file(
                file=media,
                folder=f"complaints/{complaint_id}/verification",
                filename=media.filename,
            )

            # Get the media URL for database storage
            if s3_service.is_available():
                # Use S3 key for database storage
                media_url = s3_key
            else:
                # Fallback to local path
                media_url = f"/media/complaints/{complaint_id}/verification/{media.filename}"

            # Create media record
            verification_media = ComplaintMedia(
                complaint_id=complaint_id,
                media_url=media_url,
                uploaded_by_user_id=current_user.id,
                uploaded_at=datetime(
                    datetime.now(timezone.utc).year,
                    datetime.now(timezone.utc).month,
                    datetime.now(timezone.utc).day,
                ),
            )
            db.add(verification_media)
            await db.commit()
        except HTTPException as e:
            # If S3 upload fails, continue without media
            logging.warning("Failed to upload verification media, continuing without it.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload verification media",
            ) from e

    # Update complaint status
    complaint.status_id = verified_status.id
    complaint.verified_at = datetime.now(tz=timezone.utc)
    complaint.updated_at = datetime.now()

    await db.commit()

    return {
        "message": "Complaint verified successfully",
        "complaint_id": complaint_id,
        "error": error_msg.strip(),
    }


@router.get("/analytics/geo")
async def get_complaint_counts_by_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
    district_id: Optional[int] = None,
    block_id: Optional[int] = None,
    gp_id: Optional[int] = None,
    level: GeoTypeEnum = GeoTypeEnum.DISTRICT,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> ComplaintGeoAnalyticsResponse:
    """Get complaint counts by status for analytics (Staff only)."""
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
    if (district_id and block_id) or (district_id and gp_id) or (block_id and gp_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide only one of district_id, block_id, or gp_id",
        )
    if level == GeoTypeEnum.DISTRICT and (district_id or block_id or gp_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="district_id should not be provided when level is DISTRICT",
        )
    if level == GeoTypeEnum.BLOCK and (block_id or gp_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="block_id and gp_id should not be provided when level is BLOCK",
        )
    return await ComplaintService(db).count_complaints_by_status_and_geo(
        district_id=district_id,
        block_id=block_id,
        gp_id=gp_id,
        start_date=datetime(
            start_date.year,
            start_date.month,
            start_date.day,
            0,
            0,
            0,
            tzinfo=timezone.utc,
        )
        if start_date
        else None,
        end_date=datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=timezone.utc)
        if end_date
        else None,
        level=level,
    )


@router.get("/analytics/daterange")
async def get_complaint_counts_by_date(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
    district_id: Optional[int] = None,
    block_id: Optional[int] = None,
    gp_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[ComplaintDateAnalyticsResponse]:
    """Get complaint counts by date range for analytics (Staff only)."""
    if current_user.block_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access date range analytics",
        )
    if current_user.gp_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access date range analytics",
        )
    if (district_id and block_id) or (district_id and gp_id) or (block_id and gp_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide only one of district_id, block_id, or gp_id",
        )
    return await ComplaintService(db).count_complaints_by_date(
        district_id=district_id,
        block_id=block_id,
        gp_id=gp_id,
        start_date=datetime(
            start_date.year,
            start_date.month,
            start_date.day,
            0,
            0,
            0,
            tzinfo=timezone.utc,
        )
        if start_date
        else None,
        end_date=datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=timezone.utc)
        if end_date
        else None,
    )


@router.get("/analytics/top-n")
async def get_top_n_complaint_types(
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
    n: int = 5,
    level: GeoTypeEnum = GeoTypeEnum.DISTRICT,
    district_id: Optional[int] = None,
    block_id: Optional[int] = None,
    gp_id: Optional[int] = None,
) -> List[TopNGeographiesInDateRangeResponse]:
    """Get top N complaint types for analytics (Staff only)."""
    if current_user.block_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access top N complaint types analytics",
        )
    if current_user.gp_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access top N complaint types analytics",
        )
    if (district_id and block_id) or (district_id and gp_id) or (block_id and gp_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide only one of district_id, block_id, or gp_id",
        )
    return await ComplaintService(db).get_top_n_complaint_types(
        n=n,
        district_id=district_id,
        block_id=block_id,
        gp_id=gp_id,
        level=level,
        start_date=datetime(
            start_date.year,
            start_date.month,
            start_date.day,
            0,
            0,
            0,
            tzinfo=timezone.utc,
        ),
        end_date=datetime(
            end_date.year,
            end_date.month,
            end_date.day,
            23,
            59,
            59,
            tzinfo=timezone.utc,
        ),
    )


@router.get("")
async def get_all_complaints(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),  # pylint: disable=unused-argument
    district_id: Optional[int] = None,
    block_id: Optional[int] = None,
    gp_id: Optional[int] = None,
    complaint_status_id: Optional[int] = None,
    skip: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: Optional[int] = 500,
    order_by: ComplaintOrderByEnum = ComplaintOrderByEnum.NEWEST,
) -> List[DetailedComplaintResponse]:
    """Get all complaints (Staff only)."""
    return await ComplaintService(db).get_all_complaints(
        district_id=district_id,
        block_id=block_id,
        village_id=gp_id,
        complaint_status_id=complaint_status_id,
        start_date=datetime(
            start_date.year,
            start_date.month,
            start_date.day,
            0,
            0,
            0,
            tzinfo=timezone.utc,
        )
        if start_date
        else None,
        end_date=datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=timezone.utc)
        if end_date
        else None,
        skip=skip,
        limit=limit,
        order_by=order_by,
    )
