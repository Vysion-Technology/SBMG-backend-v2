"""Controller module for managing notices."""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db

from models.database.auth import User
from models.requests.notice import CreateNoticeRequest
from models.response.notice import (
    NoticeDetailResponse,
)

from auth_utils import require_staff_role

from services.permission import PermissionService
from services.user import UserService
from services.notice import NoticeService


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/", response_model=NoticeDetailResponse, status_code=status.HTTP_201_CREATED
)
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
    notice_service = NoticeService(db)
    user_service = UserService(db)
    perm_service = PermissionService(db)

    receivers = await user_service.get_users_by_geo(
        district_id=request.district_id,
        block_id=request.block_id,
        village_id=request.village_id,
    )
    if not receivers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No user found for the specified location",
        )

    assert perm_service.valid_sender_receiver_pair(current_user, receivers[0]), (
        "Insufficient permissions to send notice to the selected location"
    )

    # Create the notice
    notices = [
        await notice_service.create_notice(
            sender_id=current_user.id,
            receiver_id=receiver_position.id,
            title=request.title,
            text=request.text,
        )
        for receiver_position in receivers
    ]
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


@router.get("/sent", response_model=List[NoticeDetailResponse])
async def get_sent_notices(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """Get all notices sent by the current user."""
    notices = await NoticeService(db).get_notices_sent_by_user(
        sender_id=current_user.id, skip=skip, limit=limit
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


@router.get("/received", response_model=List[NoticeDetailResponse])
async def get_received_notices(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """Get all notices received by the current user."""
    notices = await NoticeService(db).get_notices_received_by_user(
        receiver_id=current_user.id, skip=skip, limit=limit
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
    current_user: User = Depends(require_staff_role),
):
    """Get a specific notice by ID."""
    notice = await NoticeService(db).get_notice_by_id(notice_id=notice_id)
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found"
        )
    if (
        not notice.sender_id == current_user.id
        and not notice.receiver_id == current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view notices you have sent or received",
        )
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found"
        )
    if notice.sender_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete notices you have sent",
        )
    await svc.delete_notice(notice_id)


@router.post("/media", status_code=status.HTTP_201_CREATED)
async def upload_notice_media(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
) -> None:
    """Upload media file for a notice and get the URL."""
    raise NotImplementedError("This endpoint is not yet implemented.")  # type: ignore
