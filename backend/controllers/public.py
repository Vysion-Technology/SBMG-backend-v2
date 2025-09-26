from models.database.complaint import ComplaintMedia

from typing import List, Optional
from datetime import datetime
import os
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from models.database.auth import PublicUser, PublicUserToken
from database import get_db
from models.database.geography import District, Block, Village
from models.database.complaint import (
    ComplaintComment,
    ComplaintType,
    Complaint,
    ComplaintStatus,
)
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


class ComplaintStatusResponse(BaseModel):
    id: int
    status_name: str
    updated_at: Optional[datetime]


# Public endpoints (no authentication required)
@router.get("/districts", response_model=List[DistrictResponse])
async def get_districts(db: AsyncSession = Depends(get_db)):
    """Get all districts (Public access)."""
    result = await db.execute(select(District))
    districts = result.scalars().all()

    return [
        DistrictResponse(
            id=district.id, name=district.name, description=district.description
        )
        for district in districts
    ]


@router.get("/blocks", response_model=List[BlockResponse])
async def get_blocks(
    district_id: Optional[int] = Query(
        None, description="Filter blocks by district ID"
    ),
    db: AsyncSession = Depends(get_db),
):
    """Get blocks, optionally filtered by district (Public access)."""
    query = select(Block)

    if district_id:
        query = query.where(Block.district_id == district_id)

    result = await db.execute(query)
    blocks = result.scalars().all()

    return [
        BlockResponse(
            id=block.id,
            name=block.name,
            description=block.description,
            district_id=block.district_id,
        )
        for block in blocks
    ]


@router.get("/villages", response_model=List[VillageResponse])
async def get_villages(
    block_id: Optional[int] = Query(None, description="Filter villages by block ID"),
    district_id: Optional[int] = Query(
        None, description="Filter villages by district ID"
    ),
    db: AsyncSession = Depends(get_db),
):
    """Get villages, optionally filtered by block or district (Public access)."""
    query = select(Village)

    if block_id:
        query = query.where(Village.block_id == block_id)
    elif district_id:
        query = query.where(Village.district_id == district_id)

    result = await db.execute(query)
    villages = result.scalars().all()

    return [
        VillageResponse(
            id=village.id,
            name=village.name,
            description=village.description,
            block_id=village.block_id,
            district_id=village.district_id,
        )
        for village in villages
    ]


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


@router.get("/complaints/{complaint_id}/status", response_model=ComplaintStatusResponse)
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found"
        )

    complaint, complaint_status = complaint_data

    return ComplaintStatusResponse(
        id=complaint.id,
        status_name=complaint_status.name,
        updated_at=complaint.updated_at,
    )


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

            from fastapi.responses import Response

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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Check if file exists
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )

    # Return the file
    return FileResponse(
        path=full_path,
        headers={"Cache-Control": "public, max-age=3600"},  # Cache for 1 hour
    )


