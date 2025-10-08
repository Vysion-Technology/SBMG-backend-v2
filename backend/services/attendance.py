from typing import List, Optional, Dict, Any
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import joinedload

from models.database.attendance import DailyAttendance
from models.database.contractor import Contractor
from models.database.geography import GramPanchayat, Block
from models.database.auth import User
from models.requests.attendance import (
    AttendanceLogRequest,
    AttendanceEndRequest,
    AttendanceFilterRequest,
)
from models.response.attendance import (
    AttendanceResponse,
    AttendanceListResponse,
    AttendanceSummaryResponse,
    AttendanceStatsResponse,
)


class AttendanceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_attendance(
        self, contractor_id: int, request: AttendanceLogRequest
    ) -> DailyAttendance:
        """Log worker attendance (start of work day)"""
        # Check if attendance already exists for this contractor and date
        existing_attendance = await self.db.execute(
            select(DailyAttendance).where(
                and_(
                    DailyAttendance.contractor_id == contractor_id,
                    DailyAttendance.date == request.date,
                )
            )
        )
        existing = existing_attendance.scalar_one_or_none()

        if existing:
            raise ValueError("Attendance already logged for this date")

        # Create new attendance record
        attendance = DailyAttendance(
            contractor_id=contractor_id,
            village_id=request.village_id,
            date=request.date,
            start_time=datetime.now(),
            start_lat=request.start_lat,
            start_long=request.start_long,
            remarks=request.remarks,
        )

        self.db.add(attendance)
        await self.db.commit()
        await self.db.refresh(attendance)

        return attendance

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
        result = await self.db.execute(
            select(DailyAttendance)
            .options(
                joinedload(DailyAttendance.contractor).joinedload(Contractor.agency),
                joinedload(DailyAttendance.village)
                .joinedload(GramPanchayat.block)
                .joinedload(Block.district),
            )
            .where(DailyAttendance.id == attendance_id)
        )
        return result.scalar_one_or_none()

    async def get_contractor_attendances(
        self,
        contractor_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[DailyAttendance]:
        """Get attendance records for a specific contractor"""
        query = select(DailyAttendance).where(
            DailyAttendance.contractor_id == contractor_id
        )

        if start_date:
            query = query.where(DailyAttendance.date >= start_date)
        if end_date:
            query = query.where(DailyAttendance.date <= end_date)

        query = query.order_by(DailyAttendance.date.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_filtered_attendances(
        self, filters: AttendanceFilterRequest, user_jurisdiction: Dict[str, Any]
    ) -> AttendanceListResponse:
        """Get filtered attendance records based on user's jurisdiction"""
        # Build base query with joins
        query = select(DailyAttendance).options(
            joinedload(DailyAttendance.contractor).joinedload(Contractor.agency),
            joinedload(DailyAttendance.village)
            .joinedload(GramPanchayat.block)
            .joinedload(Block.district),
        )

        # Apply jurisdiction filters based on user's role and geographic scope
        if user_jurisdiction.get("village_ids"):
            query = query.where(
                DailyAttendance.village_id.in_(user_jurisdiction["village_ids"])
            )
        elif user_jurisdiction.get("block_ids"):
            # Join with village to filter by block
            query = query.join(GramPanchayat).where(
                GramPanchayat.block_id.in_(user_jurisdiction["block_ids"])
            )
        elif user_jurisdiction.get("district_ids"):
            # Join with village to filter by district
            query = query.join(GramPanchayat).where(
                GramPanchayat.district_id.in_(user_jurisdiction["district_ids"])
            )

        # Apply additional filters
        if filters.contractor_id:
            query = query.where(DailyAttendance.contractor_id == filters.contractor_id)
        if filters.village_id:
            query = query.where(DailyAttendance.village_id == filters.village_id)
        if filters.start_date:
            query = query.where(DailyAttendance.date >= filters.start_date)
        if filters.end_date:
            query = query.where(DailyAttendance.date <= filters.end_date)

        # Get total count
        count_query = select(func.count(DailyAttendance.id)).select_from(
            query.subquery()
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (filters.page - 1) * filters.limit
        query = query.offset(offset).limit(filters.limit)
        query = query.order_by(
            DailyAttendance.date.desc(), DailyAttendance.start_time.desc()
        )

        # Execute query
        result = await self.db.execute(query)
        attendances = list(result.scalars().all())

        # Convert to response models
        attendance_responses: List[AttendanceResponse] = []
        for attendance in attendances:
            attendance_responses.append(
                AttendanceResponse(
                    id=attendance.id,
                    contractor_id=attendance.contractor_id,
                    contractor_name=attendance.contractor.person_name
                    if attendance.contractor
                    else None,
                    village_id=attendance.village_id,
                    village_name=attendance.village.name
                    if attendance.village
                    else None,
                    block_name=attendance.village.block.name
                    if attendance.village and attendance.village.block
                    else None,
                    district_name=attendance.village.district.name
                    if attendance.village and attendance.village.district
                    else None,
                    date=attendance.date,
                    start_time=attendance.start_time,
                    start_lat=attendance.start_lat or "",
                    start_long=attendance.start_long or "",
                    end_time=attendance.end_time,
                    end_lat=attendance.end_lat,
                    end_long=attendance.end_long,
                    remarks=attendance.remarks,
                )
            )

        total_pages = (total + filters.limit - 1) // filters.limit

        return AttendanceListResponse(
            attendances=attendance_responses,
            total=total,
            page=filters.page,
            limit=filters.limit,
            total_pages=total_pages,
        )

    async def get_attendance_stats(
        self,
        user_jurisdiction: Dict[str, Any],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> AttendanceStatsResponse:
        """Get attendance statistics for user's jurisdiction"""
        # Get contractors in user's jurisdiction
        contractors_query = select(Contractor).options(
            joinedload(Contractor.village)
            .joinedload(GramPanchayat.block)
            .joinedload(Block.district)
        )

        # Apply jurisdiction filters
        if user_jurisdiction.get("village_ids"):
            contractors_query = contractors_query.where(
                Contractor.village_id.in_(user_jurisdiction["village_ids"])
            )
        elif user_jurisdiction.get("block_ids"):
            contractors_query = contractors_query.join(GramPanchayat).where(
                GramPanchayat.block_id.in_(user_jurisdiction["block_ids"])
            )
        elif user_jurisdiction.get("district_ids"):
            contractors_query = contractors_query.join(GramPanchayat).where(
                GramPanchayat.district_id.in_(user_jurisdiction["district_ids"])
            )

        contractors_result = await self.db.execute(contractors_query)
        contractors = list(contractors_result.scalars().all())

        contractor_ids = [c.id for c in contractors]

        if not contractor_ids:
            return AttendanceStatsResponse(
                total_workers=0,
                present_today=0,
                absent_today=0,
                attendance_rate=0.0,
                summaries=[],
            )

        # Get attendance counts for today
        today = date.today()
        present_today_query = select(
            func.count(func.distinct(DailyAttendance.contractor_id))
        ).where(
            and_(
                DailyAttendance.contractor_id.in_(contractor_ids),
                DailyAttendance.date == today,
            )
        )
        present_today_result = await self.db.execute(present_today_query)
        present_today = present_today_result.scalar() or 0

        # Calculate attendance summaries for each contractor
        summaries = []
        for contractor in contractors:
            summary = await self._get_contractor_summary(
                contractor, start_date, end_date
            )
            summaries.append(summary)

        total_workers = len(contractors)
        absent_today = total_workers - present_today
        attendance_rate = (
            (present_today / total_workers * 100) if total_workers > 0 else 0.0
        )

        return AttendanceStatsResponse(
            total_workers=total_workers,
            present_today=present_today,
            absent_today=absent_today,
            attendance_rate=attendance_rate,
            summaries=summaries,
        )

    async def _get_contractor_summary(
        self,
        contractor: Contractor,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> AttendanceSummaryResponse:
        """Get attendance summary for a specific contractor"""
        # Default to last 30 days if no date range provided
        if not start_date:
            start_date = date.today().replace(day=1)  # Start of current month
        if not end_date:
            end_date = date.today()

        # Count total working days in period (excluding weekends)
        total_days_query = text("""
            SELECT COUNT(*)
            FROM generate_series(:start_date::date, :end_date::date, '1 day'::interval) AS day
            WHERE EXTRACT(ISODOW FROM day) < 6
        """)
        total_days_result = await self.db.execute(
            total_days_query, {"start_date": start_date, "end_date": end_date}
        )
        total_days = total_days_result.scalar() or 0

        # Count present days
        present_days_query = select(func.count(DailyAttendance.id)).where(
            and_(
                DailyAttendance.contractor_id == contractor.id,
                DailyAttendance.date >= start_date,
                DailyAttendance.date <= end_date,
            )
        )
        present_days_result = await self.db.execute(present_days_query)
        present_days = present_days_result.scalar() or 0

        # Get last attendance date
        last_attendance_query = select(func.max(DailyAttendance.date)).where(
            DailyAttendance.contractor_id == contractor.id
        )
        last_attendance_result = await self.db.execute(last_attendance_query)
        last_attendance = last_attendance_result.scalar()

        attendance_percentage = (
            (present_days / total_days * 100) if total_days > 0 else 0.0
        )

        return AttendanceSummaryResponse(
            contractor_id=contractor.id,
            contractor_name=contractor.person_name,
            total_days=total_days,
            present_days=present_days,
            attendance_percentage=attendance_percentage,
            last_attendance=last_attendance,
        )

    async def get_user_jurisdiction(self, user: User) -> Dict[str, Any]:
        """Get user's jurisdiction based on their roles and positions"""
        jurisdiction = {
            "village_ids": [],
            "block_ids": [],
            "district_ids": [],
            "is_admin": False,
        }

        for position in user.positions:
            role_name = position.role.name.upper()

            if role_name == "ADMIN":
                jurisdiction["is_admin"] = True
                # Admin can see all
                return jurisdiction
            elif role_name == "CEO":
                # CEO can see entire district
                if position.district_id:
                    jurisdiction["district_ids"].append(position.district_id)
            elif role_name == "BDO":
                # BDO can see entire block
                if position.block_id:
                    jurisdiction["block_ids"].append(position.block_id)
            elif role_name == "VDO":
                # VDO can see specific village
                if position.village_id:
                    jurisdiction["village_ids"].append(position.village_id)

        return jurisdiction
