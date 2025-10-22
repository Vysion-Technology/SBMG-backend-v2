"""Attendance service for managing worker attendance records."""

from typing import Optional

from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, func, and_, case
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
    AttendanceResponse,
    AttendanceListResponse,
    AttendanceAnalyticsResponse,
    GeographyAttendanceCountResponse,
    DayAttendanceSummaryResponse,
    DaySummaryAttendanceResponse,
)


def get_attendance_response_from_db(attendance: DailyAttendance) -> AttendanceResponse:
    """Convert DailyAttendance DB model to AttendanceResponse model"""
    return AttendanceResponse(
        id=attendance.id,
        contractor_id=attendance.contractor_id,
        contractor_name=attendance.contractor.person_name
        if attendance.contractor
        else None,
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

    async def log_attendance(
        self, contractor_id: int, request: AttendanceLogRequest
    ) -> DailyAttendance:
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

    async def end_attendance(
        self, contractor_id: int, request: AttendanceEndRequest
    ) -> DailyAttendance:
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
            attendance.remarks = (
                f"{attendance.remarks or ''}\nEnd: {request.remarks}".strip()
            )

        await self.db.commit()
        await self.db.refresh(attendance)

        return attendance

    async def get_attendance_by_id(
        self, attendance_id: int
    ) -> Optional[DailyAttendance]:
        """Get attendance record by ID with all relations loaded"""
        stmt = (
            select(DailyAttendance)
            .options(
                joinedload(DailyAttendance.contractor).joinedload(Contractor.agency)
            )
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
            # Get all contractors grouped by district
            query = (
                select(
                    District.id,
                    District.name,
                    func.count(func.distinct(Contractor.id)).label("total_contractors"),  # type: ignore
                    func.count(
                        func.distinct(  # type: ignore
                            case(
                                (
                                    and_(
                                        DailyAttendance.date >= start_date,
                                        DailyAttendance.date <= end_date,
                                    ),
                                    DailyAttendance.contractor_id,
                                )
                            )
                        )
                    ).label("present_count"),
                    DailyAttendance.date,
                )
                .select_from(District)
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
                .group_by(District.id, District.name, DailyAttendance.date)
            )

            if district_id:
                query = query.where(District.id == district_id)

        elif level == GeoTypeEnum.BLOCK:
            # Get all contractors grouped by block
            query = (
                select(
                    Block.id,
                    Block.name,
                    func.count(func.distinct(Contractor.id)).label("total_contractors"),
                    func.count(
                        func.distinct(
                            case(
                                (
                                    and_(
                                        DailyAttendance.date >= start_date,
                                        DailyAttendance.date <= end_date,
                                    ),
                                    DailyAttendance.contractor_id,
                                )
                            )
                        )
                    ).label("present_count"),
                    DailyAttendance.date,
                )
                .select_from(Block)
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
                .group_by(Block.id, Block.name, DailyAttendance.date)
            )

            if district_id:
                query = query.where(Block.district_id == district_id)
            if block_id:
                query = query.where(Block.id == block_id)

        else:  # GP level
            # Get all contractors grouped by village/GP
            query = (
                select(
                    GramPanchayat.id,
                    GramPanchayat.name,
                    func.count(func.distinct(Contractor.id)).label("total_contractors"),
                    func.count(
                        func.distinct(
                            case(
                                (
                                    and_(
                                        DailyAttendance.date >= start_date,
                                        DailyAttendance.date <= end_date,
                                    ),
                                    DailyAttendance.contractor_id,
                                )
                            )
                        )
                    ).label("present_count"),
                    DailyAttendance.date,
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
            absent_count = total_contractors - present_count
            attendance_rate = (
                (present_count / total_contractors * 100)
                if total_contractors > 0
                else 0.0
            )

            response_items.append(
                GeographyAttendanceCountResponse(
                    date=__date,
                    geography_id=geography_id,
                    geography_name=geography_name,
                    total_contractors=total_contractors,
                    present_count=present_count,
                    absent_count=absent_count,
                    attendance_rate=attendance_rate,
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
            select(func.count(func.distinct(Contractor.id)))  # type: ignore
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
        attendance_rate = (
            (present_count / total_contractors * 100) if total_contractors > 0 else 0.0
        )

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
            .options(
                joinedload(DailyAttendance.contractor).joinedload(Contractor.agency)
            )
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
        stmt = stmt.order_by(
            DailyAttendance.date.desc(), DailyAttendance.start_time.desc()
        )
        result = await self.db.execute(stmt)
        attendances = result.scalars().all()
        return AttendanceListResponse(
            attendances=[get_attendance_response_from_db(a) for a in attendances],
            total=len(attendances),
            page=1,
            limit=limit or len(attendances),
            total_pages=1,
        )
