"""Controller for citizen (public user) related complaint operations."""

import logging
from datetime import datetime, timezone
import os
import traceback
import uuid
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    File,
    UploadFile,
    Form,
    Header,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import get_db
from services.auth import AuthService
from services.complaints import ComplaintService
from services.fcm_notification_service import notify_workers_on_new_complaint
from services.s3_service import s3_service

from models.database.complaint import Complaint, ComplaintStatus, ComplaintMedia, ComplaintComment
from models.database.contractor import Contractor
from models.database.geography import GramPanchayat
from models.database.auth import PublicUser, PublicUserToken, User
from models.response.complaint import ComplaintCommentResponse, ComplaintResponse, MediaResponse

router = APIRouter()


@router.post("/with-media", response_model=ComplaintResponse)
async def create_complaint_with_media(
    complaint_type_id: int = Form(...),
    gp_id: int = Form(..., description="Gram Panchayat (village) ID"),
    description: str = Form(..., description="Complaint description"),
    files: List[UploadFile] = File(default=[]),
    lat: float = Form(..., description="Latitude"),
    long: float = Form(..., description="Longitude"),
    location: str = Form(..., description="Location description"),
    db: AsyncSession = Depends(get_db),
    token: str = Header(..., description="Public user token"),
) -> ComplaintResponse:
    """Create a new complaint with optional media files (Public access)."""
    try:
        # Create the complaint first using similar logic to create_complaint
        # Verify village exists
        if not lat or not long:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Latitude and Longitude are required",
            )
        gp = await db.execute(
            select(GramPanchayat).join(GramPanchayat.block)
            .options(selectinload(GramPanchayat.block), selectinload(GramPanchayat.district))
            .where(GramPanchayat.id == gp_id)
        )
        gp = gp.scalar_one_or_none()
        if not gp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gram Panchayat not found")

        auth_service = AuthService(db)
        user = await auth_service.get_public_user_by_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing user token",
            )
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
            gp_id=gp.id,
            block_id=gp.block_id,
            district_id=gp.block.district_id,
            description=description,
            status_id=complaint_status.id,
            public_user_id=user.id,
            mobile_number=user.mobile_number,
            lat=lat,
            long=long,
            location=location,
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
                        filename=file.filename,
                    )

                    # Get the public URL for the uploaded file
                    if s3_service.is_available():
                        # Use S3 URL for database storage
                        media_url = s3_key
                    else:
                        # Fallback to local path
                        media_url = f"/media/complaints/{complaint.id}/{file.filename}"

                    # Create media record
                    media = ComplaintMedia(
                        complaint_id=complaint.id,
                        media_url=media_url,
                        uploaded_by_public_mobile=user.mobile_number,
                        uploaded_by_user_id=None,
                    )
                    db.add(media)
                    media_urls.append(media_url)
                    print(f"Uploaded file to {media_url}")

                except HTTPException:
                    # If S3 upload fails, continue without media
                    # In production, you might want to handle this differently
                    continue

        if media_urls:
            await db.commit()
            # Refresh complaint to get the latest media records
            await db.refresh(complaint)

            # Fetch media details after commit
            media_result = await db.execute(select(ComplaintMedia).where(ComplaintMedia.complaint_id == complaint.id))
            media_records = media_result.scalars().all()

            media_details = [
                MediaResponse(id=media.id, media_url=media.media_url, uploaded_at=media.uploaded_at)
                for media in media_records
            ]
        else:
            media_details = []

        # Send notification to workers in the village (async, non-blocking)

        try:
            # Create a ComplaintAssignment entry and notify workers
            # Get the worker of the village (there should be only one assigned)
            contractor = (await db.execute(select(Contractor).where(Contractor.gp_id == gp_id))).scalar_one_or_none()
            if contractor:
                # Get the user ID of the village contractor
                authority_users = (
                    await db.execute(select(User).where(User.gp_id == contractor.gp_id))
                ).scalars()
                # Filter the one that contains contractor in username
                authority_user = next(
                    (user for user in authority_users if "contractor" in user.username.lower()), None
                )
                if authority_user:
                    # TODO: Create ComplaintAssignment entry if needed
                    pass
            else:
                logging.warning("No contractor found for village ID %s", gp_id)
            await notify_workers_on_new_complaint(db, complaint)
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Log error but don't fail the request
            traceback.print_exc()

            logging.error("Failed to send FCM notification: %s", e)

        return ComplaintResponse(
            id=complaint.id,
            description=complaint.description,
            mobile_number=complaint.mobile_number,
            status_name=complaint_status.name,
            village_name=gp.name,
            block_name=gp.block.name,
            district_name=gp.district.name,
            created_at=complaint.created_at,
            updated_at=complaint.updated_at,
            lat=complaint.lat,
            long=complaint.long,
            media_urls=media_urls,
            media=media_details,
            location=complaint.location,
            resolved_at=complaint.resolved_at,
            verified_at=complaint.verified_at,
            closed_at=complaint.closed_at,
        )

    except HTTPException:
        raise

    except Exception as e:
        logging.error("Error creating complaint with media: %s", e)
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create complaint",
        ) from e


@router.post("/{complaint_id}/comments")
async def comment_on_complaint(
    complaint_id: int,
    comment: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user_token: str = Header(..., description="Public user token"),
) -> Dict[str, Any]:
    """Add a comment to a complaint (Public access)."""
    # Check if complaint exists
    # Get the user id using the token
    auth_service = AuthService(db)
    public_user = await auth_service.get_public_user_by_token(user_token)
    if not public_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing user token",
        )
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    # Create new comment
    new_comment = ComplaintComment(
        complaint_id=complaint.id,
        comment=comment,
        user_id=None,  # Public users are not logged in
        mobile_number=public_user.mobile_number,
    )
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)

    # If photo is provided, upload to S3/MinIO and associate with comment
    s3_key: Optional[str] = None

    return {
        "id": new_comment.id,
        "complaint_id": new_comment.complaint_id,
        "comment": new_comment.comment,
        "created_at": new_comment.commented_at,
        "photo_url": s3_key,  # URL or key of the uploaded photo
    }


@router.post("/{complaint_id}/media")
async def upload_complaint_media(
    complaint_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    token: str = Header(..., description="Public user token"),
) -> Dict[str, Any]:
    """Upload media (image) for a complaint (Public access)."""
    # Check if complaint exists
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    # Get the user id using the token
    public_user_token = (
        await db.execute(select(PublicUserToken).where(PublicUserToken.token == token))
    ).scalar_one_or_none()
    if not public_user_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing user token",
        )
    public_user_id = public_user_token.public_user_id
    public_user = (await db.execute(select(PublicUser).where(PublicUser.id == public_user_id))).scalar_one_or_none()

    # Validate file type
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    _, file_extension = os.path.splitext(file.filename.lower())  # type: ignore

    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")

    # Upload file to S3/MinIO
    s3_key = f"complaints/{complaint_id}/{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{file.filename}"

    try:
        await s3_service.upload_file(
            file=file.file,  # type: ignore
            folder=f"complaints/{complaint_id}",
            filename=f"{uuid.uuid4()}-{file.filename}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}",
        ) from e

    # Optionally, you can save the S3 key or URL in the database associated with the complaint
    # For simplicity, we just return the S3 key here
    # Save a DB entry as well
    new_media = ComplaintMedia(
        complaint_id=complaint.id,
        media_url=s3_key,
        uploaded_by_public_mobile=public_user.mobile_number,  # type: ignore
        uploaded_by_user_id=None,
    )
    db.add(new_media)
    await db.commit()
    await db.refresh(new_media)

    return {
        "complaint_id": complaint.id,
        "file_name": file.filename,
        "s3_key": s3_key,
        "content_type": file.content_type,
        "uploaded_at": datetime.now(timezone.utc),
    }


@router.post("/{complaint_id}/close", response_model=ComplaintResponse)
async def close_complaint(
    complaint_id: int,
    resolution: str,
    db: AsyncSession = Depends(get_db),
    user_token: str = Header(..., description="Public user token"),
):
    """Close a complaint (User who created the complaint only)."""
    complaint = await ComplaintService(db).get_complaint_by_id(complaint_id)
    # complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Check if the public user is the one who created the complaint
    auth_service = AuthService(db)
    public_user = await auth_service.get_public_user_by_token(user_token)
    assert public_user is not None, "Public user should be valid here"
    if complaint.public_user_id != public_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only close your own complaints",
        )
    closed_status = await db.execute(select(ComplaintStatus).where(ComplaintStatus.name == "CLOSED"))
    closed_status = closed_status.scalar_one_or_none()
    if not closed_status:
        closed_status = ComplaintStatus(name="CLOSED", description="Complaint has been verified and resolved")
        db.add(closed_status)
        await db.commit()
        await db.refresh(closed_status)
    print(closed_status)
    complaint.status_id = closed_status.id  # type: ignore
    complaint.closed_at = datetime.now(tz=timezone.utc)
    # Add a new comment indicating resolution
    if not public_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing user token",
        )
    resolution_comment = ComplaintComment(
        complaint_id=complaint.id,
        comment=resolution,
        user_id=None,  # Assuming admin user ID is not tracked here
        mobile_number=public_user.mobile_number,  # type: ignore
    )
    db.add(resolution_comment)
    db.add(complaint)
    await db.commit()
    await db.refresh(complaint)

    return ComplaintResponse(
        id=complaint.id,
        description=complaint.description,
        mobile_number=complaint.mobile_number,
        status_name=closed_status.name,
        village_name="",  # Could be fetched if needed
        block_name="",
        district_name="",
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
        lat=complaint.lat,
        long=complaint.long,
        media_urls=[],  # Could be fetched if needed
        media=[],
        location=complaint.location,
        resolved_at=complaint.resolved_at,
        verified_at=complaint.verified_at,
        closed_at=complaint.closed_at,
        comments=[  # type: ignore
            ComplaintCommentResponse(
                id=comment.id,
                complaint_id=comment.complaint_id,
                comment=comment.comment,
                commented_at=comment.commented_at,
                user_name=comment.user.username if comment.user else "Public User",
            ) for comment in complaint.comments
        ],
    )
