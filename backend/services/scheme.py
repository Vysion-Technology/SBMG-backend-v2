"""Service layer for managing schemes and their associated media."""

from datetime import datetime
from typing import Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from models.database.scheme import Scheme, SchemeMedia, SchemeBookmark


class SchemeService:
    """Service layer for managing schemes and their associated media."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_scheme_by_id(self, scheme_id: int) -> Optional[Scheme]:
        """Retrieve a scheme by its ID."""
        result = await self.db.execute(
            select(Scheme).options(selectinload(Scheme.media)).where(Scheme.id == scheme_id),
        )
        scheme = result.scalar_one_or_none()
        return scheme

    async def get_all_schemes(
        self,
        skip: int = 0,
        limit: int = 100,
        active: bool = True,
    ) -> list[Scheme]:
        """Retrieve all schemes, with optional filtering by active status."""
        query = select(Scheme).options(selectinload(Scheme.media)).offset(skip).limit(limit)
        if active:
            query = query.where(Scheme.active)
        result = await self.db.execute(query)
        schemes = result.scalars().all()
        return list(schemes)

    async def create_scheme(
        self,
        name: str,
        description: Optional[str],
        eligibility: Optional[str],
        benefits: Optional[str],
        start_time: datetime,
        end_time: datetime,
    ) -> Scheme:
        """Create a new scheme."""
        scheme = Scheme(
            name=name,
            description=description,
            eligibility=eligibility,
            benefits=benefits,
            start_time=start_time,
            end_time=end_time,
            active=True,
        )
        self.db.add(scheme)
        await self.db.commit()
        await self.db.refresh(scheme, ["media"])
        return scheme

    async def update_scheme(
        self,
        scheme_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        eligibility: Optional[str] = None,
        benefits: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        active: Optional[bool] = None,
    ) -> Optional[Scheme]:
        """Update scheme details."""
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if eligibility is not None:
            update_data["eligibility"] = eligibility
        if benefits is not None:
            update_data["benefits"] = benefits
        if start_time is not None:
            update_data["start_time"] = start_time
        if end_time is not None:
            update_data["end_time"] = end_time
        if active is not None:
            update_data["active"] = active

        if not update_data:
            return await self.get_scheme_by_id(scheme_id)

        await self.db.execute(
            update(Scheme).where(Scheme.id == scheme_id).values(**update_data),
        )
        await self.db.commit()
        scheme = await self.get_scheme_by_id(scheme_id)
        return scheme

    async def add_scheme_media(self, scheme_id: int, media_url: str) -> SchemeMedia:
        """Add media to a scheme."""
        media = SchemeMedia(scheme_id=scheme_id, media_url=media_url)
        self.db.add(media)
        await self.db.commit()
        await self.db.refresh(media)
        return media

    async def remove_scheme_media(self, scheme_id: int, scheme_media_id: int) -> None:
        """Remove media from a scheme."""
        await self.db.execute(
            delete(SchemeMedia)
            .where(SchemeMedia.id == scheme_media_id)
            .where(
                SchemeMedia.scheme_id == scheme_id,
            )
        )
        await self.db.commit()

    async def delete_scheme(self, scheme_id: int) -> None:
        """Delete a scheme by its ID."""
        # Delete associated media first due to foreign key constraint
        await self.db.execute(
            delete(SchemeMedia).where(SchemeMedia.scheme_id == scheme_id),
        )
        await self.db.execute(delete(Scheme).where(Scheme.id == scheme_id))
        await self.db.commit()

    async def add_bookmark(
        self,
        scheme_id: int,
        user_id: Optional[int] = None,
        public_user_id: Optional[int] = None,
    ) -> SchemeBookmark:
        """Add a bookmark for a scheme."""
        bookmark = SchemeBookmark(
            scheme_id=scheme_id, user_id=user_id, public_user_id=public_user_id
        )
        self.db.add(bookmark)
        try:
            await self.db.commit()
            await self.db.refresh(bookmark)
            return bookmark
        except IntegrityError:
            await self.db.rollback()
            # Bookmark already exists, return existing one
            query = select(SchemeBookmark).where(SchemeBookmark.scheme_id == scheme_id)
            if user_id:
                query = query.where(SchemeBookmark.user_id == user_id)
            if public_user_id:
                query = query.where(SchemeBookmark.public_user_id == public_user_id)

            result = await self.db.execute(query)
            return result.scalar_one()

    async def remove_bookmark(
        self,
        scheme_id: int,
        user_id: Optional[int] = None,
        public_user_id: Optional[int] = None,
    ) -> bool:
        """Remove a bookmark for a scheme. Returns True if deleted, False if not found."""
        query = delete(SchemeBookmark).where(SchemeBookmark.scheme_id == scheme_id)

        if user_id:
            query = query.where(SchemeBookmark.user_id == user_id)
        if public_user_id:
            query = query.where(SchemeBookmark.public_user_id == public_user_id)

        result = await self.db.execute(query.returning(SchemeBookmark.id))
        await self.db.commit()
        return result.scalar_one_or_none() is not None

    async def get_bookmarked_schemes(
        self,
        user_id: Optional[int] = None,
        public_user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Scheme]:
        """Get all bookmarked schemes for a user."""
        query = (
            select(Scheme)
            .join(SchemeBookmark, Scheme.id == SchemeBookmark.scheme_id)
            .options(selectinload(Scheme.media))
            .offset(skip)
            .limit(limit)
        )

        if user_id:
            query = query.where(SchemeBookmark.user_id == user_id)
        if public_user_id:
            query = query.where(SchemeBookmark.public_user_id == public_user_id)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def is_bookmarked(
        self,
        scheme_id: int,
        user_id: Optional[int] = None,
        public_user_id: Optional[int] = None,
    ) -> bool:
        """Check if a scheme is bookmarked by a user."""
        query = select(SchemeBookmark).where(SchemeBookmark.scheme_id == scheme_id)
        if user_id:
            query = query.where(SchemeBookmark.user_id == user_id)
        if public_user_id:
            query = query.where(SchemeBookmark.public_user_id == public_user_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
