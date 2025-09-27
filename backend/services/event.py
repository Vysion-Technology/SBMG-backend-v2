from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sqlalchemy import delete, select, update

from models.database.event import Event, EventMedia

class EventService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_event_by_id(self, event_id: int) -> Optional[Event]:
        result = await self.db.execute(select(Event).options(selectinload(Event.media)).where(Event.id == event_id))
        event = result.scalar_one_or_none()
        return event

    async def get_all_events(
        self,
        skip: int = 0,
        limit: int = 100,
        active: bool = True,
    ) -> list[Event]:
        query = select(Event).options(selectinload(Event.media)).offset(skip).limit(limit)
        if active:
            query = query.where(Event.active)
        result = await self.db.execute(query)
        events = result.scalars().all()
        return list(events)

    async def create_event(
        self,
        name: str,
        description: Optional[str],
        start_time: datetime,
        end_time: datetime,
    ) -> Event:
        event = Event(
            name=name,
            description=description,
            start_time=start_time,
            end_time=end_time,
            active=True,
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event, ["media"])
        return event

    async def update_event(
        self,
        event_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        active: Optional[bool] = None,
    ) -> Optional[Event]:
        """Update event details."""
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if start_time is not None:
            update_data["start_time"] = start_time
        if end_time is not None:
            update_data["end_time"] = end_time
        if active is not None:
            update_data["active"] = active

        if update_data:
            await self.db.execute(update(Event).where(Event.id == event_id).values(**update_data))
            await self.db.commit()

        # Always return the updated event with media relationship loaded
        return await self.get_event_by_id(event_id)

    async def add_event_media(self, event_id: int, media_url: str) -> None:
        # Create a new DB object for EventMedia

        event_media = EventMedia(event_id=event_id, media_url=media_url)
        self.db.add(event_media)
        await self.db.commit()

    async def remove_event_media(self, event_id: int, event_media_id: int) -> None:
        # Remove the DB object for EventMedia

        await self.db.execute(delete(EventMedia).where(EventMedia.id == event_media_id))