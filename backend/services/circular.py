"""Service layer for managing circulars."""
from datetime import datetime
from typing import Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.database.circular import Circular


class CircularService:
    """Service layer for managing circulars."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_circular_by_id(self, circular_id: int) -> Optional[Circular]:
        """Retrieve a circular by its ID."""
        result = await self.db.execute(
            select(Circular).where(Circular.id == circular_id),
        )
        return result.scalar_one_or_none()

    async def get_all_circulars(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[Circular]:
        """Retrieve all circulars ordered by creation date descending."""
        query = select(Circular)
        if active_only:
            query = query.where(Circular.is_active == True)
        query = query.order_by(Circular.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_circular(
        self,
        title: str,
        description: str,
        pdf_url: str,
        image_url: Optional[str] = None,
        is_active: bool = True,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Circular:
        """Create a new circular."""
        circular = Circular(
            title=title,
            description=description,
            pdf_url=pdf_url,
            image_url=image_url,
            is_active=is_active,
            start_date=start_date,
            end_date=end_date,
        )
        self.db.add(circular)
        await self.db.commit()
        await self.db.refresh(circular)
        return circular

    async def update_circular(
        self,
        circular_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        pdf_url: Optional[str] = None,
        image_url: Optional[str] = None,
        is_active: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Optional[Circular]:
        """Update circular details."""
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if description is not None:
            update_data["description"] = description
        if pdf_url is not None:
            update_data["pdf_url"] = pdf_url
        if image_url is not None:
            update_data["image_url"] = image_url
        if is_active is not None:
            update_data["is_active"] = is_active
        if start_date is not None:
            update_data["start_date"] = start_date
        if end_date is not None:
            update_data["end_date"] = end_date

        if not update_data:
            return await self.get_circular_by_id(circular_id)

        await self.db.execute(
            update(Circular).where(Circular.id == circular_id).values(**update_data),
        )
        await self.db.commit()
        return await self.get_circular_by_id(circular_id)

    async def delete_circular(self, circular_id: int) -> None:
        """Delete a circular by its ID."""
        await self.db.execute(delete(Circular).where(Circular.id == circular_id))
        await self.db.commit()
