import traceback
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.database.auth import User
from models.database.contractor import Contractor
from models.requests.attendance import AttendanceLogRequest, AttendanceEndRequest, AttendanceFilterRequest
from models.response.attendance import AttendanceResponse, AttendanceListResponse, AttendanceStatsResponse
from services.auth import AuthService
from services.attendance import AttendanceService
from exceptions.attendance import NoContractorForVillageError, AttemptingToLogAttendanceForAnotherUserError

# Security
security = HTTPBearer()

# Router
router = APIRouter()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    auth_service = AuthService(db)
    token = credentials.credentials
    user = await auth_service.get_current_user_from_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")
    return user


async def get_contractor_from_user(user: User, db: AsyncSession) -> Contractor:
    """Get contractor record for the authenticated user (for workers)."""
    # For workers, we need to find their contractor record
    # This assumes workers have a username that matches their contractor phone or ID
    # You might need to adjust this logic based on your authentication setup

    from sqlalchemy import select

    result = await db.execute(select(Contractor).where(Contractor.village_id == user.village_id))
    contractor = result.scalar_one_or_none()

    if not contractor:
        raise NoContractorForVillageError("There is no contractor associated with the village.")

    return contractor


@router.post("/log", response_model=AttendanceResponse)
async def log_attendance(
    request: AttendanceLogRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Log worker attendance (start of work day).
    Only workers can log their own attendance.
    """
    try:
        # Get contractor record for this user
        if not request.village_id == current_user.village_id:
            raise AttemptingToLogAttendanceForAnotherUserError("You can only log attendance for your own village.")
        contractor = await get_contractor_from_user(current_user, db)

        # Log attendance
        attendance_service = AttendanceService(db)
        attendance = await attendance_service.log_attendance(contractor.id, request)

        # Get full attendance record for response
        full_attendance = await attendance_service.get_attendance_by_id(attendance.id)

        if not full_attendance:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")

        return AttendanceResponse(
            id=full_attendance.id,
            contractor_id=full_attendance.contractor_id,
            contractor_name=full_attendance.contractor.person_name if full_attendance.contractor else None,
            village_id=full_attendance.contractor.village_id,
            village_name=full_attendance.contractor.village.name
            if full_attendance.contractor and full_attendance.contractor.village
            else None,
            block_name=full_attendance.contractor.village.block.name
            if full_attendance.contractor
            and full_attendance.contractor.village
            and full_attendance.contractor.village.block
            else None,
            district_name=full_attendance.contractor.village.block.district.name
            if full_attendance.contractor
            and full_attendance.contractor.village
            and full_attendance.contractor.village.block
            and full_attendance.contractor.village.block.district
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AssertionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NoContractorForVillageError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while logging attendance"
        ) from e


@router.put("/end", response_model=AttendanceResponse)
async def end_attendance(
    request: AttendanceEndRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")

        return AttendanceResponse(
            id=full_attendance.id,
            contractor_id=full_attendance.contractor_id,
            contractor_name=full_attendance.contractor.person_name if full_attendance.contractor else None,
            village_id=full_attendance.village_id,
            village_name=full_attendance.village.name if full_attendance.village else None,
            block_name=full_attendance.village.block.name
            if full_attendance.village and full_attendance.village.block
            else None,
            district_name=full_attendance.village.district.name
            if full_attendance.village and full_attendance.village.district
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while ending attendance"
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
        # Get contractor record for this user
        contractor = await get_contractor_from_user(current_user, db)

        # Create filter request
        filters = AttendanceFilterRequest(
            contractor_id=contractor.id, start_date=start_date, end_date=end_date, page=page, limit=limit
        )

        # Get attendance records
        attendance_service = AttendanceService(db)
        user_jurisdiction = await attendance_service.get_user_jurisdiction(current_user)

        return await attendance_service.get_filtered_attendances(filters, user_jurisdiction)

    except Exception as e:
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
    page: int = 1,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    View attendance records for officers (VDO/BDO/CEO/ADMIN).
    Officers can only see attendance within their jurisdiction.
    """
    try:
        # Check if user has officer role
        user_roles = [position.role.name.upper() for position in current_user.positions]
        if not any(role in ["VDO", "BDO", "CEO", "ADMIN"] for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to view attendance records"
            )

        # Create filter request
        filters = AttendanceFilterRequest(
            contractor_id=contractor_id,
            village_id=village_id,
            block_id=block_id,
            district_id=district_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            limit=limit,
        )

        # Get user jurisdiction and filtered attendance records
        attendance_service = AttendanceService(db)
        user_jurisdiction = await attendance_service.get_user_jurisdiction(current_user)

        return await attendance_service.get_filtered_attendances(filters, user_jurisdiction)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching attendance records",
        ) from e


@router.get("/stats", response_model=AttendanceStatsResponse)
async def get_attendance_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get attendance statistics for officers (VDO/BDO/CEO/ADMIN).
    Statistics are limited to the officer's jurisdiction.
    """
    try:
        # Check if user has officer role
        user_roles = [position.role.name.upper() for position in current_user.positions]
        if not any(role in ["VDO", "BDO", "CEO", "ADMIN"] for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to view attendance statistics"
            )

        # Get attendance statistics
        attendance_service = AttendanceService(db)
        user_jurisdiction = await attendance_service.get_user_jurisdiction(current_user)

        return await attendance_service.get_attendance_stats(user_jurisdiction, start_date, end_date)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching attendance statistics",
        ) from e


@router.get("/{attendance_id}", response_model=AttendanceResponse)
async def get_attendance_by_id(
    attendance_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")

        # Check permissions
        user_roles = [position.role.name.upper() for position in current_user.positions]

        # If user is a worker, they can only see their own attendance
        if "WORKER" in user_roles:
            try:
                contractor = await get_contractor_from_user(current_user, db)
                if attendance.contractor_id != contractor.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own attendance records"
                    )
            except HTTPException as e:
                if e.status_code == status.HTTP_404_NOT_FOUND:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own attendance records"
                    )
                raise

        # If user is an officer, check jurisdiction
        elif any(role in ["VDO", "BDO", "CEO", "ADMIN"] for role in user_roles):
            user_jurisdiction = await attendance_service.get_user_jurisdiction(current_user)

            # Check if attendance is within user's jurisdiction
            if not user_jurisdiction.get("is_admin"):
                if (
                    user_jurisdiction.get("village_ids")
                    and attendance.village_id not in user_jurisdiction["village_ids"]
                ):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN, detail="Attendance record is outside your jurisdiction"
                    )
                elif (
                    user_jurisdiction.get("block_ids")
                    and attendance.village
                    and attendance.village.block_id not in user_jurisdiction["block_ids"]
                ):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN, detail="Attendance record is outside your jurisdiction"
                    )
                elif (
                    user_jurisdiction.get("district_ids")
                    and attendance.village
                    and attendance.village.district_id not in user_jurisdiction["district_ids"]
                ):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN, detail="Attendance record is outside your jurisdiction"
                    )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to view attendance records"
            )

        return AttendanceResponse(
            id=attendance.id,
            contractor_id=attendance.contractor_id,
            contractor_name=attendance.contractor.person_name if attendance.contractor else None,
            village_id=attendance.village_id,
            village_name=attendance.village.name if attendance.village else None,
            block_name=attendance.village.block.name if attendance.village and attendance.village.block else None,
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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching attendance record",
        ) from e
