"""Controller module for managing notices."""

import asyncio
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db

from models.database.auth import User
from models.requests.notice import CreateNoticeRequest, CreateNoticeTypeRequest
from models.response.notice import (
    NoticeDetailResponse,
    NoticeTypeResponse,
)

from auth_utils import require_admin, require_staff_role

from services.auth import AuthService
from services.position_holder import PositionHolderService
from services.notice import NoticeService
from services.s3_service import S3Service


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=NoticeDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_notice(
    request: CreateNoticeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
) -> NoticeDetailResponse:
    """
    Create a new notice.
    Select district (required), block (optional), and village (optional).
    The system will find the appropriate position holder for that location.
    """
    try:
        notice_service = NoticeService(db)
        auth_service = AuthService(db)

        # Create the notice
        sender_position, receiver_position = await asyncio.gather(
            auth_service.get_current_position_holder(
                current_user.district_id,
                current_user.block_id,
                current_user.gp_id,
            ),
            auth_service.get_current_position_holder(
                district_id=request.district_id,
                block_id=request.block_id,
                gp_id=request.gp_id,
            ),
        )

        assert sender_position, "Sender position holder not found"
        assert receiver_position, "Receiver position holder not found"

        notice = await notice_service.create_notice(
            notice_type_id=request.notice_type_id,
            sender_id=sender_position.id,
            receiver_id=receiver_position.id,
            title=request.title,
            text=request.text,
        )
        return NoticeDetailResponse(
            id=notice.id,
            sender_id=notice.sender_id,
            receiver_id=notice.receiver_id,
            title=notice.title,
            date=notice.date,  # type: ignore
            text=notice.text,
        )
    except HTTPException as e:
        logger.error("Database error while creating notice: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

@router.post("/types")
async def create_notice_type(
    notice_create: CreateNoticeTypeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> NoticeTypeResponse:
    """Create a new notice type."""
    assert current_user, "Authentication required"
    notice_type = await NoticeService(db).create_notice_type(
        name=notice_create.name,
        description=notice_create.description,
    )
    return NoticeTypeResponse(
        id=notice_type.id,
        name=notice_type.name,
        description=notice_type.description,
    )


@router.get("/sent", response_model=List[NoticeDetailResponse])
async def get_sent_notices(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """Get all notices sent by the current user."""
    current_user_position_ids = await PositionHolderService(db).get_position_holder_ids_by_user(user_id=current_user.id)

    notices = await NoticeService(db).get_notices_sent_by_user(
        sender_ids=current_user_position_ids, skip=skip, limit=limit
    )
    return [
        NoticeDetailResponse(
            id=notice.id,
            sender_id=notice.sender_id,
            receiver_id=notice.receiver_id,
            title=notice.title,
            date=notice.date,  # type: ignore
            text=notice.text,
            sender=notice.sender,
            receiver=notice.receiver,
        )
        for notice in notices
    ]


@router.get("/received", response_model=List[NoticeDetailResponse])
async def get_received_notices(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """Get all notices received by the current user."""
    # Position Holder IDs of the current user
    current_user_position_ids = await PositionHolderService(db).get_position_holder_ids_by_user(user_id=current_user.id)
    print(current_user_position_ids)
    notices = await NoticeService(db).get_notices_received_by_user(
        receiver_ids=current_user_position_ids, skip=skip, limit=limit
    )
    return [
        NoticeDetailResponse(
            id=notice.id,
            sender_id=notice.sender_id,
            receiver_id=notice.receiver_id,
            title=notice.title,
            date=notice.date,  # type: ignore
            text=notice.text,
        )
        for notice in notices
    ]


@router.get("/{notice_id}", response_model=NoticeDetailResponse)
async def get_notice_by_id(
    notice_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific notice by ID."""
    notice = await NoticeService(db).get_notice_by_id(notice_id=notice_id)
    if not notice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found")
    return NoticeDetailResponse(
        id=notice.id,
        sender_id=notice.sender_id,
        receiver_id=notice.receiver_id,
        title=notice.title,
        date=notice.date,  # type: ignore
        text=notice.text,
    )


@router.delete("/{notice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notice(
    notice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
) -> None:
    """Delete a notice. Only the sender can delete their notices."""
    svc = NoticeService(db)
    notice = await svc.get_notice_by_id(notice_id)
    if not notice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found")
    if notice.sender_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete notices you have sent",
        )
    await svc.delete_notice(notice_id)


@router.post("{notice_id}/media", status_code=status.HTTP_201_CREATED)
async def upload_notice_media(
    notice_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
) -> NoticeDetailResponse:
    """Upload media file for a notice and get the URL."""
    assert current_user, "Authentication required"
    s3_service = S3Service()
    file_url = await s3_service.upload_file(file, folder="notices")
    await NoticeService(db).upload_notice_media(notice_id=notice_id, media_url=file_url)
    notice = await NoticeService(db).get_notice_by_id(notice_id)
    if not notice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found")
    return NoticeDetailResponse(
        id=notice.id,
        sender_id=notice.sender_id,
        receiver_id=notice.receiver_id,
        title=notice.title,
        date=notice.date,  # type: ignore
        text=notice.text,
        media=[media for media in notice.media],
    )
