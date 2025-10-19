"""Public controllers for complaint management system."""

import os
from typing import Optional, List

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import get_db
from models.database.auth import User
from models.database.complaint import (
    Complaint,
    ComplaintComment,
    ComplaintAssignment,
)
from models.database.geography import GramPanchayat, Block
from models.database.complaint import (
    ComplaintType,
)

from models.response.complaint import MediaResponse
from models.response.complaint import (
    ComplaintCommentResponse,
    DetailedComplaintResponse,
)

from services.geography import GeographyService
from services.s3_service import s3_service

router = APIRouter()


# Pydantic models for responses
class DistrictResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]


class BlockResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    district_id: int


class VillageResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    block_id: int
    district_id: int


class ComplaintTypeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]


@router.get("/complaint-types", response_model=List[ComplaintTypeResponse])
async def get_complaint_types(db: AsyncSession = Depends(get_db)):
    """Get all complaint types (Public access)."""
    result = await db.execute(select(ComplaintType))
    complaint_types = result.scalars().all()

    return [
        ComplaintTypeResponse(
            id=complaint_type.id,
            name=complaint_type.name,
            description=complaint_type.description,
        )
        for complaint_type in complaint_types
    ]


@router.get("/media/{file_path:path}")
async def serve_media(file_path: str):
    """Serve media files (images) from S3/MinIO or local media directory."""

    # First try to serve from S3/MinIO if available
    if s3_service.is_available():
        try:
            # Download file from S3/MinIO
            file_content = s3_service.download_file(file_path)

            # Determine content type based on file extension
            content_type = "application/octet-stream"
            if file_path.lower().endswith((".jpg", ".jpeg")):
                content_type = "image/jpeg"
            elif file_path.lower().endswith(".png"):
                content_type = "image/png"
            elif file_path.lower().endswith(".gif"):
                content_type = "image/gif"
            elif file_path.lower().endswith(".webp"):
                content_type = "image/webp"

            return Response(
                content=file_content,
                media_type=content_type,
                headers={"Cache-Control": "public, max-age=3600"},  # Cache for 1 hour
            )
        except HTTPException as e:
            # If file not found in S3, fall through to local file serving
            if e.status_code != 404:
                # Re-raise non-404 errors
                raise e

    # Fallback: serve from local media directory
    media_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "media")
    full_path = os.path.join(media_dir, file_path)

    # Security check: make sure the file is within the media directory
    media_dir = os.path.abspath(media_dir)
    full_path = os.path.abspath(full_path)

    if not full_path.startswith(media_dir):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Check if file exists
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    # Return the file
    return FileResponse(
        path=full_path,
        headers={"Cache-Control": "public, max-age=3600"},  # Cache for 1 hour
    )


@router.get("/{complaint_id}/details", response_model=DetailedComplaintResponse)
async def get_detailed_complaint(complaint_id: int, db: AsyncSession = Depends(get_db)):
    """Get detailed complaint information with all related data (Public access)."""
    # Query complaint with all related data
    result = await db.execute(
        select(Complaint)
        .options(
            selectinload(Complaint.complaint_type),
            selectinload(Complaint.status),
            selectinload(Complaint.village).selectinload(GramPanchayat.block).selectinload(Block.district),
            selectinload(Complaint.media),
            selectinload(Complaint.comments).selectinload(ComplaintComment.user).selectinload(User.positions),
            selectinload(Complaint.assignments).selectinload(ComplaintAssignment.user).selectinload(User.positions),
        )
        .where(Complaint.id == complaint_id)
    )
    complaint = result.scalar_one_or_none()

    geo_service: GeographyService = GeographyService(db)

    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    # Get media URLs and detailed media information
    media_details = [
        MediaResponse(id=media.id, media_url=media.media_url, uploaded_at=media.uploaded_at)
        for media in complaint.media
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

        comments.append(  # type: ignore
            ComplaintCommentResponse(
                id=comment.id,
                complaint_id=comment.complaint_id,
                comment=comment.comment,
                commented_at=comment.commented_at,
                user_name=user_name,
            )
        )

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

    village: GramPanchayat = await geo_service.get_village(complaint.village_id)

    print("Complaint:  ", complaint)

    return DetailedComplaintResponse(
        id=complaint.id,
        description=complaint.description,
        mobile_number=complaint.mobile_number,
        complaint_type_id=complaint.complaint_type_id,
        status_id=complaint.status_id,
        # complaint_type_name=complaint.complaint_type.name,
        # status_name=complaint.status.name,
        village_name=village.name,
        block_name=village.block.name,
        district_name=village.block.district.name,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
        media=media_details,
        comments=comments,  # type: ignore
        assigned_worker=assigned_worker,
        assignment_date=assignment_date,
    )
