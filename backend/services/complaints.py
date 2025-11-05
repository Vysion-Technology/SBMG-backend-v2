"""Service layer for managing complaints."""

from enum import Enum
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Date, func, select
from sqlalchemy.sql.functions import coalesce
from sqlalchemy.orm import selectinload

from models.database.complaint import (
    Complaint,
    ComplaintType,
    ComplaintStatus,
    ComplaintComment,
)
from models.database.geography import Block, District, GramPanchayat as GramPanchayat
from models.response.complaint import (
    ComplaintCommentResponse,
    DetailedComplaintResponse,
    MediaResponse,
)
from models.response.analytics import (
    ComplaintDateAnalyticsResponse,
    GeographyComplaintCountByStatusResponse,
    ComplaintGeoAnalyticsResponse,
    TopNGeographiesInDateRangeResponse,
)
from models.internal import GeoTypeEnum


class ComplaintOrderByEnum(str, Enum):
    """Enumeration for complaint ordering options."""

    NEWEST = "newest"
    OLDEST = "oldest"
    STATUS = "status"
    DISTRICT = "district"
    BLOCK = "block"
    GP = "gp"


class ComplaintService:
    """Service layer for managing complaints."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_complaint_by_id(self, complaint_id: int) -> Optional[Complaint]:
        """Retrieve a complaint by its ID."""
        result = await self.db.execute(
            select(Complaint)
            .where(
                Complaint.id == complaint_id,  # type: ignore
            )
            .options(
                selectinload(Complaint.status),
                selectinload(Complaint.gp),
                selectinload(Complaint.block),
                selectinload(Complaint.district),
                selectinload(Complaint.complaint_type),
                selectinload(Complaint.media),
                selectinload(Complaint.comments),
                selectinload(Complaint.comments).selectinload(ComplaintComment.user),
            )
        )
        complaint = result.scalar_one_or_none()
        return complaint

    async def get_all_complaints(
        self,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        village_id: Optional[int] = None,
        complaint_status_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = 500,
        order_by: ComplaintOrderByEnum = ComplaintOrderByEnum.NEWEST,
    ) -> list[DetailedComplaintResponse]:
        query = (
            select(Complaint)
            .options(
                selectinload(Complaint.status),
                selectinload(Complaint.gp),
                selectinload(Complaint.block),
                selectinload(Complaint.district),
                selectinload(Complaint.complaint_type),
                # selectinload(Complaint.media_urls),
                selectinload(Complaint.media),
                selectinload(Complaint.comments),
                selectinload(Complaint.comments).selectinload(ComplaintComment.user),
            )
            .join(ComplaintStatus, isouter=True)
            .join(GramPanchayat, isouter=True)
            .join(Block, isouter=True)
            .join(District, isouter=True)
            .join(ComplaintType, isouter=True)
            .join(ComplaintComment, isouter=True)
            .join(Complaint.media, isouter=True)
        )
        if district_id is not None:
            query = query.where(Complaint.district_id == district_id)  # type: ignore
        if block_id is not None:
            query = query.where(Complaint.block_id == block_id)  # type: ignore
        if village_id is not None:
            query = query.where(Complaint.gp_id == village_id)  # type: ignore
        if complaint_status_id is not None:
            query = query.where(Complaint.status_id == complaint_status_id)  # type: ignore
        if start_date is not None:
            query = query.where(Complaint.created_at >= start_date)
        if end_date is not None:
            query = query.where(Complaint.created_at <= end_date)

        if order_by == ComplaintOrderByEnum.NEWEST:
            query = query.order_by(Complaint.created_at.desc())
        elif order_by == ComplaintOrderByEnum.OLDEST:
            query = query.order_by(Complaint.created_at.asc())
        elif order_by == ComplaintOrderByEnum.STATUS:
            query = query.order_by(Complaint.status_id)
        elif order_by == ComplaintOrderByEnum.DISTRICT:
            query = query.order_by(Complaint.district_id)
        elif order_by == ComplaintOrderByEnum.BLOCK:
            query = query.order_by(Complaint.block_id)
        elif order_by == ComplaintOrderByEnum.GP:
            query = query.order_by(Complaint.gp_id)

        if skip is not None:
            query = query.offset(skip)
        if limit is not None:
            query = query.limit(limit)

        result = await self.db.execute(query)
        complaints = result.scalars().all()
        return [
            DetailedComplaintResponse(
                id=complaint.id,
                description=complaint.description,
                complaint_type_id=complaint.complaint_type_id,
                mobile_number=complaint.mobile_number,
                created_at=complaint.created_at,
                updated_at=complaint.updated_at,
                status_id=complaint.status_id,
                lat=complaint.lat,
                long=complaint.long,
                location=complaint.location,
                complaint_type=complaint.complaint_type.name if complaint.complaint_type else None,
                status=complaint.status.name if complaint.status else None,
                village_name=complaint.gp.name if complaint.gp else None,
                block_name=complaint.block.name if complaint.block else None,
                district_name=complaint.district.name if complaint.district else None,
                media_urls=[media.media_url for media in complaint.media] if complaint.media else [],
                media=[
                    MediaResponse(
                        id=media.id,
                        media_url=media.media_url,
                        uploaded_at=media.uploaded_at,
                    )
                    for media in complaint.media
                ]
                if complaint.media
                else [],
                comments=[
                    ComplaintCommentResponse(
                        id=comment.id,
                        complaint_id=comment.complaint_id,
                        comment=comment.comment,
                        commented_at=comment.commented_at,
                        user_name=comment.user.name if comment.user else "",
                    )
                    for comment in complaint.comments
                ],
                resolved_at=complaint.resolved_at,
                verified_at=complaint.verified_at,
                closed_at=complaint.closed_at,
            )
            for complaint in complaints
        ]

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

    async def count_complaints_by_status_and_geo(
        self,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        gp_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        level: GeoTypeEnum = GeoTypeEnum.DISTRICT,
    ) -> ComplaintGeoAnalyticsResponse:
        """Count complaints grouped by their status."""
        if level == GeoTypeEnum.DISTRICT:
            query = (
                select(
                    Complaint.district_id,
                    District.name,
                    Complaint.status_id,
                    ComplaintStatus.name,
                    func.count(Complaint.id),
                    func.avg(
                        func.extract(
                            "epoch", coalesce(Complaint.resolved_at, Complaint.created_at) - Complaint.created_at
                        )
                    ).label("avg_resolution_time"),
                )
                .join(GramPanchayat, Complaint.gp_id == GramPanchayat.id)
                .join(Block, GramPanchayat.block_id == Block.id)
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
                    Complaint.block_id,
                    Block.name,
                    ComplaintStatus.id,
                    ComplaintStatus.name,
                    func.count(Complaint.id),
                    func.avg(
                        func.extract(
                            "epoch", coalesce(Complaint.resolved_at, Complaint.created_at) - Complaint.created_at
                        )
                    ).label("avg_resolution_time"),
                )
                .join(GramPanchayat, Complaint.gp_id == GramPanchayat.id)
                .join(Block, GramPanchayat.block_id == Block.id)
                .join(ComplaintStatus, Complaint.status_id == ComplaintStatus.id)
                .group_by(Complaint.block_id, Block.name, ComplaintStatus.id, ComplaintStatus.name)
            )
        else:  # GP level
            query = (
                select(
                    Complaint.gp_id,
                    GramPanchayat.name,
                    ComplaintStatus.id,
                    ComplaintStatus.name,
                    func.count(Complaint.id),
                    func.avg(
                        func.extract(
                            "epoch", coalesce(Complaint.resolved_at, Complaint.created_at) - Complaint.created_at
                        )
                    ).label("avg_resolution_time"),
                )
                .join(GramPanchayat, Complaint.gp_id == GramPanchayat.id)
                .join(ComplaintStatus, Complaint.status_id == ComplaintStatus.id)
                .group_by(Complaint.gp_id, GramPanchayat.name, ComplaintStatus.id, ComplaintStatus.name)
            )
        if district_id is not None:
            query = query.where(Complaint.district_id == district_id)
        if block_id is not None:
            query = query.where(Complaint.block_id == block_id)  # type: ignore
        if gp_id is not None:
            query = query.where(Complaint.gp_id == gp_id)  # type: ignore
        if start_date is not None:
            query = query.where(Complaint.created_at >= start_date)
        if end_date is not None:
            query = query.where(Complaint.created_at <= end_date)
        result = await self.db.execute(query)
        counts = result.fetchall()
        return ComplaintGeoAnalyticsResponse(
            geo_type=level,
            response=[
                GeographyComplaintCountByStatusResponse(
                    geography_id=row[0],
                    geography_name=row[1],
                    status_id=row[2],
                    status=row[3],
                    count=row[4],
                    average_resolution_time=row[5],
                )
                for row in counts
            ],
        )

    async def count_complaints_by_date(
        self,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        gp_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ComplaintDateAnalyticsResponse]:
        """Count complaints grouped by their creation date."""
        query = (
            select(Complaint.created_at.cast(Date), func.count(Complaint.id), Complaint.status_id, ComplaintStatus.name)
            .group_by(Complaint.created_at.cast(Date), Complaint.status_id, ComplaintStatus.name)
            .join(ComplaintStatus, Complaint.status_id == ComplaintStatus.id)
        )
        if district_id is not None:
            query = query.where(Complaint.district_id == district_id)
        if block_id is not None:
            query = query.where(Complaint.block_id == block_id)
        if gp_id is not None:
            query = query.where(Complaint.gp_id == gp_id)

        if start_date is not None:
            query = query.where(Complaint.created_at >= start_date)
        if end_date is not None:
            query = query.where(Complaint.created_at <= end_date)

        result = await self.db.execute(query)
        counts = result.fetchall()
        return [
            ComplaintDateAnalyticsResponse(
                district_id=district_id,
                block_id=block_id,
                gp_id=gp_id,
                date=row[0],
                count=row[1],
                status_id=row[2],
                status=row[3],
            )
            for row in counts
        ]

    def calculate_score(
        self, average_resolution_time: float, total_complaints: int, total_resolved_complaints: int
    ) -> float:
        """Calculate score based on count and average resolution time.

        MAX Score: 100 (50 for % resolution within SLA (7 days) + 50 for % of complaints resolved)
        Score = (Resolved within SLA % * 50) + (Resolved Complaints % * 50)
        """

        score1 = max(0, (84600 * 7 - average_resolution_time) / 84600 * 7)
        score2 = max(0, total_resolved_complaints / total_complaints * 50)
        return score1 + score2

    async def get_top_n_geographies(
        self,
        start_date: datetime,
        end_date: datetime,
        n: int = 5,
        level: GeoTypeEnum = GeoTypeEnum.DISTRICT,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        gp_id: Optional[int] = None,
    ) -> List[TopNGeographiesInDateRangeResponse]:
        """Get top N complaint types by count."""
        if level == GeoTypeEnum.DISTRICT:
            query = (
                select(
                    Complaint.district_id,
                    District.name,
                    Complaint.status_id,
                    ComplaintStatus.name,
                    func.count(Complaint.id),
                    func.avg(
                        func.extract(
                            "epoch", coalesce(Complaint.resolved_at, Complaint.created_at) - Complaint.created_at
                        )
                    ).label("avg_resolution_time"),
                )
                .join(GramPanchayat, Complaint.gp_id == GramPanchayat.id)
                .join(Block, GramPanchayat.block_id == Block.id)
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
                    Complaint.block_id,
                    Block.name,
                    ComplaintStatus.id,
                    ComplaintStatus.name,
                    func.count(Complaint.id),
                    func.avg(
                        func.extract(
                            "epoch", coalesce(Complaint.resolved_at, Complaint.created_at) - Complaint.created_at
                        )
                    ).label("avg_resolution_time"),
                )
                .join(GramPanchayat, Complaint.gp_id == GramPanchayat.id)
                .join(Block, GramPanchayat.block_id == Block.id)
                .join(ComplaintStatus, Complaint.status_id == ComplaintStatus.id)
                .group_by(Complaint.block_id, Block.name, ComplaintStatus.id, ComplaintStatus.name)
            )
        else:  # GP level
            query = (
                select(
                    Complaint.gp_id,
                    GramPanchayat.name,
                    ComplaintStatus.id,
                    ComplaintStatus.name,
                    func.count(Complaint.id),
                    func.avg(
                        func.extract(
                            "epoch", coalesce(Complaint.resolved_at, Complaint.created_at) - Complaint.created_at
                        )
                    ).label("avg_resolution_time"),
                )
                .join(GramPanchayat, Complaint.gp_id == GramPanchayat.id)
                .join(ComplaintStatus, Complaint.status_id == ComplaintStatus.id)
                .group_by(Complaint.gp_id, GramPanchayat.name, ComplaintStatus.id, ComplaintStatus.name)
            )
        query = query.where(Complaint.created_at >= start_date)
        query = query.where(Complaint.created_at <= end_date)
        if district_id is not None:
            query = query.where(Complaint.district_id == district_id)
        if block_id is not None:
            query = query.where(Complaint.block_id == block_id)  # type: ignore
        if gp_id is not None:
            query = query.where(Complaint.gp_id == gp_id)  # type: ignore
        results = await self.db.execute(query)
        res = results.fetchall()

        # Create a list of list of rows with the same geo id and name
        class TempGeoItem(BaseModel):
            """Temporary model to hold aggregated data per geography."""

            geo_id: int
            geo_name: str
            total_complaints: int
            total_resolved_complaints: int
            total_resolution_time: float

        nested_rows: dict[int, TempGeoItem] = {}

        for row in res:
            geo_id = row[0]
            geo_name = row[1]
            count = int(row[4])
            avg_resolution_time = float(row[5])
            if geo_id not in nested_rows:
                nested_rows[geo_id] = TempGeoItem(
                    geo_id=geo_id,
                    geo_name=geo_name,
                    total_complaints=0,
                    total_resolved_complaints=0,
                    total_resolution_time=0.0,
                )
            nested_rows[geo_id].total_complaints += count
            if row[3] == "RESOLVED":
                nested_rows[geo_id].total_resolved_complaints += count
                nested_rows[geo_id].total_resolution_time += avg_resolution_time * count
        # Create a list of TopNGeographiesInDateRangeResponse from the nested_rows
        res = [
            TopNGeographiesInDateRangeResponse(
                geo_type=level,
                start_date=start_date.date(),
                end_date=end_date.date(),
                geo_id=geo_id,
                geo_name=nested_rows[geo_id].geo_name,
                score=self.calculate_score(
                    average_resolution_time=(
                        nested_rows[geo_id].total_resolution_time / nested_rows[geo_id].total_resolved_complaints
                        if nested_rows[geo_id].total_resolved_complaints > 0
                        else 84600
                    ),
                    total_complaints=nested_rows[geo_id].total_complaints,
                    total_resolved_complaints=nested_rows[geo_id].total_resolved_complaints,
                ),
            )
            for geo_id in nested_rows
        ]
        res = sorted(res, key=lambda x: (x.score), reverse=True)
        res = sorted(res, key=lambda x: (x.geo_name))
        return res[:n]

    async def create_complaint(
        self,
        public_user_id: int,
        description: str,
        complaint_type_id: int,
        gp_id: int,
        mobile_number: Optional[str] = None,
        lat: Optional[float] = 1,
        long: Optional[float] = 1,
        location: str = "location",
    ) -> Complaint:
        """Create a new complaint."""
        # Get default status (e.g., "NEW")
        status_result = await self.db.execute(select(ComplaintStatus).where(ComplaintStatus.name == "NEW"))
        default_status = status_result.scalar_one_or_none()
        if not default_status:
            default_status = ComplaintStatus(name="NEW", description="Newly created complaint")
            self.db.add(default_status)
            await self.db.commit()
            await self.db.refresh(default_status)

        gp = await self.db.execute(
            select(GramPanchayat).options(selectinload(GramPanchayat.block)).where(GramPanchayat.id == gp_id)
        )
        gp_obj = gp.scalar_one_or_none()
        if not gp_obj:
            raise HTTPException(status_code=404, detail=f"Gram Panchayat with id {gp_id} does not exist")

        complaint = Complaint(
            public_user_id=public_user_id,
            description=description,
            complaint_type_id=complaint_type_id,
            gp_id=gp_id,
            block_id=gp_obj.block_id,
            district_id=gp_obj.block.district_id,
            mobile_number=mobile_number,
            status_id=default_status.id,
            lat=lat,
            long=long,
            location=location,
        )

        self.db.add(complaint)
        await self.db.commit()
        await self.db.refresh(complaint)
        return await self.get_complaint_by_id(complaint.id)

    async def update_complaint(self, complaint_id: int, status_id: Optional[int] = None) -> Optional[Complaint]:
        """Update an existing complaint."""
        complaint_result = await self.db.execute(select(Complaint).where(Complaint.id == complaint_id))
        complaint = complaint_result.scalar_one_or_none()
        if not complaint:
            return None
        if status_id is not None:
            complaint.status_id = status_id
        complaint.updated_at = datetime.now(tz=timezone.utc)
        await self.db.commit()
        await self.db.refresh(complaint)
        return await self.get_complaint_by_id(complaint.id)
