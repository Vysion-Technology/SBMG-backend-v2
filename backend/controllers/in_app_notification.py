"""Controller for in-app notifications."""

import logging
from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.database.auth import User, PublicUser
from controllers.auth import get_current_any_user
from auth_utils import require_admin
from services.in_app_notification_service import InAppNotificationService
from models.response.notification import (
    NotificationListResponse,
    UnreadCountResponse,
    MarkReadResponse,
)
from middleware.xss_protection import XSSProtectionRoute

logger = logging.getLogger(__name__)

router = APIRouter(route_class=XSSProtectionRoute)


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    unread_only: bool = Query(False, description="Filter for unread notifications only"),
    category: Optional[str] = Query(None, description="Filter by category (NOTICE, SLA, EVENT, SCHEME)"),
    current_user: Union[User, PublicUser] = Depends(get_current_any_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationListResponse:
    """
    List in-app notifications for the logged in user (authority staff or public citizen).
    Returns direct notifications addressed to the user as well as global broadcast alerts.
    """
    service = InAppNotificationService(db)
    skip = (page - 1) * page_size
    items, total, unread_count = await service.get_user_notifications(
        user=current_user,
        skip=skip,
        limit=page_size,
        unread_only=unread_only,
        category=category,
    )

    return NotificationListResponse(
        items=items,
        total=total,
        unread_count=unread_count,
        page=page,
        page_size=page_size,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_notification_count(
    current_user: Union[User, PublicUser] = Depends(get_current_any_user),
    db: AsyncSession = Depends(get_db),
) -> UnreadCountResponse:
    """
    Get the unread notification count for the badge icon in the navigation bar.
    """
    service = InAppNotificationService(db)
    count = await service.get_unread_count(user=current_user)
    return UnreadCountResponse(unread_count=count)


@router.patch("/{notification_id}/read", response_model=MarkReadResponse)
async def mark_single_notification_read(
    notification_id: int = Path(..., description="ID of the notification to mark read"),
    current_user: Union[User, PublicUser] = Depends(get_current_any_user),
    db: AsyncSession = Depends(get_db),
) -> MarkReadResponse:
    """
    Mark an individual notification as read.
    """
    service = InAppNotificationService(db)
    success = await service.mark_notification_as_read(
        user=current_user, notification_id=notification_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied",
        )
    return MarkReadResponse(success=True, marked_count=1)


@router.patch("/mark-all-read", response_model=MarkReadResponse)
async def mark_all_notifications_read(
    current_user: Union[User, PublicUser] = Depends(get_current_any_user),
    db: AsyncSession = Depends(get_db),
) -> MarkReadResponse:
    """
    Mark all unread notifications as read for the logged in user.
    """
    service = InAppNotificationService(db)
    marked_count = await service.mark_all_as_read(user=current_user)
    return MarkReadResponse(success=True, marked_count=marked_count)


@router.post("/sync-triggers", response_model=dict)
async def trigger_event_and_scheme_checks(
    _: bool = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Admin utility to evaluate active/expiring events and schemes and dispatch broadcast notifications.
    """
    service = InAppNotificationService(db)
    events_triggered = await service.check_and_trigger_event_notifications()
    schemes_triggered = await service.check_and_trigger_scheme_notifications()
    return {
        "success": True,
        "events_triggered": events_triggered,
        "schemes_triggered": schemes_triggered,
    }
