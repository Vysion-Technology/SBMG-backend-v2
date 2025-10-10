from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from models.database.complaint import (
    Complaint,
    ComplaintType,
    ComplaintStatus,
    ComplaintComment,
)
from models.database.geography import Block, District, GramPanchayat as Village
from models.response.complaint import (
    GeoGraphyComplaintCountByStatusResponse,
    GeoTypeEnum,
    ComplaintTypeCountResponse,
)


class ComplaintService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_complaint_by_id(self, complaint_id: int) -> Optional[Complaint]:
        result = await self.db.execute(
            select(Complaint).where(
                Complaint.id == complaint_id,  # type: ignore
            )
        )
        complaint = result.scalar_one_or_none()
        return complaint

    async def get_all_complaints(
        self,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        village_id: Optional[int] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = 500,
    ) -> list[Complaint]:
        query = select(Complaint)
        if district_id is not None:
            query = query.where(Complaint.district_id == district_id)  # type: ignore
        if block_id is not None:
            query = query.where(Complaint.block_id == block_id)  # type: ignore
        if village_id is not None:
            query = query.where(Complaint.village_id == village_id)  # type: ignore
        if skip is not None:
            query = query.offset(skip)
        if limit is not None:
            query = query.limit(limit)

        result = await self.db.execute(query)
        complaints = result.scalars().all()
        return list(complaints)

    async def get_complaint_types(self) -> list[ComplaintType]:
        result = await self.db.execute(select(ComplaintType))
        types = result.scalars().all()
        return list(types)

    async def get_complaint_statuses(self) -> list[ComplaintStatus]:
        result = await self.db.execute(select(ComplaintStatus))
        statuses = result.scalars().all()
        return list(statuses)

    async def add_complaint_comment(self, complaint_id: int, user_id: int, comment_text: str) -> ComplaintComment:
        """Add a comment to a complaint."""
        comment = ComplaintComment(complaint_id=complaint_id, user_id=user_id, comment=comment_text)

        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def resolve_complaint(
        self, complaint_id: int, user_id: int, resolution_comment: Optional[str] = None
    ) -> bool:
        """Mark a complaint as resolved and optionally add a resolution comment."""
        # Get or create "RESOLVED" status
        status_result = await self.db.execute(select(ComplaintStatus).where(ComplaintStatus.name == "RESOLVED"))
        resolved_status = status_result.scalar_one_or_none()
        if not resolved_status:
            resolved_status = ComplaintStatus(name="RESOLVED", description="Complaint has been resolved")
            self.db.add(resolved_status)
            await self.db.commit()
            await self.db.refresh(resolved_status)

        # Update complaint status
        complaint_result = await self.db.execute(select(Complaint).where(Complaint.id == complaint_id))
        complaint = complaint_result.scalar_one_or_none()
        if not complaint:
            return False

        complaint.status_id = resolved_status.id
        complaint.updated_at = datetime.now(tz=timezone.utc)

        # Add resolution comment if provided
        if resolution_comment:
            comment = ComplaintComment(
                complaint_id=complaint_id,
                user_id=user_id,
                comment=f"[RESOLVED] {resolution_comment}",
            )
            self.db.add(comment)

        await self.db.commit()
        return True

    async def count_complaints_by_status(
        self,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        gp_id: Optional[int] = None,
        level: GeoTypeEnum = GeoTypeEnum.DISTRICT,
    ) -> ComplaintTypeCountResponse:
        """Count complaints grouped by their status."""
        if level == GeoTypeEnum.DISTRICT:
            query = (
                select(
                    Complaint.district_id,
                    District.name,
                    Complaint.status_id,
                    ComplaintStatus.name,
                    func.count(Complaint.id),
                )
                .join(Village, Complaint.village_id == Village.id)
                .join(Block, Village.block_id == Block.id)
                .join(District, Block.district_id == District.id)
                .join(ComplaintStatus, Complaint.status_id == ComplaintStatus.id)
                .group_by(
                    Complaint.district_id,
                    District.name,
                    Complaint.status_id,
                    ComplaintStatus.name,
                    ComplaintStatus.id,
                )
            )
        elif level == GeoTypeEnum.BLOCK:
            query = (
                select(
                    Complaint.block_id, Block.name, ComplaintStatus.id, ComplaintStatus.name, func.count(Complaint.id)
                )
                .join(Village, Complaint.village_id == Village.id)
                .join(Block, Village.block_id == Block.id)
                .join(ComplaintStatus, Complaint.status_id == ComplaintStatus.id)
                .group_by(Complaint.block_id, Block.name, ComplaintStatus.id, ComplaintStatus.name)
            )
        else:  # GP level
            query = (
                select(
                    Complaint.village_id,
                    Village.name,
                    ComplaintStatus.id,
                    ComplaintStatus.name,
                    func.count(Complaint.id),
                )
                .join(Village, Complaint.village_id == Village.id)
                .join(ComplaintStatus, Complaint.status_id == ComplaintStatus.id)
                .group_by(Complaint.village_id, Village.name, ComplaintStatus.id, ComplaintStatus.name)
            )
        if district_id is not None:
            query = query.where(Complaint.district_id == district_id)
        if block_id is not None:
            query = query.where(Complaint.block_id == block_id)  # type: ignore
        if gp_id is not None:
            query = query.where(Complaint.village_id == gp_id)  # type: ignore
        result = await self.db.execute(query)
        counts = result.fetchall()
        return ComplaintTypeCountResponse(
            geo_type=level,
            response=[
                GeoGraphyComplaintCountByStatusResponse(
                    geography_id=row[0],
                    geography_name=row[1],
                    status_id=row[2],
                    status=row[3],
                    count=row[4],
                )
                for row in counts
            ],
        )
