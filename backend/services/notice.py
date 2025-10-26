from typing import Optional, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, insert, and_
from sqlalchemy.orm import selectinload

from models.database.notice import Notice
from models.database.auth import PositionHolder


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
        self, sender_ids: List[int], skip: int = 0, limit: int = 100
    ) -> List[Notice]:
        """
        Get notices sent by a user.
        
        This includes notices sent from any of the user's position holder IDs.
        """
        result = await self.db.execute(
            select(Notice)
            .where(Notice.sender_id.in_(sender_ids))
            .offset(skip)
            .limit(limit)
            .order_by(Notice.date.desc())
        )
        notices = result.scalars().all()
        return list(notices)

    async def get_notices_received_by_user(
        self, receiver_ids: List[int], skip: int = 0, limit: int = 100
    ) -> List[Notice]:
        """
        Get notices received by a user.
        
        This includes notices sent to:
        1. The user's current position holder IDs (direct match)
        2. Any previous position holders who had the same role and geographical assignment
           (role-based visibility for transferred positions)
        
        Example: If a VDO at Village X was transferred and replaced by a new VDO,
        the new VDO will see all notices that were sent to the old VDO position.
        """
        # First, get the current user's position holders to know their roles and geography
        current_positions_result = await self.db.execute(
            select(PositionHolder).where(PositionHolder.id.in_(receiver_ids))
        )
        current_positions = list(current_positions_result.scalars().all())
        
        # Build a list of position holder IDs that match the same role+geography
        all_relevant_position_ids = set(receiver_ids)  # Start with direct IDs
        print("All Relevant Position IDs Start:", all_relevant_position_ids)
        
        for position in current_positions:
            # Find all position holders (past and present) with the same role and geography
            matching_positions_result = await self.db.execute(
                select(PositionHolder.id).where(
                    and_(
                        PositionHolder.role_id == position.role_id,
                        PositionHolder.district_id == position.district_id,
                        PositionHolder.block_id == position.block_id,
                        PositionHolder.village_id == position.village_id,
                    )
                )
            )
            matching_ids = [row[0] for row in matching_positions_result.all()]
            all_relevant_position_ids.update(matching_ids)
        
        # Query notices sent to any of these position holders
        result = await self.db.execute(
            select(Notice)
            .where(Notice.receiver_id.in_(list(all_relevant_position_ids)))
            .offset(skip)
            .limit(limit)
            .order_by(Notice.date.desc())
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
