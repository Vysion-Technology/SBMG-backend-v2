from typing import Optional, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, insert
from sqlalchemy.orm import selectinload

from models.database.notice import Notice


class NoticeService:
    """Service for managing notices."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notice(
        self,
        sender_id: int,
        receiver_id: int,
        title: str,
        text: Optional[str],
    ) -> Notice:
        """Create a new notice."""
        notice = (
            await self.db.execute(
                insert(Notice)
                .values(
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    title=title,
                    text=text,
                    date=date.today(),
                )
                .returning(Notice)
            )
        ).scalar_one()
        return notice

    async def get_notices_sent_by_user(
        self, sender_id: int, skip: int = 0, limit: int = 100
    ) -> List[Notice]:
        """Get notices sent by a specific user."""
        result = await self.db.execute(
            select(Notice)
            .where(Notice.sender_id == sender_id)
            .offset(skip)
            .limit(limit)
        )
        notices = result.scalars().all()
        return list(notices)

    async def get_notices_received_by_user(
        self, receiver_id: int, skip: int = 0, limit: int = 100
    ) -> List[Notice]:
        """Get notices received by a specific user."""
        result = await self.db.execute(
            select(Notice)
            .where(Notice.receiver_id == receiver_id)
            .offset(skip)
            .limit(limit)
        )
        notices = result.scalars().all()
        return list(notices)

    async def get_notice_by_id(self, notice_id: int) -> Optional[Notice]:
        """Get a specific notice by ID."""
        result = await self.db.execute(
            select(Notice)
            .where(Notice.id == notice_id)
            .options(selectinload(Notice.media))
        )
        notice = result.scalar_one_or_none()
        return notice

    async def delete_notice(self, notice_id: int) -> None:
        """Delete a specific notice by ID."""
        await self.db.execute(delete(Notice).where(Notice.id == notice_id))
        await self.db.commit()
