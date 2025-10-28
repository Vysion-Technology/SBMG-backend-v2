from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sqlalchemy import delete, select, update

from models.database.scheme import Scheme, SchemeMedia

class SchemeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_scheme_by_id(self, scheme_id: int) -> Optional[Scheme]:
        result = await self.db.execute(select(Scheme).options(selectinload(Scheme.media)).where(Scheme.id == scheme_id))
        scheme = result.scalar_one_or_none()
        return scheme

    async def get_all_schemes(
        self,
        skip: int = 0,
        limit: int = 100,
        active: bool = True,
    ) -> list[Scheme]:
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
            update(Scheme)
            .where(Scheme.id == scheme_id)
            .values(**update_data)
        )
        await self.db.commit()
        scheme = await self.get_scheme_by_id(scheme_id)
        return scheme

    async def add_scheme_media(self, scheme_id: int, media_url: str) -> SchemeMedia:
        media = SchemeMedia(scheme_id=scheme_id, media_url=media_url)
        self.db.add(media)
        await self.db.commit()
        await self.db.refresh(media)
        return media

    async def remove_scheme_media(self, scheme_id: int, scheme_media_id: int) -> None:
        await self.db.execute(
            delete(SchemeMedia)
            .where(SchemeMedia.id == scheme_media_id)
            .where(SchemeMedia.scheme_id == scheme_id)
        )
        await self.db.commit()

    async def delete_scheme(self, scheme_id: int) -> None:
        await self.db.execute(delete(Scheme).where(Scheme.id == scheme_id))
        await self.db.commit()