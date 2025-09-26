from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from database import get_db
from models.database.auth import User
from models.database.complaint import Complaint, ComplaintStatus, ComplaintMedia, ComplaintComment, ComplaintAssignment
from models.database.geography import Village, Block
from auth_utils import require_staff_role, PermissionChecker, UserRole
from services.s3_service import s3_service

router = APIRouter()


# Pydantic models
class CreateComplaintRequest(BaseModel):
    complaint_type_id: int
    village_id: int
    block_id: int
    district_id: int
    description: str
    mobile_number: Optional[str] = None


class UpdateComplaintStatusRequest(BaseModel):
    status_name: str


class AddCommentRequest(BaseModel):
    comment: str


class ComplaintCommentResponse(BaseModel):
    id: int
    complaint_id: int
    comment: str
    commented_at: datetime
    user_name: str


class ResolveComplaintRequest(BaseModel):
    resolution_comment: Optional[str] = None


class ResolveComplaintResponse(BaseModel):
    message: str
    complaint_id: int


class MediaResponse(BaseModel):
    id: int
    media_url: str
    uploaded_at: datetime


class ComplaintResponse(BaseModel):
    id: int
    description: str
    mobile_number: Optional[str] = None
    status_name: str
    village_name: str
    block_name: str
    district_name: str
    created_at: datetime
    updated_at: Optional[datetime]
    media_urls: List[str] = []
    media: List[MediaResponse] = []


class MediaUploadResponse(BaseModel):
    id: int
    complaint_id: int
    media_url: str
    uploaded_at: datetime


class ComplaintStatusResponse(BaseModel):
    id: int
    status_name: str
    updated_at: Optional[datetime]


class DetailedComplaintResponse(BaseModel):
    id: int
    description: str
    mobile_number: Optional[str] = None
    complaint_type_name: str
    status_name: str
    village_name: str
    block_name: str
    district_name: str
    created_at: datetime
    updated_at: Optional[datetime]
    media_urls: List[str] = []
    media: List[MediaResponse] = []
    comments: List[ComplaintCommentResponse] = []
    assigned_worker: Optional[str] = None
    assignment_date: Optional[datetime] = None


class CitizenStatusUpdateRequest(BaseModel):
    complaint_id: int
    mobile_number: str
    new_status: str  # Should be "VERIFIED" or "RESOLVED"


class CitizenStatusUpdateResponse(BaseModel):
    message: str
    complaint_id: int
    new_status: str
    updated_at: datetime


class VerifyComplaintStatusRequest(BaseModel):
    complaint_id: int
    mobile_number: str


class VerifyComplaintStatusResponse(BaseModel):
    complaint_id: int
    current_status: str
    message: str


# Public endpoints (no authentication required)

@router.get("/{complaint_id}/details", response_model=DetailedComplaintResponse)
async def get_detailed_complaint(complaint_id: int, db: AsyncSession = Depends(get_db)):
    """Get detailed complaint information with all related data (Public access)."""
    # Query complaint with all related data
    result = await db.execute(
        select(Complaint)
        .options(
            selectinload(Complaint.complaint_type),
            selectinload(Complaint.status),
            selectinload(Complaint.village).selectinload(Village.block).selectinload(Block.district),
            selectinload(Complaint.media),
            selectinload(Complaint.comments).selectinload(ComplaintComment.user).selectinload(User.positions),
            selectinload(Complaint.assignments).selectinload(ComplaintAssignment.user).selectinload(User.positions)
        )
        .where(Complaint.id == complaint_id)
    )
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    # Get media URLs and detailed media information
    media_details = [
        MediaResponse(
            id=media.id,
            media_url=media.media_url,
            uploaded_at=media.uploaded_at
        ) for media in complaint.media
    ]

    # Get comments with user names
    comments = []
    for comment in complaint.comments:
        user_name = "Unknown User"
        if comment.user and comment.user.positions:
            first_pos = comment.user.positions[0]
            user_name = f"{first_pos.first_name} {first_pos.last_name}"
        elif comment.user:
            user_name = comment.user.username
        
        comments.append(ComplaintCommentResponse(
            id=comment.id,
            complaint_id=comment.complaint_id,
            comment=comment.comment,
            commented_at=comment.commented_at,
            user_name=user_name
        ))

    # Get assigned worker info
    assigned_worker = None
    assignment_date = None
    if complaint.assignments:
        latest_assignment = max(complaint.assignments, key=lambda a: a.assigned_at)
        if latest_assignment.user and latest_assignment.user.positions:
            first_pos = latest_assignment.user.positions[0]
            assigned_worker = f"{first_pos.first_name} {first_pos.last_name}"
        elif latest_assignment.user:
            assigned_worker = latest_assignment.user.username
        assignment_date = latest_assignment.assigned_at

    return DetailedComplaintResponse(
        id=complaint.id,
        description=complaint.description,
        mobile_number=complaint.mobile_number,
        complaint_type_name=complaint.complaint_type.name,
        status_name=complaint.status.name,
        village_name=complaint.village.name,
        block_name=complaint.village.block.name,
        district_name=complaint.village.block.district.name,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
        media=media_details,
        comments=comments,
        assigned_worker=assigned_worker,
        assignment_date=assignment_date
    )


@router.post("/citizen/update-status", response_model=CitizenStatusUpdateResponse)
async def citizen_update_complaint_status(
    status_request: CitizenStatusUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Allow citizens to update complaint status using complaint ID and mobile number (Public access)."""
    # Verify complaint exists and mobile number matches
    result = await db.execute(
        select(Complaint)
        .options(selectinload(Complaint.status))
        .where(
            Complaint.id == status_request.complaint_id,
            Complaint.mobile_number == status_request.mobile_number
        )
    )
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Complaint not found or mobile number does not match"
        )

    # Only allow specific status transitions for citizens
    allowed_statuses = ["VERIFIED", "RESOLVED"]
    if status_request.new_status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Citizens can only set status to: {', '.join(allowed_statuses)}"
        )

    # Ensure the complaint is in a state that allows citizen updates
    # For example, only allow verification if complaint is COMPLETED
    current_status = complaint.status.name
    if status_request.new_status == "VERIFIED" and current_status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only verify complaints that are marked as COMPLETED"
        )

    # Get or create the new status
    status_result = await db.execute(
        select(ComplaintStatus).where(ComplaintStatus.name == status_request.new_status)
    )
    new_status = status_result.scalar_one_or_none()

    if not new_status:
        # Create the status if it doesn't exist
        new_status = ComplaintStatus(
            name=status_request.new_status,
            description="Status set by citizen verification"
        )
        db.add(new_status)
        await db.commit()
        await db.refresh(new_status)

    # Update complaint status
    complaint.status_id = new_status.id
    complaint.updated_at = datetime.now()  # type: ignore

    # Add a comment to track the citizen update
    comment = ComplaintComment(
        complaint_id=complaint.id,
        user_id=None,  # No user_id for citizen updates
        comment=f"Status updated to {status_request.new_status} by citizen via mobile verification"
    )
    db.add(comment)

    await db.commit()

    return CitizenStatusUpdateResponse(
        message=f"Complaint status updated to {status_request.new_status} successfully",
        complaint_id=complaint.id,
        new_status=status_request.new_status,
        updated_at=complaint.updated_at or datetime.now()
    )


@router.post("/citizen/verify-status", response_model=VerifyComplaintStatusResponse)
async def verify_complaint_status(
    verify_request: VerifyComplaintStatusRequest,
    db: AsyncSession = Depends(get_db)
):
    """Verify complaint status using complaint ID and mobile number (Public access)."""
    # Verify complaint exists and mobile number matches
    result = await db.execute(
        select(Complaint)
        .options(selectinload(Complaint.status))
        .where(
            Complaint.id == verify_request.complaint_id,
            Complaint.mobile_number == verify_request.mobile_number
        )
    )
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Complaint not found or mobile number does not match"
        )

    
    # Determine appropriate message based on status
    
    # Save the status to DB
    complaint.status = (await db.execute(select(ComplaintStatus).where(ComplaintStatus.name == "COMPLETED"))).scalar_one()
    complaint.status_id = complaint.status_id  # No change, just to trigger update
    await db.commit()
    await db.refresh(complaint)

    return VerifyComplaintStatusResponse(
        complaint_id=complaint.id,
        current_status=complaint.status.name,
        message=f"Your complaint is currently {complaint.status.name.replace('_', ' ')}."
    )


@router.post("/", response_model=ComplaintResponse)
async def create_complaint(complaint_request: CreateComplaintRequest, db: AsyncSession = Depends(get_db)):
    """Create a new complaint (Public access)."""
    # Verify village exists
    village_result = await db.execute(
        select(Village)
        .options(selectinload(Village.block), selectinload(Village.district))
        .where(Village.id == complaint_request.village_id)
    )
    village = village_result.scalar_one_or_none()
    if not village:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Village not found")

    # Get or create "OPEN" status
    status_result = await db.execute(select(ComplaintStatus).where(ComplaintStatus.name == "OPEN"))
    complaint_status = status_result.scalar_one_or_none()
    if not complaint_status:
        complaint_status = ComplaintStatus(name="OPEN", description="Newly created complaint")
        db.add(complaint_status)
        await db.commit()
        await db.refresh(complaint_status)

    # Create complaint
    complaint = Complaint(
        complaint_type_id=complaint_request.complaint_type_id,
        village_id=complaint_request.village_id,
        block_id=complaint_request.block_id,
        district_id=complaint_request.district_id,
        description=complaint_request.description,
        mobile_number=complaint_request.mobile_number,
        status_id=complaint_status.id,
    )

    db.add(complaint)
    await db.commit()
    await db.refresh(complaint)

    return ComplaintResponse(
        id=complaint.id,
        description=complaint.description,
        mobile_number=complaint.mobile_number,
        status_name=complaint_status.name,
        village_name=village.name,
        block_name=village.block.name,
        district_name=village.district.name,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
        media_urls=[],
        media=[],
    )


@router.post("/with-media", response_model=ComplaintResponse)
async def create_complaint_with_media(
    complaint_type_id: int = Form(...),
    village_id: int = Form(...),
    block_id: int = Form(...),
    district_id: int = Form(...),
    description: str = Form(...),
    mobile_number: Optional[str] = Form(None),
    files: List[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db),
):
    """Create a new complaint with optional media files (Public access)."""
    # Create the complaint first using similar logic to create_complaint
    # Verify village exists
    village_result = await db.execute(
        select(Village)
        .options(selectinload(Village.block), selectinload(Village.district))
        .where(Village.id == village_id)
    )
    village = village_result.scalar_one_or_none()
    if not village:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Village not found")

    # Get or create "OPEN" status
    status_result = await db.execute(select(ComplaintStatus).where(ComplaintStatus.name == "OPEN"))
    complaint_status = status_result.scalar_one_or_none()
    if not complaint_status:
        complaint_status = ComplaintStatus(name="OPEN", description="Newly created complaint")
        db.add(complaint_status)
        await db.commit()
        await db.refresh(complaint_status)

    # Create complaint
    complaint = Complaint(
        complaint_type_id=complaint_type_id,
        village_id=village_id,
        block_id=block_id,
        district_id=district_id,
        description=description,
        mobile_number=mobile_number,
        status_id=complaint_status.id,
    )

    db.add(complaint)
    await db.commit()
    await db.refresh(complaint)

    # Handle media files if provided
    media_urls: List[str] = []
    for file in files:
        if file.filename:
            try:
                # Upload file to S3/MinIO
                s3_key = await s3_service.upload_file(
                    file=file,
                    folder=f"complaints/{complaint.id}",
                    filename=file.filename
                )
                
                # Get the public URL for the uploaded file
                if s3_service.is_available():
                    # Use S3 URL for database storage
                    media_url = s3_key
                else:
                    # Fallback to local path
                    media_url = f"/media/complaints/{complaint.id}/{file.filename}"

                # Create media record
                media = ComplaintMedia(complaint_id=complaint.id, media_url=media_url)
                db.add(media)
                media_urls.append(media_url)
                
            except HTTPException:
                # If S3 upload fails, continue without media
                # In production, you might want to handle this differently
                continue

    if media_urls:
        await db.commit()
        # Refresh complaint to get the latest media records
        await db.refresh(complaint)
        
        # Fetch media details after commit
        media_result = await db.execute(
            select(ComplaintMedia).where(ComplaintMedia.complaint_id == complaint.id)
        )
        media_records = media_result.scalars().all()
        
        media_details = [
            MediaResponse(
                id=media.id,
                media_url=media.media_url,
                uploaded_at=media.uploaded_at
            ) for media in media_records
        ]
    else:
        media_details = []

    return ComplaintResponse(
        id=complaint.id,
        description=complaint.description,
        mobile_number=complaint.mobile_number,
        status_name=complaint_status.name,
        village_name=village.name,
        block_name=village.block.name,
        district_name=village.district.name,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
        media_urls=media_urls,
        media=media_details,
    )


@router.patch("/{complaint_id}/status")
async def update_complaint_status(
    complaint_id: int,
    status_request: UpdateComplaintStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
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

    return {"message": "Complaint status updated successfully"}


@router.get("/{complaint_id}/status", response_model=ComplaintStatusResponse)
async def get_complaint_status(complaint_id: int, db: AsyncSession = Depends(get_db)):
    """Get complaint status (Public access)."""
    # Get complaint with its status
    result = await db.execute(
        select(Complaint, ComplaintStatus)
        .join(ComplaintStatus, Complaint.status_id == ComplaintStatus.id)
        .where(Complaint.id == complaint_id)
    )
    complaint_data = result.first()

    if not complaint_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    complaint, complaint_status = complaint_data

    return ComplaintStatusResponse(id=complaint.id, status_name=complaint_status.name, updated_at=complaint.updated_at)


# Helper function to check if user has access to a complaint in their village
async def check_complaint_village_access(user: User, complaint: Complaint) -> bool:
    """Check if user can access complaint based on village assignment."""
    # Admin can access everything
    if PermissionChecker.user_has_role(user, [UserRole.ADMIN.value]):
        return True

    # Check if user has access to the complaint's village
    return PermissionChecker.user_can_access_village(user, complaint.village_id)


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
    if not PermissionChecker.user_has_role(current_user, [UserRole.WORKER.value, UserRole.VDO.value]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only Workers and VDOs can comment on complaints"
        )

    # Get complaint with village information
    result = await db.execute(
        select(Complaint).options(selectinload(Complaint.village)).where(Complaint.id == complaint_id)
    )
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    # Check village access
    if not await check_complaint_village_access(current_user, complaint):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You can only comment on complaints in your assigned village"
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
                filename=photo.filename
            )
            
            # Get the media URL for database storage
            if s3_service.is_available():
                # Use S3 key for database storage
                media_url = s3_key
            else:
                # Fallback to local path
                media_url = f"/media/complaints/{complaint_id}/comments/{comment.id}/{photo.filename}"

            # Create media record
            media = ComplaintMedia(complaint_id=complaint_id, media_url=media_url)
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


@router.patch("/{complaint_id}/resolve", response_model=ResolveComplaintResponse)
async def resolve_complaint(
    complaint_id: int,
    resolve_request: ResolveComplaintRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """Mark complaint as resolved (VDOs only, within their village)."""
    # Check if user is a VDO
    if not PermissionChecker.user_has_role(current_user, [UserRole.VDO.value]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only VDOs can resolve complaints")

    # Get complaint with village information
    result = await db.execute(
        select(Complaint).options(selectinload(Complaint.village)).where(Complaint.id == complaint_id)
    )
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    # Check village access
    if not await check_complaint_village_access(current_user, complaint):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You can only resolve complaints in your assigned village"
        )

    # Get or create "RESOLVED" status
    status_result = await db.execute(select(ComplaintStatus).where(ComplaintStatus.name == "RESOLVED"))
    resolved_status = status_result.scalar_one_or_none()
    if not resolved_status:
        resolved_status = ComplaintStatus(name="RESOLVED", description="Complaint has been resolved")
        db.add(resolved_status)
        await db.commit()
        await db.refresh(resolved_status)

    # Update complaint status
    complaint.status_id = resolved_status.id
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
