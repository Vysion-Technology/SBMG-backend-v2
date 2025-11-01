"""Attendance service for managing worker attendance records."""

from typing import Dict, List, Optional

from datetime import date, datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import distinct, insert, select, func, and_, literal_column
from sqlalchemy.orm import joinedload

from models.database.attendance import DailyAttendance
from models.database.contractor import Contractor
from models.database.geography import GramPanchayat, Block, District
from models.internal import GeoTypeEnum
from models.requests.attendance import (
    AttendanceLogRequest,
    AttendanceEndRequest,
)
from models.response.attendance import (
    AttendanceOverviewResponse,
    AttendanceResponse,
    AttendanceListResponse,
    AttendanceAnalyticsResponse,
    GeographyAttendanceCountResponse,
    DayAttendanceSummaryResponse,
    DaySummaryAttendanceResponse,
    MonthlyAggregation,
    MonthlyAttendanceTrendResponse,
    TopNGeoAttendanceResponse,
    AnnualGeoPerformanceResponse,
)


def get_attendance_response_from_db(attendance: DailyAttendance) -> AttendanceResponse:
    """Convert DailyAttendance DB model to AttendanceResponse model"""
    return AttendanceResponse(
        id=attendance.id,
        contractor_id=attendance.contractor_id,
        contractor_name=attendance.contractor.person_name if attendance.contractor else None,
        village_id=None,
        village_name=None,
        block_name=None,
        district_name=None,
        date=attendance.date,
        start_time=attendance.start_time,
        start_lat=attendance.start_lat or "",
        start_long=attendance.start_long or "",
        end_time=attendance.end_time,
        end_lat=attendance.end_lat,
        end_long=attendance.end_long,
        remarks=attendance.remarks,
        agency=attendance.contractor.agency if attendance.contractor else None,
    )


class AttendanceService:
    """Service for managing worker attendance"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_attendance(self, contractor_id: int, request: AttendanceLogRequest) -> DailyAttendance:
        """Log worker attendance (start of work day)"""
        # Check if attendance already exists for this contractor and date
        date_field = date.today()
        existing_attendance = await self.db.execute(
            select(DailyAttendance).where(
                and_(
                    DailyAttendance.contractor_id == contractor_id,
                    DailyAttendance.date == date_field,
                )
            )
        )
        existing = existing_attendance.scalar_one_or_none()

        if existing:
            raise ValueError("Attendance already logged for this date")

        # Create new attendance record
        attendance = (
            await self.db.execute(
                insert(DailyAttendance)
                .values(
                    contractor_id=contractor_id,
                    date=date_field,
                    start_time=datetime.now(),
                    start_lat=request.start_lat,
                    start_long=request.start_long,
                    remarks=request.remarks,
                )
                .returning(DailyAttendance)
            )
        ).scalar_one()

        await self.db.commit()
        await self.db.refresh(attendance)

        return (
            await self.db.execute(
                select(DailyAttendance)
                .join(Contractor, DailyAttendance.contractor_id == Contractor.id)
                .join(GramPanchayat, Contractor.gp_id == GramPanchayat.id)
                .join(Block, GramPanchayat.block_id == Block.id)
                .options(joinedload(DailyAttendance.contractor))
                .where(DailyAttendance.id == attendance.id)
            )
        ).scalar_one()

    async def end_attendance(self, contractor_id: int, request: AttendanceEndRequest) -> DailyAttendance:
        """End worker attendance (end of work day)"""
        # Get attendance record
        result = await self.db.execute(
            select(DailyAttendance).where(
                and_(
                    DailyAttendance.id == request.attendance_id,
                    DailyAttendance.contractor_id == contractor_id,
                )
            )
        )
        attendance = result.scalar_one_or_none()

        if not attendance:
            raise ValueError("Attendance record not found")

        if attendance.end_time:
            raise ValueError("Attendance already ended")

        # Update attendance with end details
        attendance.end_time = datetime.now()
        attendance.end_lat = request.end_lat
        attendance.end_long = request.end_long
        if request.remarks:
            attendance.remarks = f"{attendance.remarks or ''}\nEnd: {request.remarks}".strip()

        await self.db.commit()
        await self.db.refresh(attendance)

        return attendance

    async def get_attendance_by_id(self, attendance_id: int) -> Optional[DailyAttendance]:
        """Get attendance record by ID with all relations loaded"""
        stmt = (
            select(DailyAttendance)
            .options(joinedload(DailyAttendance.contractor).joinedload(Contractor.agency))
            .join(Contractor, DailyAttendance.contractor_id == Contractor.id)
            .join(GramPanchayat, Contractor.gp_id == GramPanchayat.id)
            .join(Block, GramPanchayat.block_id == Block.id)
            .join(District, Block.district_id == District.id)
        )
        result = await self.db.execute(stmt.where(DailyAttendance.id == attendance_id))
        return result.scalar_one_or_none()

    async def attendance_analytics(
        self,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        gp_id: Optional[int] = None,
        level: GeoTypeEnum = GeoTypeEnum.DISTRICT,
        skip: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = 500,
    ) -> AttendanceAnalyticsResponse:
        """
        Get attendance analytics aggregated by geographic level.
        Returns attendance statistics for each geographic unit at the specified level.
        """

        # Default to current month if no dates provided
        if not start_date:
            start_date = date.today().replace(day=1)
        if not end_date:
            end_date = date.today()

        # Build query based on geographic level
        if level == GeoTypeEnum.DISTRICT:
            # Subquery to get total contractors per district
            total_contractors_subq = (
                select(
                    District.id.label("dist_id"),
                    func.count(func.distinct(Contractor.id)).label("total_contractors"),  # pylint: disable=E1102
                )
                .select_from(District)
                .join(Block, Block.district_id == District.id)
                .join(GramPanchayat, GramPanchayat.block_id == Block.id)
                .join(Contractor, Contractor.gp_id == GramPanchayat.id)
                .group_by(District.id)
            ).subquery()

            # Main query for attendance
            query = (
                select(
                    District.id,
                    District.name,
                    total_contractors_subq.c.total_contractors,
                    func.count(func.distinct(DailyAttendance.contractor_id)).label("present_count"),  # pylint: disable=E1102  # type: ignore
                    DailyAttendance.date.label("attendance_date"),
                    (
                        select(func.count(func.distinct(GramPanchayat.id)))  # pylint: disable=E1102
                        .select_from(GramPanchayat)
                        .join(Block, GramPanchayat.block_id == Block.id)
                        .where(Block.district_id == District.id)
                        .correlate(District)
                        .scalar_subquery()
                    ).label("gp_count"),
                )
                .select_from(District)
                .join(total_contractors_subq, District.id == total_contractors_subq.c.dist_id)
                .join(Block, Block.district_id == District.id)
                .join(GramPanchayat, GramPanchayat.block_id == Block.id)
                .join(Contractor, Contractor.gp_id == GramPanchayat.id)
                .outerjoin(
                    DailyAttendance,
                    and_(
                        DailyAttendance.contractor_id == Contractor.id,
                        DailyAttendance.date >= start_date,
                        DailyAttendance.date <= end_date,
                    ),
                )
                .group_by(District.id, District.name, total_contractors_subq.c.total_contractors, DailyAttendance.date)
            )

            if district_id:
                query = query.where(District.id == district_id)

        elif level == GeoTypeEnum.BLOCK:
            # Subquery to get total contractors per block
            total_contractors_subq = (
                select(
                    Block.id.label("block_id"),
                    func.count(func.distinct(Contractor.id)).label("total_contractors"),  # pylint: disable=E1102
                )
                .select_from(Block)
                .join(GramPanchayat, GramPanchayat.block_id == Block.id)
                .join(Contractor, Contractor.gp_id == GramPanchayat.id)
                .group_by(Block.id)
            ).subquery()

            # Main query for attendance
            query = (
                select(
                    Block.id,
                    Block.name,
                    total_contractors_subq.c.total_contractors,
                    func.count(func.distinct(DailyAttendance.contractor_id)).label("present_count"),  # pylint: disable=E1102
                    DailyAttendance.date.label("attendance_date"),
                    (
                        select(func.count(func.distinct(GramPanchayat.id)))  # pylint: disable=E1102
                        .select_from(GramPanchayat)
                        .where(GramPanchayat.block_id == Block.id)
                        .correlate(Block)
                        .scalar_subquery()
                    ).label("gp_count"),
                )
                .select_from(Block)
                .join(total_contractors_subq, Block.id == total_contractors_subq.c.block_id)
                .join(GramPanchayat, GramPanchayat.block_id == Block.id)
                .join(Contractor, Contractor.gp_id == GramPanchayat.id)
                .outerjoin(
                    DailyAttendance,
                    and_(
                        DailyAttendance.contractor_id == Contractor.id,
                        DailyAttendance.date >= start_date,
                        DailyAttendance.date <= end_date,
                    ),
                )
                .group_by(Block.id, Block.name, total_contractors_subq.c.total_contractors, DailyAttendance.date)
            )

            if district_id:
                query = query.where(Block.district_id == district_id)
            if block_id:
                query = query.where(Block.id == block_id)

        else:  # GP level
            # Subquery to get total contractors per GP
            total_contractors_subq = (
                select(
                    GramPanchayat.id.label("gp_id"),
                    func.count(func.distinct(Contractor.id)).label("total_contractors"),  # pylint: disable=E1102
                )
                .select_from(GramPanchayat)
                .join(Contractor, Contractor.gp_id == GramPanchayat.id)
                .group_by(GramPanchayat.id)
            ).subquery()

            # Main query for attendance
            query = (
                select(
                    GramPanchayat.id,
                    GramPanchayat.name,
                    (select(1).scalar_subquery()).label("total_contractors"),
                    func.count(func.distinct(DailyAttendance.contractor_id, DailyAttendance.date)).label(
                        "present_count"
                    ),  # pylint: disable=E1102
                    DailyAttendance.date.label("attendance_date"),
                    (select(1).scalar_subquery()).label("gp_count"),
                )
                .select_from(GramPanchayat)
                .join(Contractor, Contractor.gp_id == GramPanchayat.id)
                .outerjoin(
                    DailyAttendance,
                    and_(
                        DailyAttendance.contractor_id == Contractor.id,
                        DailyAttendance.date >= start_date,
                        DailyAttendance.date <= end_date,
                    ),
                )
                .group_by(GramPanchayat.id, GramPanchayat.name, DailyAttendance.date)
            )

            if block_id:
                query = query.where(GramPanchayat.block_id == block_id)
            if gp_id:
                query = query.where(GramPanchayat.id == gp_id)

        query = query.offset(skip or 0).limit(limit or 500)

        result = await self.db.execute(query)
        rows = result.fetchall()

        response_items: list[GeographyAttendanceCountResponse] = []
        for row in rows:
            geography_id = row[0]
            geography_name = row[1]
            total_contractors = row[2]
            present_count = row[3]
            __date = row[4]
            gp_count = row[5]

            # Skip rows where date is None (no attendance records for this geography)
            if __date is None:
                continue

            absent_count = total_contractors - present_count
            attendance_rate = (present_count / gp_count * 100) if total_contractors > 0 else 0.0
            print("GP Count:", gp_count)
            print("Attendance Rate:", attendance_rate)

            response_items.append(
                GeographyAttendanceCountResponse(
                    date=__date,
                    geography_id=geography_id,
                    geography_name=geography_name,
                    total_contractors=total_contractors,
                    present_count=present_count,
                    absent_count=absent_count,
                    attendance_rate=attendance_rate,
                    gp_count=gp_count,
                )
            )

        return AttendanceAnalyticsResponse(
            geo_type=level,
            response=response_items,
        )

    async def get_day_attendance(
        self,
        attendance_date: date,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        gp_id: Optional[int] = None,
        level: GeoTypeEnum = GeoTypeEnum.DISTRICT,
        skip: Optional[int] = None,
        limit: Optional[int] = 500,
    ) -> DayAttendanceSummaryResponse:
        """
        Get attendance records for a specific day and geographical level.
        Returns detailed attendance information for all contractors in the specified geography.
        """
        # Build base query
        query = (
            select(DailyAttendance, Contractor, GramPanchayat, Block, District)
            .join(Contractor, DailyAttendance.contractor_id == Contractor.id)
            .join(GramPanchayat, Contractor.gp_id == GramPanchayat.id)
            .join(Block, GramPanchayat.block_id == Block.id)
            .join(District, Block.district_id == District.id)
            .where(DailyAttendance.date == attendance_date)
        )

        # Apply geographic filters
        if district_id:
            query = query.where(District.id == district_id)
        if block_id:
            query = query.where(Block.id == block_id)
        if gp_id:
            query = query.where(GramPanchayat.id == gp_id)

        # Get total count for attendance rate calculation
        count_query = (
            select(func.count(func.distinct(Contractor.id)))  # pylint: disable=E1102
            .select_from(Contractor)
            .join(GramPanchayat, Contractor.gp_id == GramPanchayat.id)
            .join(Block, GramPanchayat.block_id == Block.id)
            .join(District, Block.district_id == District.id)
        )

        if district_id:
            count_query = count_query.where(District.id == district_id)
        if block_id:
            count_query = count_query.where(Block.id == block_id)
        if gp_id:
            count_query = count_query.where(GramPanchayat.id == gp_id)

        total_result = await self.db.execute(count_query)
        total_contractors = total_result.scalar() or 0

        # Apply pagination
        if skip:
            query = query.offset(skip)
        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        rows = result.fetchall()

        attendances: list[DaySummaryAttendanceResponse] = []
        for row in rows:
            attendance = row[0]
            contractor = row[1]
            village = row[2]
            block = row[3]
            district = row[4]

            # Calculate duration if end_time exists
            duration_hours = None
            if attendance.start_time and attendance.end_time:
                duration = attendance.end_time - attendance.start_time
                duration_hours = duration.total_seconds() / 3600

            attendances.append(
                DaySummaryAttendanceResponse(
                    contractor_id=contractor.id,
                    contractor_name=contractor.person_name,
                    village_id=village.id,
                    village_name=village.name,
                    block_id=block.id,
                    block_name=block.name,
                    district_id=district.id,
                    district_name=district.name,
                    date=attendance.date,
                    start_time=attendance.start_time,
                    end_time=attendance.end_time,
                    duration_hours=duration_hours,
                    remarks=attendance.remarks,
                )
            )

        present_count = len(attendances)
        absent_count = total_contractors - present_count
        attendance_rate = (present_count / total_contractors * 100) if total_contractors > 0 else 0.0

        return DayAttendanceSummaryResponse(
            date=attendance_date,
            geo_type=level,
            total_contractors=total_contractors,
            present_count=present_count,
            absent_count=absent_count,
            attendance_rate=attendance_rate,
            attendances=attendances,
        )

    async def get_attendances(
        self,
        contractor_id: Optional[int] = None,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        gp_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 500,
    ) -> AttendanceListResponse:
        """Get all attendance records with optional filters"""
        stmt = (
            select(DailyAttendance)
            .options(joinedload(DailyAttendance.contractor).joinedload(Contractor.agency))
            .join(Contractor, DailyAttendance.contractor_id == Contractor.id)
            .join(GramPanchayat, Contractor.gp_id == GramPanchayat.id)
            .join(Block, GramPanchayat.block_id == Block.id)
            .join(District, Block.district_id == District.id)
        )
        if contractor_id:
            stmt = stmt.where(DailyAttendance.contractor_id == contractor_id)
        if district_id:
            stmt = stmt.where(District.id == district_id)
        if block_id:
            stmt = stmt.where(Block.id == block_id)
        if gp_id:
            stmt = stmt.where(GramPanchayat.id == gp_id)
        if start_date:
            stmt = stmt.where(DailyAttendance.date >= start_date)
        if end_date:
            stmt = stmt.where(DailyAttendance.date <= end_date)
        if skip:
            stmt = stmt.offset(skip)
        if limit:
            stmt = stmt.limit(limit)
        stmt = stmt.order_by(DailyAttendance.date.desc(), DailyAttendance.start_time.desc())
        result = await self.db.execute(stmt)
        attendances = result.scalars().all()
        return AttendanceListResponse(
            attendances=[get_attendance_response_from_db(a) for a in attendances],
            total=len(attendances),
            page=1,
            limit=limit or len(attendances),
            total_pages=1,
        )

    async def get_attendance_overview(
        self,
        start_date: date,
        end_date: date,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        gp_id: Optional[int] = None,
    ) -> AttendanceOverviewResponse:
        """Get attendance overview including total contractors, attendance rate, present and absent counts."""
        if end_date < start_date:
            raise HTTPException(detail="end_date must be greater than or equal to start_date", status_code=400)
        if end_date - start_date > timedelta(days=370):
            raise HTTPException(detail="Date range should not exceed 1 year", status_code=400)
        present_count: Optional[int] = None
        absent_count: Optional[int] = None
        total_contractors: int = 0
        attendance_rate: float = 0.0

        # Count the number of Contractors in the given geo filters
        contractors_count_query = select(func.count(func.distinct(Contractor.id)))  # pylint: disable=E1102
        if gp_id:
            contractors_count_query = contractors_count_query.where(Contractor.gp_id == gp_id)
        elif block_id:
            contractors_count_query = contractors_count_query.join(
                GramPanchayat, Contractor.gp_id == GramPanchayat.id
            ).where(GramPanchayat.block_id == block_id)
        elif district_id:
            contractors_count_query = (
                contractors_count_query.join(GramPanchayat, Contractor.gp_id == GramPanchayat.id)
                .join(Block, GramPanchayat.block_id == Block.id)
                .where(Block.district_id == district_id)
            )
        contractors_count_result = await self.db.execute(contractors_count_query)
        total_contractors = contractors_count_result.scalar() or 0
        if start_date == end_date:
            present_count_query = select(func.count(func.distinct(DailyAttendance.contractor_id)))  # pylint: disable=E1102
            present_count_query = (
                present_count_query.select_from(DailyAttendance)
                .join(Contractor, DailyAttendance.contractor_id == Contractor.id)
                .where(
                    DailyAttendance.date == start_date,
                )
            )
            if gp_id:
                present_count_query = present_count_query.where(Contractor.gp_id == gp_id)
            present_count_result = await self.db.execute(present_count_query)
            present_count = present_count_result.scalar() or 0
            absent_count = total_contractors - present_count
            attendance_rate = (present_count / total_contractors * 100) if total_contractors > 0 else 0.0
        else:
            # Count of non Sundays in the date range
            total_days = (end_date - start_date).days + 1
            total_non_sundays = sum(1 for i in range(total_days) if (start_date + timedelta(days=i)).weekday() < 6)
            # Count the number of unique attendance records in the date range in the given geo filters
            present_count_query = select(func.count(func.distinct(DailyAttendance.id)))  # pylint: disable=E1102
            present_count_query = (
                present_count_query.select_from(DailyAttendance)
                .join(Contractor, DailyAttendance.contractor_id == Contractor.id)
                .where(
                    DailyAttendance.date >= start_date,
                    DailyAttendance.date <= end_date,
                )
            )
            if gp_id:
                present_count_query = present_count_query.where(Contractor.gp_id == gp_id)
            elif block_id:
                present_count_query = present_count_query.join(
                    GramPanchayat, Contractor.gp_id == GramPanchayat.id
                ).where(GramPanchayat.block_id == block_id)
            elif district_id:
                present_count_query = (
                    present_count_query.join(GramPanchayat, Contractor.gp_id == GramPanchayat.id)
                    .join(Block, GramPanchayat.block_id == Block.id)
                    .where(Block.district_id == district_id)
                )
            present_count_result = await self.db.execute(present_count_query)
            total_attendance_records = present_count_result.scalar() or 0
            attendance_rate = (
                total_attendance_records / (total_contractors * total_non_sundays) * 100
                if total_contractors > 0 and total_non_sundays > 0
                else 0.0
            )

        return AttendanceOverviewResponse(
            total_contractors=total_contractors,
            attendance_rate=attendance_rate,
            present=present_count,
            absent=absent_count,
        )

    async def get_top_n_geo_attendance(
        self,
        level: GeoTypeEnum,
        start_date: date,
        end_date: date,
        n: int = 3,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
    ) -> list[TopNGeoAttendanceResponse]:
        """Get top N geographical attendance records."""
        # Calculate start and end dates for the month
        # working days in the month (exclude Sundays)
        total_days = (end_date - start_date).days + 1
        working_days = sum(1 for i in range(total_days) if (start_date + timedelta(days=i)).weekday() < 6)

        # Build total contractors subquery and main query depending on level
        if level == GeoTypeEnum.GP:
            total_contractors_subq = (
                select(
                    GramPanchayat.id.label("gp_id"),
                    func.count(func.distinct(Contractor.id)).label("total_contractors"),
                )
                .select_from(GramPanchayat)
                .join(Contractor, Contractor.gp_id == GramPanchayat.id)
                .group_by(GramPanchayat.id)
            ).subquery()

            query = (
                select(
                    GramPanchayat.id.label("geo_id"),
                    GramPanchayat.name.label("geo_name"),
                    total_contractors_subq.c.total_contractors,
                    func.count(func.distinct(DailyAttendance.id)).label("present_count"),
                )
                .select_from(DailyAttendance)
                .join(Contractor, DailyAttendance.contractor_id == Contractor.id)
                .join(GramPanchayat, Contractor.gp_id == GramPanchayat.id)
                .outerjoin(total_contractors_subq, GramPanchayat.id == total_contractors_subq.c.gp_id)
                .where(DailyAttendance.date >= start_date, DailyAttendance.date <= end_date)
                .group_by(GramPanchayat.id, GramPanchayat.name, total_contractors_subq.c.total_contractors)
            )
            if block_id:
                query = query.where(GramPanchayat.block_id == block_id)
            if district_id:
                query = query.join(Block, GramPanchayat.block_id == Block.id).where(Block.district_id == district_id)

        elif level == GeoTypeEnum.BLOCK:
            total_contractors_subq = (
                select(
                    Block.id.label("block_id"),
                    func.count(func.distinct(Contractor.id)).label("total_contractors"),
                )
                .select_from(Block)
                .join(GramPanchayat, GramPanchayat.block_id == Block.id)
                .join(Contractor, Contractor.gp_id == GramPanchayat.id)
                .group_by(Block.id)
            ).subquery()

            query = (
                select(
                    Block.id.label("geo_id"),
                    Block.name.label("geo_name"),
                    total_contractors_subq.c.total_contractors,
                    func.count(func.distinct(DailyAttendance.id)).label("present_count"),
                )
                .select_from(DailyAttendance)
                .join(Contractor, DailyAttendance.contractor_id == Contractor.id)
                .join(GramPanchayat, Contractor.gp_id == GramPanchayat.id)
                .join(Block, GramPanchayat.block_id == Block.id)
                .outerjoin(total_contractors_subq, Block.id == total_contractors_subq.c.block_id)
                .where(DailyAttendance.date >= start_date, DailyAttendance.date <= end_date)
                .group_by(Block.id, Block.name, total_contractors_subq.c.total_contractors)
            )
            if district_id:
                query = query.where(Block.district_id == district_id)
            if block_id:
                query = query.where(Block.id == block_id)

        else:  # DISTRICT
            total_contractors_subq = (
                select(
                    District.id.label("dist_id"),
                    func.count(func.distinct(Contractor.id)).label("total_contractors"),
                )
                .select_from(District)
                .join(Block, Block.district_id == District.id)
                .join(GramPanchayat, GramPanchayat.block_id == Block.id)
                .join(Contractor, Contractor.gp_id == GramPanchayat.id)
                .group_by(District.id)
            ).subquery()

            query = (
                select(
                    District.id.label("geo_id"),
                    District.name.label("geo_name"),
                    total_contractors_subq.c.total_contractors,
                    func.count(func.distinct(DailyAttendance.id)).label("present_count"),
                )
                .select_from(DailyAttendance)
                .join(Contractor, DailyAttendance.contractor_id == Contractor.id)
                .join(GramPanchayat, Contractor.gp_id == GramPanchayat.id)
                .join(Block, GramPanchayat.block_id == Block.id)
                .join(District, Block.district_id == District.id)
                .outerjoin(total_contractors_subq, District.id == total_contractors_subq.c.dist_id)
                .where(DailyAttendance.date >= start_date, DailyAttendance.date <= end_date)
                .group_by(District.id, District.name, total_contractors_subq.c.total_contractors)
            )
            if district_id:
                query = query.where(District.id == district_id)

        # order by present_count descending and limit
        query = query.order_by(func.count(func.distinct(DailyAttendance.id)).desc()).limit(n)

        # Execute and build responses
        result = await self.db.execute(query)
        rows = result.fetchall()

        responses: list[TopNGeoAttendanceResponse] = []
        working_days = max(working_days, 1)  # avoid division by zero
        for row in rows:
            geo_id = row.geo_id
            geo_name = row.geo_name
            total_contractors = row.total_contractors or 0
            present_count = row.present_count or 0

            denom = total_contractors * working_days
            attendance_rate = (present_count / denom * 100) if denom > 0 else 0.0

            responses.append(
                TopNGeoAttendanceResponse(
                    geo_type=level,
                    geo_id=geo_id,
                    geo_name=geo_name,
                    attendance_rate=attendance_rate,
                )
            )

        return responses

    async def get_monthly_attendance_performance(
        self,
        level: GeoTypeEnum,
        start_date: date,
        end_date: date,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        gp_id: Optional[int] = None,
    ) -> List[MonthlyAttendanceTrendResponse]:
        """
        Get monthly attendance performance.
        Returns attendance statistics for the specified month.
        """
        if (district_id and block_id) or (district_id and gp_id) or (block_id and gp_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide only one of district_id, block_id, or gp_id",
            )
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date must be less than or equal to end_date",
            )
        if start_date.day != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date must be the first day of the month",
            )
        # Build base query
        if level == GeoTypeEnum.GP:
            geo_model = GramPanchayat
        elif level == GeoTypeEnum.BLOCK:
            geo_model = Block
        elif level == GeoTypeEnum.DISTRICT:
            geo_model = District
        query = (
            select(
                geo_model.id.label("geo_id"),
                geo_model.name.label("geo_name"),
                func.date_trunc(literal_column("'month'"), DailyAttendance.date).label("month"),
                func.count(func.distinct(DailyAttendance.id)).label("present_count"),
                func.count(func.distinct(Contractor.id)).label("total_contractors"),
            )
            .select_from(DailyAttendance)
            .join(Contractor, DailyAttendance.contractor_id == Contractor.id)
            .join(GramPanchayat, Contractor.gp_id == GramPanchayat.id)
            .join(Block, GramPanchayat.block_id == Block.id)
            .join(District, Block.district_id == District.id)
            .where(DailyAttendance.date >= start_date, DailyAttendance.date <= end_date)
            .group_by(geo_model.id, geo_model.name, func.date_trunc(literal_column("'month'"), DailyAttendance.date))
            .order_by(func.date_trunc(literal_column("'month'"), DailyAttendance.date).asc())
        )
        if district_id:
            query = query.where(Block.district_id == district_id)
        if block_id:
            query = query.where(GramPanchayat.block_id == block_id)
        if gp_id:
            query = query.where(Contractor.gp_id == gp_id)
        result = await self.db.execute(query)
        rows = result.fetchall()
        responses: List[MonthlyAttendanceTrendResponse] = []
        for row in rows:
            geo_id = row.geo_id
            geo_name = row.geo_name
            month = row.month
            present_count = row.present_count or 0
            total_contractors = row.total_contractors or 0

            # Calculate working days in the month (exclude Sundays)
            month_start = month.date()
            if month_start < start_date:
                month_start = start_date
            month_end = date(month.year, month.month + 1, 1) - timedelta(days=1)
            if month_end > end_date:
                month_end = end_date
            total_days = (month_end - month_start).days + 1
            working_days = sum(1 for i in range(total_days) if (month_start + timedelta(days=i)).weekday() < 6)

            denom = total_contractors * working_days
            attendance_rate = (present_count / denom * 100) if denom > 0 else 0.0

            responses.append(
                MonthlyAttendanceTrendResponse(
                    geo_type=level,
                    geo_id=geo_id,
                    geo_name=geo_name,
                    month=month.month,
                    year=month.year,
                    attendance_rate=attendance_rate,
                )
            )
        return responses

    async def get_annual_geo_performance(
        self,
        level: GeoTypeEnum,
        year: int,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        gp_id: Optional[int] = None,
    ) -> List[AnnualGeoPerformanceResponse]:
        """
        Get annual attendance performance for geographical units.
        Returns attendance statistics for the specified year.
        """
        start_date = date(year, 1, 1)
        end_date = min(date(year, 12, 31), date.today())

        # Build base query
        if level == GeoTypeEnum.GP:
            geo_model = GramPanchayat
        elif level == GeoTypeEnum.BLOCK:
            geo_model = Block
        elif level == GeoTypeEnum.DISTRICT:
            geo_model = District

        query = (
            select(
                geo_model.id.label("geo_id"),
                geo_model.name.label("geo_name"),
                func.count(func.distinct(DailyAttendance.id)).label("present_count"),
                func.count(func.distinct(Contractor.id)).label("total_contractors"),
            )
            .select_from(DailyAttendance)
            .join(Contractor, DailyAttendance.contractor_id == Contractor.id)
            .join(GramPanchayat, Contractor.gp_id == GramPanchayat.id)
            .join(Block, GramPanchayat.block_id == Block.id)
            .join(District, Block.district_id == District.id)
            .where(DailyAttendance.date >= start_date, DailyAttendance.date <= end_date)
            .group_by(geo_model.id, geo_model.name)
        )

        if district_id:
            query = query.where(Block.district_id == district_id)
        if block_id:
            query = query.where(GramPanchayat.block_id == block_id)
        if gp_id:
            query = query.where(Contractor.gp_id == gp_id)

        query = query.order_by(geo_model.id.asc())
        result = await self.db.execute(query)
        rows = result.fetchall()

        responses: List[AnnualGeoPerformanceResponse] = []
        # Calculate total working days in the year (exclude Sundays)
        total_days = (end_date - start_date).days + 1
        print("Total Days:", total_days)
        working_days = sum(1 for i in range(total_days) if (start_date + timedelta(days=i)).weekday() < 6)

        for row in rows:
            geo_id = row.geo_id
            geo_name = row.geo_name
            present_count = row.present_count
            total_contractors = row.total_contractors
            denom = total_contractors * working_days
            attendance_rate = (present_count / denom * 100) if denom > 0 else 0.0
            responses.append(
                AnnualGeoPerformanceResponse(
                    geo_type=level,
                    geo_id=geo_id,
                    year=year,
                    geo_name=geo_name,
                    attendance_rate=attendance_rate,
                    working_days=working_days,
                    present_days=present_count,
                )
            )
        return responses

    async def get_monthly_aggregated_geo_performance(
        self,
        year: int,
    ) -> List[MonthlyAggregation]:
        """
        Get monthly aggregated attendance performance across all geographical levels.
        Returns attendance statistics for the specified year.
        """
        start_date = date(year, 1, 1)
        end_date = min(date(year, 12, 31), date.today())

        # Build base query
        query = (
            select(
                func.date_trunc(literal_column("'month'"), DailyAttendance.date).label("month"),
                func.count(func.distinct(DailyAttendance.id)).label("present_count"),
                func.count(func.distinct(Contractor.id)).label("total_contractors"),
            )
            .select_from(DailyAttendance)
            .join(Contractor, DailyAttendance.contractor_id == Contractor.id)
            .where(DailyAttendance.date >= start_date, DailyAttendance.date <= end_date)
            .group_by(func.date_trunc(literal_column("'month'"), DailyAttendance.date))
            .order_by(func.date_trunc(literal_column("'month'"), DailyAttendance.date).asc())
        )

        result = await self.db.execute(query)
        rows = result.fetchall()

        # Get the number of contractors
        total_contractors_query = select(func.count(func.distinct(Contractor.id)))  # pylint: disable=E1102
        total_contractors_result = await self.db.execute(total_contractors_query)
        total_contractors = total_contractors_result.scalar() or 0

        responses: List[MonthlyAggregation] = []
        for row in rows:
            month = row.month
            present_count = row.present_count or 0

            # Calculate working days in the month (exclude Sundays)
            month_start = month.date()
            if month_start < start_date:
                month_start = start_date
            month_end = date(month.year, month.month + 1, 1) - timedelta(days=1)
            if month_end > end_date:
                month_end = end_date
            total_days = (month_end - month_start).days + 1
            working_days = sum(1 for i in range(total_days) if (month_start + timedelta(days=i)).weekday() < 6)

            denom = total_contractors * working_days
            attendance_rate = (present_count / denom * 100) if denom > 0 else 0.0

            item = MonthlyAggregation(
                month=month.month,
                year=month.year,
                # working_days=working_days,
                # present_count=present_count,
                attendance_rate=attendance_rate,
            )
            responses.append(item)
        return responses
