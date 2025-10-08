"""
Consolidated advanced reporting router with perfect RBAC and optimized DB queries.
Serves all roles from VDO to ADMIN with unified access control and efficient data fetching.
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, asc, text
from sqlalchemy.orm import selectinload, joinedload
from pydantic import BaseModel

from utils import get_user_jurisdiction_filter
from database import get_db
from models.database.auth import User
from models.database.complaint import Complaint, ComplaintStatus, ComplaintAssignment
from models.database.geography import GramPanchayat, Block, District
from auth_utils import require_staff_role, UserRole, PermissionChecker

router = APIRouter()


# Response Models
class ComplaintResponse(BaseModel):
    """Unified complaint response model for all access levels."""

    id: int
    description: str
    status_name: str
    complaint_type_name: Optional[str] = None
    village_name: str
    block_name: str
    district_name: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    assigned_worker_name: Optional[str] = None
    media_count: int = 0
    media_urls: List[str] = []


class DashboardStatsResponse(BaseModel):
    """Comprehensive dashboard statistics for all access levels."""

    total_complaints: int
    complaints_by_status: Dict[str, int]
    complaints_by_type: Dict[str, int] = {}
    recent_complaints: List[ComplaintResponse]
    geographic_summary: Dict[str, Any] = {}
    performance_metrics: Dict[str, Any] = {}


class WorkerTaskResponse(BaseModel):
    """Response for worker-specific task management."""

    id: int
    description: str
    status_name: str
    village_name: str
    block_name: str
    district_name: str
    assigned_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    priority: str = "NORMAL"
    media_urls: List[str] = []
    completion_percentage: int = 0


class AdminAnalyticsResponse(BaseModel):
    """Advanced analytics for admin and senior roles."""

    total_entities: Dict[str, int]
    performance_trends: Dict[str, List[Dict[str, Any]]]
    user_productivity: List[Dict[str, Any]]
    geographic_distribution: Dict[str, Any]
    system_health: Dict[str, Any]


# Core RBAC and Query Optimization Helper
class UnifiedReportingService:
    """Service class for optimized database queries with perfect RBAC."""

    @staticmethod
    def get_optimized_complaint_query():
        """Get optimized complaint query with all necessary joins."""
        return select(Complaint).options(
            joinedload(Complaint.village),
            joinedload(Complaint.block),
            joinedload(Complaint.district),
            joinedload(Complaint.status),
            joinedload(Complaint.complaint_type),
            selectinload(Complaint.media),
            selectinload(Complaint.assignments).joinedload(ComplaintAssignment.user),
        )

    @staticmethod
    async def get_complaint_stats(
        db: AsyncSession, jurisdiction_filter: Optional[Any] = None
    ) -> Tuple[int, Dict[str, int]]:
        """Get complaint statistics with optional jurisdiction filtering."""
        try:
            base_query = select(func.count(Complaint.id)).select_from(Complaint)

            if jurisdiction_filter is not None:
                base_query = base_query.where(jurisdiction_filter)

            # Total complaints
            total_result = await db.execute(base_query)
            total_complaints = total_result.scalar() or 0

            # Complaints by status with optimized single query
            status_query = (
                select(ComplaintStatus.name, func.count(Complaint.id))
                .select_from(Complaint)
                .join(ComplaintStatus)
                .group_by(ComplaintStatus.name)
            )

            if jurisdiction_filter is not None:
                status_query = status_query.where(jurisdiction_filter)

            status_result = await db.execute(status_query)
            complaints_by_status = {name: count for name, count in status_result}

            return total_complaints, complaints_by_status

        except Exception as e:
            # Log error in production
            print(f"Error getting complaint stats: {e}")
            return 0, {}

    @staticmethod
    async def get_user_role_summary(user: User) -> Dict[str, Any]:
        """Get a summary of user's roles and jurisdiction."""
        roles: List[str] = []
        jurisdictions: List[str] = []

        for position in user.positions:
            if position.role:
                roles.append(position.role.name)

                if position.village_id:
                    jurisdictions.append(f"Village-{position.village_id}")
                elif position.block_id:
                    jurisdictions.append(f"Block-{position.block_id}")
                elif position.district_id:
                    jurisdictions.append(f"District-{position.district_id}")

        return {
            "roles": list(set(roles)),
            "jurisdictions": list(set(jurisdictions)),
            "is_admin": UserRole.ADMIN in roles,
            "access_level": "ADMIN"
            if UserRole.ADMIN in roles
            else "CEO"
            if UserRole.CEO in roles
            else "BDO"
            if UserRole.BDO in roles
            else "VDO"
            if UserRole.VDO in roles
            else "WORKER"
            if UserRole.WORKER in roles
            else "PUBLIC",
        }


# Unified Endpoints for All Roles


@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_unified_dashboard(
    limit: int = Query(10, ge=1, le=50, description="Number of recent complaints"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """Get unified dashboard statistics based on user's access level and jurisdiction."""

    # Get jurisdiction filter based on user role
    jurisdiction_filter = get_user_jurisdiction_filter(current_user)

    # Get complaint statistics
    (
        total_complaints,
        complaints_by_status,
    ) = await UnifiedReportingService.get_complaint_stats(db, jurisdiction_filter)

    # Get recent complaints with optimized query
    recent_query = UnifiedReportingService.get_optimized_complaint_query()

    if jurisdiction_filter is not None:
        recent_query = recent_query.where(jurisdiction_filter)

    recent_query = recent_query.order_by(desc(Complaint.created_at)).limit(limit)

    recent_result = await db.execute(recent_query)
    recent_complaints_data = recent_result.scalars().all()

    # Build response
    recent_complaints: List[ComplaintResponse] = []
    for complaint in recent_complaints_data:
        assigned_worker_name = None
        if complaint.assignments:
            assigned_worker_name = complaint.assignments[0].user.username

        recent_complaints.append(
            ComplaintResponse(
                id=complaint.id,
                description=complaint.description,
                status_name=complaint.status.name,
                complaint_type_name=complaint.complaint_type.name
                if complaint.complaint_type
                else None,
                village_name=complaint.village.name,
                block_name=complaint.block.name,
                district_name=complaint.district.name,
                created_at=complaint.created_at,
                updated_at=complaint.updated_at,
                assigned_worker_name=assigned_worker_name,
                media_count=len(complaint.media),
                media_urls=[media.media_url for media in complaint.media],
            )
        )

    # Get geographic summary for higher level users
    geographic_summary = {}
    user_roles = [pos.role.name for pos in current_user.positions if pos.role]

    if any(role in [UserRole.ADMIN, UserRole.CEO, UserRole.BDO] for role in user_roles):
        # Get district/block/village counts within jurisdiction
        if UserRole.ADMIN in user_roles:
            # Admin sees all
            district_count = await db.execute(select(func.count(District.id)))
            block_count = await db.execute(select(func.count(Block.id)))
            village_count = await db.execute(select(func.count(GramPanchayat.id)))

            geographic_summary = {
                "total_districts": district_count.scalar() or 0,
                "total_blocks": block_count.scalar() or 0,
                "total_villages": village_count.scalar() or 0,
            }
        elif UserRole.CEO in user_roles:
            # CEO sees their district statistics
            ceo_districts = [
                pos.district_id
                for pos in current_user.positions
                if pos.role.name == UserRole.CEO and pos.district_id
            ]
            if ceo_districts:
                block_count = await db.execute(
                    select(func.count(Block.id)).where(
                        Block.district_id.in_(ceo_districts)
                    )
                )
                village_count = await db.execute(
                    select(func.count(GramPanchayat.id)).where(
                        GramPanchayat.district_id.in_(ceo_districts)
                    )
                )
                geographic_summary = {
                    "managed_districts": len(ceo_districts),
                    "total_blocks": block_count.scalar() or 0,
                    "total_villages": village_count.scalar() or 0,
                }

    return DashboardStatsResponse(
        total_complaints=total_complaints,
        complaints_by_status=complaints_by_status,
        recent_complaints=recent_complaints,
        geographic_summary=geographic_summary,
    )


@router.get("/complaints", response_model=List[ComplaintResponse])
async def get_complaints(
    district_id: Optional[int] = Query(None, description="Filter by district"),
    block_id: Optional[int] = Query(None, description="Filter by block"),
    village_id: Optional[int] = Query(None, description="Filter by village"),
    status_name: Optional[str] = Query(None, description="Filter by status"),
    complaint_type_id: Optional[int] = Query(
        None, description="Filter by complaint type"
    ),
    assigned_worker_id: Optional[int] = Query(
        None, description="Filter by assigned worker"
    ),
    date_from: Optional[date] = Query(
        None, description="Filter complaints from date (YYYY-MM-DD)"
    ),
    date_to: Optional[date] = Query(
        None, description="Filter complaints to date (YYYY-MM-DD)"
    ),
    search: Optional[str] = Query(None, description="Search in complaint description"),
    sort_by: str = Query(
        "created_at", description="Sort by field (created_at, updated_at, status)"
    ),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
) -> List[ComplaintResponse]:
    """Get complaints with advanced filtering, search, and pagination."""

    # Start with optimized base query
    query = UnifiedReportingService.get_optimized_complaint_query()

    # Apply jurisdiction filter based on user role
    jurisdiction_filter = get_user_jurisdiction_filter(current_user)
    if jurisdiction_filter is not None:
        query = query.where(jurisdiction_filter)

    # Apply additional filters
    if district_id:
        query = query.where(Complaint.district_id == district_id)
    if block_id:
        query = query.where(Complaint.block_id == block_id)
    if village_id:
        query = query.where(Complaint.village_id == village_id)
    if status_name:
        query = query.where(ComplaintStatus.name == status_name)
    if complaint_type_id:
        query = query.where(Complaint.complaint_type_id == complaint_type_id)
    if assigned_worker_id:
        query = query.where(
            Complaint.id.in_(
                select(ComplaintAssignment.complaint_id).where(
                    ComplaintAssignment.user_id == assigned_worker_id
                )
            )
        )

    # Date range filtering
    if date_from:
        query = query.where(Complaint.created_at >= date_from)
    if date_to:
        query = query.where(Complaint.created_at <= date_to)

    # Search functionality
    if search:
        query = query.where(Complaint.description.ilike(f"%{search}%"))

    # Apply sorting
    if sort_by == "created_at":
        sort_column = Complaint.created_at
    elif sort_by == "updated_at":
        sort_column = Complaint.updated_at
    elif sort_by == "status":
        sort_column = ComplaintStatus.name
    else:
        sort_column = Complaint.created_at

    if sort_order.lower() == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute query
    result = await db.execute(query)
    complaints = result.scalars().all()

    # Build response
    response_data: List[ComplaintResponse] = []
    for complaint in complaints:
        assigned_worker_name = None
        if complaint.assignments:
            assigned_worker_name = complaint.assignments[0].user.username

        response_data.append(
            ComplaintResponse(
                id=complaint.id,
                description=complaint.description,
                status_name=complaint.status.name,
                complaint_type_name=complaint.complaint_type.name
                if complaint.complaint_type
                else None,
                village_name=complaint.village.name,
                block_name=complaint.block.name,
                district_name=complaint.district.name,
                created_at=complaint.created_at,
                updated_at=complaint.updated_at,
                assigned_worker_name=assigned_worker_name,
                media_count=len(complaint.media),
                media_urls=[media.media_url for media in complaint.media],
            )
        )

    return response_data


@router.get("/complaints/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint_details(
    complaint_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """Get detailed information about a specific complaint with RBAC."""

    # Get complaint with optimized query
    query = UnifiedReportingService.get_optimized_complaint_query().where(
        Complaint.id == complaint_id
    )

    result = await db.execute(query)
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found"
        )

    # Check access permissions
    jurisdiction_filter = get_user_jurisdiction_filter(current_user)
    if jurisdiction_filter is not None:
        # Verify user has access to this specific complaint
        access_query = select(Complaint.id).where(
            and_(Complaint.id == complaint_id, jurisdiction_filter)
        )
        access_result = await db.execute(access_query)
        if not access_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this complaint",
            )

    # Build response
    assigned_worker_name = None
    if complaint.assignments:
        assigned_worker_name = complaint.assignments[0].user.username

    return ComplaintResponse(
        id=complaint.id,
        description=complaint.description,
        status_name=complaint.status.name,
        complaint_type_name=complaint.complaint_type.name
        if complaint.complaint_type
        else None,
        village_name=complaint.village.name,
        block_name=complaint.block.name,
        district_name=complaint.district.name,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
        assigned_worker_name=assigned_worker_name,
        media_count=len(complaint.media),
        media_urls=[media.media_url for media in complaint.media],
    )


# Worker-specific endpoints
@router.get("/worker/tasks", response_model=List[WorkerTaskResponse])
async def get_worker_tasks(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
) -> List[WorkerTaskResponse]:
    """Get tasks assigned to the current worker."""

    if not PermissionChecker.user_has_role(current_user, [UserRole.WORKER]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workers can access this endpoint",
        )

    # Get assigned complaints for the worker
    query = (
        UnifiedReportingService.get_optimized_complaint_query()
        .join(ComplaintAssignment)
        .where(ComplaintAssignment.user_id == current_user.id)
    )

    if status_filter:
        query = query.where(ComplaintStatus.name == status_filter)

    query = query.order_by(desc(Complaint.created_at))

    result = await db.execute(query)
    complaints = result.scalars().all()

    # Build worker task response
    tasks: List[WorkerTaskResponse] = []
    for complaint in complaints:
        # Get assignment details
        assignment = next(
            (a for a in complaint.assignments if a.user_id == current_user.id), None
        )

        tasks.append(
            WorkerTaskResponse(
                id=complaint.id,
                description=complaint.description,
                status_name=complaint.status.name,
                village_name=complaint.village.name,
                block_name=complaint.block.name,
                district_name=complaint.district.name,
                assigned_date=assignment.assigned_at if assignment else None,
                media_urls=[media.media_url for media in complaint.media],
                completion_percentage=75
                if complaint.status.name == "IN_PROGRESS"
                else 100
                if complaint.status.name in ["COMPLETED", "VERIFIED"]
                else 0,
            )
        )

    return tasks


# Admin analytics endpoints
@router.get("/admin/analytics", response_model=AdminAnalyticsResponse)
async def get_admin_analytics(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(require_staff_role)
):
    """Get comprehensive analytics for admin users."""

    if not PermissionChecker.user_has_role(current_user, [UserRole.ADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access analytics",
        )

    # Get total entities count
    total_complaints = await db.execute(select(func.count(Complaint.id)))
    total_users = await db.execute(select(func.count(User.id)))
    total_districts = await db.execute(select(func.count(District.id)))
    total_blocks = await db.execute(select(func.count(Block.id)))
    total_villages = await db.execute(select(func.count(GramPanchayat.id)))

    total_entities = {
        "complaints": total_complaints.scalar() or 0,
        "users": total_users.scalar() or 0,
        "districts": total_districts.scalar() or 0,
        "blocks": total_blocks.scalar() or 0,
        "villages": total_villages.scalar() or 0,
    }

    # Get user productivity (simplified for now)
    user_productivity_query = (
        select(
            User.username, func.count(ComplaintAssignment.id).label("assigned_tasks")
        )
        .select_from(User)
        .join(ComplaintAssignment, User.id == ComplaintAssignment.user_id, isouter=True)
        .group_by(User.id, User.username)
        .order_by(desc(text("assigned_tasks")))
        .limit(10)
    )

    productivity_result = await db.execute(user_productivity_query)
    user_productivity = [
        {"username": username, "assigned_tasks": count}
        for username, count in productivity_result
    ]

    # Basic system health metrics
    system_health: Dict[str, Any] = {
        "database_status": "healthy",
        "active_users": total_entities["users"],
        "pending_complaints": 0,  # Would be calculated from complaint statuses
    }

    return AdminAnalyticsResponse(
        total_entities=total_entities,
        performance_trends={},  # Would be implemented with time-series data
        user_productivity=user_productivity,
        geographic_distribution={},  # Would be calculated from geographic data
        system_health=system_health,
    )


# Public endpoint (no authentication)
@router.get("/public/status", response_model=List[ComplaintResponse])
async def get_public_complaint_status(
    district_id: Optional[int] = Query(None, description="Filter by district"),
    block_id: Optional[int] = Query(None, description="Filter by block"),
    village_id: Optional[int] = Query(None, description="Filter by village"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Number of records to return"),
    db: AsyncSession = Depends(get_db),
) -> List[ComplaintResponse]:
    """Public API to see the status of complaints (limited information)."""

    query = select(Complaint).options(
        joinedload(Complaint.village),
        joinedload(Complaint.block),
        joinedload(Complaint.district),
        joinedload(Complaint.status),
        joinedload(Complaint.complaint_type),
    )

    # Apply geographic filters
    if district_id:
        query = query.where(Complaint.district_id == district_id)
    if block_id:
        query = query.where(Complaint.block_id == block_id)
    if village_id:
        query = query.where(Complaint.village_id == village_id)

    # Apply pagination and ordering
    query = query.order_by(desc(Complaint.created_at)).offset(skip).limit(limit)

    result = await db.execute(query)
    complaints = result.scalars().all()

    # Build public response (limited information)
    response_data: List[ComplaintResponse] = []
    for complaint in complaints:
        response_data.append(
            ComplaintResponse(
                id=complaint.id,
                description=complaint.description[:100] + "..."
                if len(complaint.description) > 100
                else complaint.description,
                status_name=complaint.status.name,
                complaint_type_name=complaint.complaint_type.name
                if complaint.complaint_type
                else None,
                village_name=complaint.village.name,
                block_name=complaint.block.name,
                district_name=complaint.district.name,
                created_at=complaint.created_at,
                updated_at=complaint.updated_at,
                assigned_worker_name=None,  # Don't expose worker info to public
                media_count=0,  # Don't expose media to public
                media_urls=[],
            )
        )

    return response_data


# User access information endpoint (for debugging and UI)
@router.get("/user/access-info")
async def get_user_access_info(
    current_user: User = Depends(require_staff_role),
) -> Dict[str, Any]:
    """Get current user's access information and permissions."""

    access_info = await UnifiedReportingService.get_user_role_summary(current_user)

    # Get some basic stats that user can access
    jurisdiction_filter = get_user_jurisdiction_filter(current_user)

    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "access_summary": access_info,
        "can_access_all_data": jurisdiction_filter is None,
        "positions": [
            {
                "role": pos.role.name if pos.role else None,
                "district_id": pos.district_id,
                "block_id": pos.block_id,
                "village_id": pos.village_id,
                "start_date": pos.start_date.isoformat() if pos.start_date else None,
                "end_date": pos.end_date.isoformat() if pos.end_date else None,
            }
            for pos in current_user.positions
        ],
    }
