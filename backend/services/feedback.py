"""Service layer for feedback-related operations."""

from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession


from models.database.feedback import Feedback
from models.internal import FeedbackFromEnum
from models.response.feedback import FeedbackStatsResponse


class FeedbackService:
    """Service class for managing feedback operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_feedback(
        self, auth_user_id: int | None, public_user_id: int | None, rating: int, comment: str | None
    ) -> Feedback:
        """Save feedback to the database."""
        if not auth_user_id and not public_user_id:
            raise ValueError("Either auth_user_id or public_user_id must be provided.")
        # Check if feedback already exists for the user
        query = select(Feedback).where(
            (Feedback.auth_user_id == auth_user_id) if auth_user_id else (Feedback.public_user_id == public_user_id)
        )
        result = await self.db.execute(query)
        existing_feedback = result.scalar_one_or_none()
        if existing_feedback:
            raise HTTPException(status_code=400, detail="Feedback already exists for this user.")

        feedback = (await self.db.execute(
            insert(Feedback)
            .values(
                auth_user_id=auth_user_id,
                public_user_id=public_user_id,
                rating=rating,
                comment=comment,
            )
            .returning(Feedback)
        )).scalar_one()
        await self.db.commit()
        await self.db.refresh(feedback)
        return feedback

    async def get_feedback_by_id(self, feedback_id: int) -> Feedback | None:
        """Retrieve feedback by its ID."""
        result = await self.db.execute(select(Feedback).where(Feedback.id == feedback_id))
        feedback = result.scalar_one_or_none()
        return feedback

    async def get_all_feedback(
        self,
        feedback_source: Optional[FeedbackFromEnum] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Feedback]:
        """Retrieve all feedback from a specific source."""
        if limit >= 1000:
            raise HTTPException(status_code=400, detail="Limit exceeds maximum of 1000")
        query = select(Feedback)
        if feedback_source == FeedbackFromEnum.AUTH_USER:
            query = query.where(Feedback.auth_user_id.isnot(None))
        elif feedback_source == FeedbackFromEnum.PUBLIC_USER:
            query = query.where(Feedback.public_user_id.isnot(None))

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        feedback_list = result.scalars().all()
        return list(feedback_list)

    async def count_stats(self) -> FeedbackStatsResponse:
        """Count feedback statistics."""
        total_feedback_result = await self.db.execute(select(Feedback))
        total_feedback = total_feedback_result.scalars().all()
        total_count = len(total_feedback)

        if total_count == 0:
            return FeedbackStatsResponse(
                total_feedback=0,
                average_rating=0.0,
                auth_user_avg_rating=0.0,
                public_user_avg_rating=0.0,
            )

        average_rating = sum(fb.rating for fb in total_feedback) / total_count

        auth_user_feedback = [fb for fb in total_feedback if fb.auth_user_id is not None]
        public_user_feedback = [fb for fb in total_feedback if fb.public_user_id is not None]

        auth_user_avg_rating = (
            sum(fb.rating for fb in auth_user_feedback) / len(auth_user_feedback) if auth_user_feedback else 0.0
        )
        public_user_avg_rating = (
            sum(fb.rating for fb in public_user_feedback) / len(public_user_feedback) if public_user_feedback else 0.0
        )

        return FeedbackStatsResponse(
            total_feedback=total_count,
            average_rating=average_rating,
            auth_user_avg_rating=auth_user_avg_rating,
            public_user_avg_rating=public_user_avg_rating,
        )
