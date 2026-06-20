"""Controller for managing circulars."""
import json
from typing import List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db

from auth_utils import require_admin_or_smd
from models.database.auth import User
from services.s3_service import s3_service
from services.circular import CircularService
from models.requests.circular import CreateCircularRequest, CircularUpdateRequest
from models.response.circular import CircularResponse
from models.response.deletion import DeletionResponse

router = APIRouter()


@router.post("/", response_model=CircularResponse, status_code=status.HTTP_201_CREATED)
async def create_circular(
    circular_data: str = Form(...),
    pdf: UploadFile = File(...),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_smd),
) -> CircularResponse:
    """
    Create a new circular.
    Only accessible by Admin, Superadmin, and SMD.
    """
    try:
        data_dict = json.loads(circular_data)
        request = CreateCircularRequest(**data_dict)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid circular data: {str(e)}"
        )

    # Validate PDF content type
    if not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file must be a PDF."
        )

    # Upload PDF and optional Image
    pdf_url = await s3_service.upload_file(pdf, folder="circulars/pdfs")
    image_url = None
    if image:
        image_url = await s3_service.upload_file(image, folder="circulars/images")

    service = CircularService(db)
    circular = await service.create_circular(
        title=request.title,
        description=request.description,
        pdf_url=pdf_url,
        image_url=image_url,
        start_date=request.start_date,
        end_date=request.end_date,
    )
    return circular


@router.get("/{circular_id}", response_model=CircularResponse)
async def get_circular(
    circular_id: int,
    db: AsyncSession = Depends(get_db),
) -> CircularResponse:
    """Get circular details by ID."""
    service = CircularService(db)
    circular = await service.get_circular_by_id(circular_id)
    if not circular:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Circular not found."
        )
    return circular


@router.get("/", response_model=List[CircularResponse])
async def list_circulars(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[CircularResponse]:
    """List all circulars (newest first)."""
    service = CircularService(db)
    circulars = await service.get_all_circulars(skip=skip, limit=limit)
    return circulars


@router.put("/{circular_id}", response_model=CircularResponse)
async def update_circular(
    circular_id: int,
    circular_data: str = Form(...),
    pdf: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_smd),
) -> CircularResponse:
    """
    Update an existing circular.
    Only accessible by Admin, Superadmin, and SMD.
    """
    service = CircularService(db)
    circular = await service.get_circular_by_id(circular_id)
    if not circular:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Circular not found."
        )

    try:
        data_dict = json.loads(circular_data)
        request = CircularUpdateRequest(**data_dict)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid circular update data: {str(e)}"
        )

    # If new PDF uploaded, validate and replace
    pdf_url = None
    if pdf:
        if not pdf.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file must be a PDF."
            )
        pdf_url = await s3_service.upload_file(pdf, folder="circulars/pdfs")

    # If new image uploaded, replace
    image_url = None
    if image:
        image_url = await s3_service.upload_file(image, folder="circulars/images")

    updated_circular = await service.update_circular(
        circular_id=circular_id,
        title=request.title,
        description=request.description,
        pdf_url=pdf_url,
        image_url=image_url,
        start_date=request.start_date,
        end_date=request.end_date,
    )
    return updated_circular


@router.delete("/{circular_id}", response_model=DeletionResponse)
async def delete_circular(
    circular_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_smd),
) -> DeletionResponse:
    """
    Delete a circular by its ID.
    Only accessible by Admin, Superadmin, and SMD.
    """
    service = CircularService(db)
    circular = await service.get_circular_by_id(circular_id)
    if not circular:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Circular not found."
        )

    await service.delete_circular(circular_id)
    return DeletionResponse(message="Circular deleted successfully")
