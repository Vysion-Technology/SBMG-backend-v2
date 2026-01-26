"""Event Controller"""

from datetime import timezone
from typing import List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from models.database.auth import User, PublicUser
from controllers.auth import get_current_any_user

from sqlalchemy.ext.asyncio import AsyncSession

from auth_utils import require_admin
from database import get_db
from models.requests.event import CreateEventRequest, EventUpdateRequest
from models.response.event import EventResponse
from models.response.deletion import DeletionResponse

from services.event import EventService
from services.s3_service import s3_service

router = APIRouter()


@router.post("/", response_model=EventResponse)
async def create_event(
    event_create_req: CreateEventRequest,
    is_admin: bool = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> EventResponse:
    """Create a new event."""
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    assert event_create_req.name is not None, "Name is required"
    assert event_create_req.start_time is not None, "Start time is required"
    assert event_create_req.end_time is not None, "End time is required"

    service = EventService(db)
    if not event_create_req.start_time.tzinfo:
        event_create_req.start_time = event_create_req.start_time.replace(tzinfo=timezone.utc)
    if not event_create_req.end_time.tzinfo:
        event_create_req.end_time = event_create_req.end_time.replace(tzinfo=timezone.utc)
    event = await service.create_event(
        event_create_req.name,
        event_create_req.description,
        event_create_req.start_time,
        event_create_req.end_time,
    )
    print("Created Event:")
    print(event)

    # Refresh the event with media relationship loaded
    await db.refresh(event, ["media"])

    return event


@router.get("/{event_id}", response_model=Optional[EventResponse])
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
) -> Optional[EventResponse]:
    """Get an event by ID."""
    service = EventService(db)
    event = await service.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("/{event_id}/media", response_model=Optional[EventResponse])
async def add_event_media(
    event_id: int,
    media: UploadFile = File(...),
    is_admin: bool = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Optional[EventResponse]:
    """Add media to an event."""
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    service = EventService(db)
    event = await service.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Upload media to S3/MinIO and get the URL
    media_url = await s3_service.upload_file(media, f"events/{event_id}")

    await service.add_event_media(event_id, media_url)
    await db.refresh(event, ["media"])
    return event


@router.delete("/{event_id}/media/{event_media_id}", response_model=Optional[EventResponse])
async def remove_event_media(
    event_id: int,
    event_media_id: int,
    is_admin: bool = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Optional[EventResponse]:
    """Remove media from an event."""
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    service = EventService(db)
    event = await service.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    await service.remove_event_media(event_media_id)
    await db.refresh(event, ["media"])
    return event


@router.get("/", response_model=List[EventResponse])
async def list_events(
    skip: int = 0,
    limit: int = 100,
    active: bool = True,
    db: AsyncSession = Depends(get_db),
) -> List[EventResponse]:
    """List all events with pagination."""
    if limit > 1000:
        raise HTTPException(status_code=400, detail="Limit exceeds maximum of 100.")

    service = EventService(db)
    events = await service.get_all_events(skip=skip, limit=limit, active=active)
    return [
        EventResponse(
            id=event.id,
            name=event.name,
            description=event.description,
            start_time=event.start_time,
            end_time=event.end_time,
            active=event.active,
            media=event.media,
        )
        for event in events
    ]


@router.put("/{event_id}", response_model=Optional[EventResponse])
async def update_event(
    event_id: int,
    event_update: EventUpdateRequest,
    is_admin: bool = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Optional[EventResponse]:
    """Update an event."""
    name = event_update.name
    description = event_update.description
    start_time = event_update.start_time
    end_time = event_update.end_time
    active = event_update.active
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    service = EventService(db)
    event = await service.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    updated_event = await service.update_event(
        event_id,
        name=name,
        description=description,
        start_time=start_time,
        end_time=end_time,
        active=active,
    )
    return updated_event


@router.delete("/{event_id}", response_model=DeletionResponse, status_code=200)
async def delete_event(
    event_id: int,
    is_admin: bool = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> DeletionResponse:
    """Delete an event."""
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    service = EventService(db)
    event = await service.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    await service.delete_event(event_id)
    return DeletionResponse(message="Event deleted successfully")


@router.post("/{event_id}/bookmark", status_code=201)
async def add_event_bookmark(
    event_id: int,
    current_user: Union[User, PublicUser] = Depends(get_current_any_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a bookmark for an event."""
    service = EventService(db)
    event = await service.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    user_id = current_user.id if isinstance(current_user, User) else None
    public_user_id = current_user.id if isinstance(current_user, PublicUser) else None

    await service.add_bookmark(event_id, user_id=user_id, public_user_id=public_user_id)
    return {"message": "Event bookmarked successfully"}


@router.delete("/{event_id}/bookmark", status_code=200)
async def remove_event_bookmark(
    event_id: int,
    current_user: Union[User, PublicUser] = Depends(get_current_any_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a bookmark for an event."""
    service = EventService(db)

    user_id = current_user.id if isinstance(current_user, User) else None
    public_user_id = current_user.id if isinstance(current_user, PublicUser) else None

    deleted = await service.remove_bookmark(
        event_id, user_id=user_id, public_user_id=public_user_id
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return {"message": "Bookmark removed successfully"}


@router.get("/bookmarked/list", response_model=List[EventResponse])
async def list_bookmarked_events(
    skip: int = 0,
    limit: int = 100,
    current_user: Union[User, PublicUser] = Depends(get_current_any_user),
    db: AsyncSession = Depends(get_db),
) -> List[EventResponse]:
    """List all bookmarked events for the current user."""
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100")

    service = EventService(db)

    user_id = current_user.id if isinstance(current_user, User) else None
    public_user_id = current_user.id if isinstance(current_user, PublicUser) else None

    events = await service.get_bookmarked_events(
        user_id=user_id, public_user_id=public_user_id, skip=skip, limit=limit
    )
    return [
        EventResponse(
            id=event.id,
            name=event.name,
            description=event.description,
            start_time=event.start_time,
            end_time=event.end_time,
            active=event.active,
            media=event.media,
        )
        for event in events
    ]
