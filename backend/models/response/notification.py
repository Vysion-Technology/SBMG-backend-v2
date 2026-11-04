"""Response models for in-app notifications."""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class InAppNotificationItem(BaseModel):
    """Single in-app notification item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    message: str
    category: str
    priority: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    action_url: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime


class NotificationListResponse(BaseModel):
    """Paginated list of in-app notifications."""

    items: List[InAppNotificationItem]
    total: int
    unread_count: int
    page: int
    page_size: int


class UnreadCountResponse(BaseModel):
    """Unread count for notification badge."""

    unread_count: int


class MarkReadResponse(BaseModel):
    """Response after marking notifications as read."""

    success: bool
    marked_count: int
