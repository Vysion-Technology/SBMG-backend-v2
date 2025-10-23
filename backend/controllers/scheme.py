from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from services.s3_service import s3_service
from database import get_db
from models.response.scheme import SchemeResponse
from auth_utils import require_admin
from services.scheme import SchemeService


router = APIRouter()


class CreateSchemeRequest(BaseModel):
    name: str
    description: Optional[str] = None
    eligibility: Optional[str] = None
    benefits: Optional[str] = None
    start_time: datetime
    end_time: datetime


@router.post("/", response_model=SchemeResponse)
async def create_scheme(
    scheme: CreateSchemeRequest,
    is_admin: bool = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> SchemeResponse:
    """Create a new scheme."""
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    name = scheme.name
    description = scheme.description
    eligibility = scheme.eligibility
    benefits = scheme.benefits
    start_time = scheme.start_time
    end_time = scheme.end_time

    assert name is not None, "Name is required"
    assert start_time is not None, "Start time is required"
    assert end_time is not None, "End time is required"

    service = SchemeService(db)
    print("Start Time")
    print(start_time)
    print("End Time")
    print(end_time)
    start_time = start_time.replace(tzinfo=timezone.utc)
    end_time = end_time.replace(tzinfo=timezone.utc)
    scheme = await service.create_scheme(
        name, description, eligibility, benefits, start_time, end_time
    )
    print("Created Scheme:")
    print(scheme)

    # Refresh the scheme with media relationship loaded
    await db.refresh(scheme, ["media"])

    return scheme


@router.get("/{scheme_id}", response_model=Optional[SchemeResponse])
async def get_scheme(
    scheme_id: int, db: AsyncSession = Depends(get_db)
) -> Optional[SchemeResponse]:
    service = SchemeService(db)
    scheme = await service.get_scheme_by_id(scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return scheme


@router.post("/{scheme_id}/media", response_model=Optional[SchemeResponse])
async def add_scheme_media(
    scheme_id: int,
    media: UploadFile = File(...),
    is_admin: bool = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Optional[SchemeResponse]:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    service = SchemeService(db)
    scheme = await service.get_scheme_by_id(scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    # Upload media to S3
    media_url = await s3_service.upload_file(media, f"schemes/{scheme_id}")

    # Add media record to the database
    await service.add_scheme_media(scheme_id, media_url)

    # Refresh the scheme with media relationship loaded
    await db.refresh(scheme, ["media"])

    return scheme


@router.delete("/{scheme_id}/media", response_model=Optional[SchemeResponse])
async def remove_scheme_media(
    scheme_id: int,
    scheme_media_id: int,
    is_admin: bool = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Optional[SchemeResponse]:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    service = SchemeService(db)
    scheme = await service.get_scheme_by_id(scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    await service.remove_scheme_media(scheme_id, scheme_media_id)

    # Refresh the scheme with media relationship loaded
    await db.refresh(scheme, ["media"])

    return scheme


@router.get("/", response_model=List[SchemeResponse])
async def list_schemes(
    skip: int = 0,
    limit: int = 100,
    active: bool = True,
    db: AsyncSession = Depends(get_db),
) -> List[SchemeResponse]:
    service = SchemeService(db)
    schemes = await service.get_all_schemes(skip=skip, limit=limit, active=active)
    return [
        SchemeResponse(
            id=scheme.id,
            name=scheme.name,
            description=scheme.description,
            eligibility=scheme.eligibility,
            benefits=scheme.benefits,
            start_time=scheme.start_time,
            end_time=scheme.end_time,
            active=scheme.active,
            media=[media for media in scheme.media],
        )
        for scheme in schemes
    ]


class SchemeUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    eligibility: Optional[str] = None
    benefits: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    active: Optional[bool] = None


@router.put("/{scheme_id}", response_model=Optional[SchemeResponse])
async def update_scheme(
    scheme_id: int,
    scheme_update: SchemeUpdateRequest,
    is_admin: bool = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Optional[SchemeResponse]:
    """Update scheme details."""
    name = scheme_update.name
    description = scheme_update.description
    eligibility = scheme_update.eligibility
    benefits = scheme_update.benefits
    start_time = scheme_update.start_time
    end_time = scheme_update.end_time
    active = scheme_update.active
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    service = SchemeService(db)
    scheme = await service.get_scheme_by_id(scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    if start_time is not None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time is not None:
        end_time = end_time.replace(tzinfo=timezone.utc)

    updated_scheme = await service.update_scheme(
        scheme_id,
        name=name,
        description=description,
        eligibility=eligibility,
        benefits=benefits,
        start_time=start_time,
        end_time=end_time,
        active=active,
    )
    return updated_scheme
