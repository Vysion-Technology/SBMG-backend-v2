"""Attendance Controllers: Handles attendance logging and retrieval."""

import traceback
from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.response.contractor import AgencyResponse
from database import get_db

from models.database.auth import User
from models.database.contractor import Contractor
from models.database.geography import GramPanchayat
from models.requests.attendance import (
    AttendanceLogRequest,
    AttendanceEndRequest,
)
from models.response.attendance import (
    AttendanceResponse,
    AttendanceListResponse,
    DayAttendanceSummaryResponse,
    AttendanceAnalyticsResponse,
)
from models.internal import GeoTypeEnum

from services.auth import AuthService, UserRole
from services.attendance import AttendanceService
from services.geography import GeographyService

from exceptions.attendance import (
    NoContractorForVillageError,
    AttemptingToLogAttendanceForAnotherUserError,
)

# Security
security = HTTPBearer()

# Router
router = APIRouter()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user."""
    auth_service = AuthService(db)
    token = credentials.credentials
    user = await auth_service.get_current_user_from_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )
    return user


async def get_contractor_from_user(user: User, db: AsyncSession) -> Contractor:
    """Get contractor record for the authenticated user (for workers)."""
    # For workers, we need to find their contractor record
    # This assumes workers have a username that matches their contractor phone or ID
    # You might need to adjust this logic based on your authentication setup

    result = await db.execute(
        select(Contractor).where(Contractor.gp_id == user.gp_id)
    )
    contractor = result.scalar_one_or_none()

    if not contractor:
        raise NoContractorForVillageError(
            "There is no contractor associated with the village."
        )

    return contractor


@router.post("/log", response_model=AttendanceResponse)
async def log_attendance(
    request: AttendanceLogRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Log worker attendance (start of work day).
    Only workers can log their own attendance.
    """
    try:
        # Get contractor record for this user
        if not request.village_id == current_user.gp_id:
            raise AttemptingToLogAttendanceForAnotherUserError(
                "You can only log attendance for your own village."
            )
        contractor = await get_contractor_from_user(current_user, db)

        # Log attendance
        attendance_service = AttendanceService(db)
        attendance = await attendance_service.log_attendance(contractor.id, request)

        # Get full attendance record for response
        full_attendance = await attendance_service.get_attendance_by_id(attendance.id)

        if not full_attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendance record not found",
            )

        geo_service = GeographyService(db)

        assert current_user.gp_id is not None, "User must have a village_id"

        gp: GramPanchayat = await geo_service.get_village(current_user.gp_id)

        return AttendanceResponse(
            id=full_attendance.id,
            contractor_id=full_attendance.contractor_id,
            contractor_name=contractor.person_name
            if full_attendance.contractor
            else None,
            village_id=gp.id,
            village_name=gp.name,
            block_name=gp.block.name
            if full_attendance.contractor and gp and gp.block
            else None,
            district_name=gp.block.district.name
            if full_attendance.contractor
            and gp
            and gp.block
            and gp.block.district
            else None,
            date=full_attendance.date,
            start_time=full_attendance.start_time,
            start_lat=full_attendance.start_lat or "",
            start_long=full_attendance.start_long or "",
            end_time=full_attendance.end_time,
            end_lat=full_attendance.end_lat,
            end_long=full_attendance.end_long,
            remarks=full_attendance.remarks,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except AssertionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except NoContractorForVillageError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while logging attendance",
        ) from e


@router.put("/end", response_model=AttendanceResponse)
async def end_attendance(
    request: AttendanceEndRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    End worker attendance (end of work day).
    Only workers can end their own attendance.
    """
    try:
        # Get contractor record for this user
        contractor = await get_contractor_from_user(current_user, db)

        # End attendance
        attendance_service = AttendanceService(db)
        attendance = await attendance_service.end_attendance(contractor.id, request)

        # Get full attendance record for response
        full_attendance = await attendance_service.get_attendance_by_id(attendance.id)

        if not full_attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendance record not found",
            )

        geo_service: GeographyService = GeographyService(db)

        assert contractor.gp_id is not None, "Contractor must have a village_id"

        gp: GramPanchayat = await geo_service.get_village(contractor.gp_id)

        return AttendanceResponse(
            id=full_attendance.id,
            contractor_id=full_attendance.contractor_id,
            contractor_name=contractor.person_name
            if full_attendance.contractor
            else None,
            village_id=gp.id,
            village_name=gp.name,
            block_name=gp.block.name if gp.block else None,
            district_name=gp.block.district.name
            if gp.block and gp.block.district
            else None,
            date=full_attendance.date,
            start_time=full_attendance.start_time,
            start_lat=full_attendance.start_lat or "",
            start_long=full_attendance.start_long or "",
            end_time=full_attendance.end_time,
            end_lat=full_attendance.end_lat,
            end_long=full_attendance.end_long,
            remarks=full_attendance.remarks,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while ending attendance",
        ) from e


@router.get("/my", response_model=AttendanceListResponse)
async def get_my_attendance(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = 1,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get attendance records for the authenticated worker.
    """
    try:
        # Check if the user is a contractor/worker
        user_role = AuthService.get_role_by_user(current_user)
        if user_role != UserRole.WORKER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workers can view their own attendance records",
            )
        attendance_svc = AttendanceService(db)
        attendances = await attendance_svc.get_attendances(
            contractor_id=(await get_contractor_from_user(current_user, db)).id,
            start_date=start_date,
            end_date=end_date,
            skip=(page - 1) * limit,
            limit=limit,
        )
        return attendances
    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching attendance records",
        ) from e


@router.get("/view", response_model=AttendanceListResponse)
async def view_attendance(
    contractor_id: Optional[int] = None,
    village_id: Optional[int] = None,
    block_id: Optional[int] = None,
    district_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 500,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AttendanceListResponse:
    """
    View attendance records for officers (VDO/BDO/CEO/ADMIN).
    Officers can only see attendance within their jurisdiction.
    """
    try:
        # Check if user has officer role
        user_role = AuthService.get_role_by_user(current_user)
        if user_role == UserRole.WORKER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=" ".join(
                    [
                        "Workers cannot view attendance records of others. ",
                        "Use the other API to get your attendance records.",
                    ]
                ),
            )

        if not any(role in ["VDO", "BDO", "CEO", "ADMIN"] for role in [user_role]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view attendance records",
            )

        svc = AttendanceService(db)

        return await svc.get_attendances(
            contractor_id=contractor_id,
            gp_id=village_id,
            block_id=block_id,
            district_id=district_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching attendance records",
        ) from e


@router.get("/analytics")
async def get_attendance_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    district_id: Optional[int] = None,
    block_id: Optional[int] = None,
    gp_id: Optional[int] = None,
    level: GeoTypeEnum = GeoTypeEnum.DISTRICT,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: Optional[int] = None,
    limit: Optional[int] = 500,
) -> AttendanceAnalyticsResponse:
    """
    Get attendance analytics aggregated by geographic level.
    Returns attendance statistics for each geographic unit at the specified level.
    """
    try:
        print("Hi" * 100)
        # Permission checks based on user's jurisdiction
        if current_user.block_id is not None and level == GeoTypeEnum.DISTRICT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access district-level analytics",
            )
        if current_user.gp_id is not None and level in [
            GeoTypeEnum.DISTRICT,
            GeoTypeEnum.BLOCK,
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access district or block-level analytics",
            )

        # Validate query parameters
        if (
            (district_id and block_id)
            or (district_id and gp_id)
            or (block_id and gp_id)
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide only one of district_id, block_id, or gp_id",
            )
        if level == GeoTypeEnum.DISTRICT and (district_id or block_id or gp_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Do not provide specific IDs when level is DISTRICT",
            )
        if level == GeoTypeEnum.BLOCK and (block_id or gp_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Do not provide block_id or gp_id when level is BLOCK",
            )

        attendance_service = AttendanceService(db)
        return await attendance_service.attendance_analytics(
            district_id=district_id,
            block_id=block_id,
            gp_id=gp_id,
            level=level,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching attendance analytics",
        ) from e


@router.get("/day-summary")
async def get_attendance_for_day(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    attendance_date: date = date.today(),
    district_id: Optional[int] = None,
    block_id: Optional[int] = None,
    gp_id: Optional[int] = None,
    level: GeoTypeEnum = GeoTypeEnum.DISTRICT,
    skip: Optional[int] = None,
    limit: Optional[int] = 500,
) -> DayAttendanceSummaryResponse:
    """
    Get detailed attendance summary for a specific day.
    Returns all attendance records for the specified date and geographic level.
    """
    # Permission checks based on user's jurisdiction
    if current_user.block_id is not None and level == GeoTypeEnum.DISTRICT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access district-level data",
        )
    if current_user.gp_id is not None and level in [
        GeoTypeEnum.DISTRICT,
        GeoTypeEnum.BLOCK,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access district or block-level data",
        )

    # Validate query parameters
    if (district_id and block_id) or (district_id and gp_id) or (block_id and gp_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide only one of district_id, block_id, or gp_id",
        )

    attendance_service = AttendanceService(db)
    return await attendance_service.get_day_attendance(
        attendance_date=attendance_date,
        district_id=district_id,
        block_id=block_id,
        gp_id=gp_id,
        level=level,
        skip=skip,
        limit=limit,
    )


@router.get("/{attendance_id}", response_model=AttendanceResponse)
async def get_attendance_by_id(
    attendance_id: int,
    # current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get specific attendance record by ID.
    Workers can only see their own attendance.
    Officers can see attendance within their jurisdiction.
    """
    try:
        attendance_service = AttendanceService(db)
        attendance = await attendance_service.get_attendance_by_id(attendance_id)

        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendance record not found",
            )
        contractor = attendance.contractor
        agency = contractor.agency

        geo_svc = GeographyService(db)

        gp: GramPanchayat = await geo_svc.get_village(
            village_id=contractor.gp_id
        )

        return AttendanceResponse(
            id=attendance.id,
            contractor_id=attendance.contractor_id,
            contractor_name=attendance.contractor.person_name
            if attendance.contractor
            else None,
            village_id=gp.id,
            village_name=gp.name,
            block_name=gp.block.name,
            district_name=gp.district.name,
            date=attendance.date,
            start_time=attendance.start_time,
            start_lat=attendance.start_lat or "",
            start_long=attendance.start_long or "",
            end_time=attendance.end_time,
            end_lat=attendance.end_lat,
            end_long=attendance.end_long,
            remarks=attendance.remarks,
            agency=AgencyResponse(
                id=agency.id,
                name=agency.name,
                phone=agency.phone,
                email=agency.email,
                address=agency.address,
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching attendance record",
        ) from e
