from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from services.s3_service import s3_service
from database import get_db
from models.response.event import EventResponse
from auth_utils import require_admin
from services.event import EventService


router = APIRouter()


class CreateEventRequest(BaseModel):
    name: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime


@router.post("/", response_model=EventResponse)
async def create_event(
    event: Optional[CreateEventRequest] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    is_admin: bool = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> EventResponse:
    """Create a new event."""
    name = event.name if event else name
    description = event.description if event else description
    start_time = event.start_time if event else start_time
    end_time = event.end_time if event else end_time
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    assert name is not None, "Name is required"
    assert start_time is not None, "Start time is required"
    assert end_time is not None, "End time is required"

    service = EventService(db)
    print("Start Time")
    print(start_time)
    print("End Time")
    print(end_time)
    start_time = start_time.replace(tzinfo=timezone.utc)
    end_time = end_time.replace(tzinfo=timezone.utc)
    event = await service.create_event(name, description, start_time, end_time)
    print("Created Event:")
    print(event)

    # Refresh the event with media relationship loaded
    await db.refresh(event, ["media"])

    return event


@router.get("/{event_id}", response_model=Optional[EventResponse])
async def get_event(
    event_id: int, db: AsyncSession = Depends(get_db)
) -> Optional[EventResponse]:
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


@router.delete("/{event_id}/media", response_model=Optional[EventResponse])
async def remove_event_media(
    event_id: int,
    event_media_id: int,
    is_admin: bool = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Optional[EventResponse]:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    service = EventService(db)
    event = await service.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    await service.remove_event_media(event_id, event_media_id)
    await db.refresh(event, ["media"])
    return event


@router.get("/", response_model=List[EventResponse])
async def list_events(
    skip: int = 0,
    limit: int = 100,
    active: bool = True,
    db: AsyncSession = Depends(get_db),
) -> List[EventResponse]:
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


class EventUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    active: Optional[bool] = None


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
