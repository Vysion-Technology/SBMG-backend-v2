"""Service layer for managing events and their associated media."""

from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from sqlalchemy import delete, insert, select, update

from models.database.event import Event, EventMedia, EventBookmark


class EventService:
    """Service class for managing events and their media."""

    def __init__(self, db: AsyncSession):
        """Initialize EventService with a database session."""
        self.db = db

    async def get_event_by_id(self, event_id: int) -> Optional[Event]:
        """Retrieve an event by its ID."""
        result = await self.db.execute(
            select(Event).options(selectinload(Event.media)).where(Event.id == event_id),
        )
        event = result.scalar_one_or_none()
        return event

    async def get_all_events(
        self,
        skip: int = 0,
        limit: int = 100,
        active: bool = True,
    ) -> list[Event]:
        """Retrieve all events with optional pagination and active filter."""
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
        """Create a new event."""
        event = (await self.db.execute(insert(Event).values(
            name=name,
            description=description,
            start_time=start_time,
            end_time=end_time,
            active=True,
        ).returning(Event))).scalar_one()
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
            await self.db.execute(
                update(Event).where(Event.id == event_id).values(**update_data),
            )
            await self.db.commit()

        # Always return the updated event with media relationship loaded
        return await self.get_event_by_id(event_id)

    async def add_event_media(self, event_id: int, media_url: str) -> None:
        """Add media to an event."""
        await self.db.execute(
            insert(EventMedia).values(event_id=event_id, media_url=media_url),
        )
        await self.db.commit()

    async def remove_event_media(self, event_media_id: int) -> None:
        """Remove event media by its ID."""
        await self.db.execute(
            delete(EventMedia).where(EventMedia.id == event_media_id),
        )
        await self.db.commit()

    async def delete_event(self, event_id: int) -> None:
        """Delete an event by its ID."""
        # Delete associated media first due to foreign key constraint
        await self.db.execute(
            delete(EventMedia).where(EventMedia.event_id == event_id),
        )
        await self.db.execute(
            delete(Event).where(Event.id == event_id),
        )
        await self.db.commit()

    async def add_bookmark(
        self,
        event_id: int,
        user_id: Optional[int] = None,
        public_user_id: Optional[int] = None,
    ) -> EventBookmark:
        """Add a bookmark for an event."""
        bookmark = EventBookmark(
            event_id=event_id, user_id=user_id, public_user_id=public_user_id
        )
        self.db.add(bookmark)
        try:
            await self.db.commit()
            await self.db.refresh(bookmark)
            return bookmark
        except IntegrityError:
            await self.db.rollback()
            # Bookmark already exists, return existing one
            query = select(EventBookmark).where(EventBookmark.event_id == event_id)
            if user_id:
                query = query.where(EventBookmark.user_id == user_id)
            if public_user_id:
                query = query.where(EventBookmark.public_user_id == public_user_id)

            result = await self.db.execute(query)
            return result.scalar_one()

    async def remove_bookmark(
        self,
        event_id: int,
        user_id: Optional[int] = None,
        public_user_id: Optional[int] = None,
    ) -> bool:
        """Remove a bookmark for an event. Returns True if deleted, False if not found."""
        query = delete(EventBookmark).where(EventBookmark.event_id == event_id)

        if user_id:
            query = query.where(EventBookmark.user_id == user_id)
        if public_user_id:
            query = query.where(EventBookmark.public_user_id == public_user_id)

        result = await self.db.execute(query.returning(EventBookmark.id))
        await self.db.commit()
        return result.scalar_one_or_none() is not None

    async def get_bookmarked_events(
        self,
        user_id: Optional[int] = None,
        public_user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Event]:
        """Get all bookmarked events for a user."""
        query = (
            select(Event)
            .join(EventBookmark, Event.id == EventBookmark.event_id)
            .options(selectinload(Event.media))
            .offset(skip)
            .limit(limit)
        )

        if user_id:
            query = query.where(EventBookmark.user_id == user_id)
        if public_user_id:
            query = query.where(EventBookmark.public_user_id == public_user_id)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def is_bookmarked(
        self,
        event_id: int,
        user_id: Optional[int] = None,
        public_user_id: Optional[int] = None,
    ) -> bool:
        """Check if an event is bookmarked by a user."""
        query = select(EventBookmark).where(EventBookmark.event_id == event_id)
        if user_id:
            query = query.where(EventBookmark.user_id == user_id)
        if public_user_id:
            query = query.where(EventBookmark.public_user_id == public_user_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
