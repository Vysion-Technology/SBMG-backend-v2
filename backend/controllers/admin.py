from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from database import get_db
from models.database.auth import User, Role, PositionHolder
from models.database.complaint import Complaint, ComplaintStatus, ComplaintType
from models.database.geography import District, Block, GramPanchayat
from models.requests.geography import CreateDistrictRequest
from models.response.geography import (
    CreateBlockRequest,
    CreateGPRequest,
    DistrictResponse,
    BlockResponse,
    GPResponse,
)
from services.auth import AuthService
from auth_utils import require_admin, UserRole
from models.requests.admin import (
    CreateUserRequest,
    CreatePositionHolderRequest,
    CreateRoleRequest,
)
from models.response.admin import UserResponse, RoleResponse

router = APIRouter()


# User Management
@router.post("/users", response_model=UserResponse)
async def create_user(
    user_request: CreateUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new user (Admin only)."""
    auth_service = AuthService(db)

    # Check if username already exists
    existing_user = await auth_service.get_user_by_username(user_request.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )

    user = await auth_service.create_user(
        username=user_request.username,
        email=user_request.email,
        password=user_request.password,
        is_active=user_request.is_active,
    )

    return UserResponse(
        id=user.id, username=user.username, email=user.email, is_active=user.is_active
    )


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    username_like: str = "",
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Get all users with optional filtering (Admin only)."""
    auth_service = AuthService(db)
    users = await auth_service.get_all_users(username_like, skip, limit)

    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
        )
        for user in users
    ]


# Position Holder Management
@router.post("/position-holders")
async def create_position_holder(
    position_request: CreatePositionHolderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, str | int]:
    """Create a new position holder (Admin only)."""
    auth_service = AuthService(db)

    # Get role by name
    role = await auth_service.get_role_by_name(position_request.role_name)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )

    # Verify user exists
    user = await auth_service.get_user_by_id(position_request.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    position = await auth_service.create_position_holder(
        user_id=position_request.user_id,
        role_id=role.id,
        first_name=position_request.first_name,
        middle_name=position_request.middle_name,
        last_name=position_request.last_name,
        village_id=position_request.village_id,
        block_id=position_request.block_id,
        district_id=position_request.district_id,
        start_date=position_request.start_date,
        end_date=position_request.end_date,
    )

    return {"message": "Position holder created successfully", "id": position.id}


# Role Management
@router.post("/roles", response_model=RoleResponse)
async def create_role(
    role_request: CreateRoleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new role (Admin only)."""
    # Check if role already exists
    existing_role = await AuthService(db).get_role_by_name(role_request.name)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Role already exists"
        )

    role = Role(name=role_request.name, description=role_request.description)
    db.add(role)
    await db.commit()
    await db.refresh(role)

    return RoleResponse(id=role.id, name=role.name, description=role.description)


@router.get("/roles", response_model=List[RoleResponse])
async def get_all_roles(
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(require_admin)
):
    """Get all roles (Admin only)."""
    from sqlalchemy import select

    result = await db.execute(select(Role))
    roles = result.scalars().all()

    return [
        RoleResponse(id=role.id, name=role.name, description=role.description)
        for role in roles
    ]


# Geography Management
@router.post("/districts", response_model=DistrictResponse)
async def create_district(
    district_request: CreateDistrictRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new district (Admin only)."""
    # Check if district name is unique
    existing_result = await db.execute(
        select(District).where(District.name == district_request.name)
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="District name already exists")

    district = District(
        name=district_request.name, description=district_request.description
    )
    db.add(district)
    await db.commit()
    await db.refresh(district)

    return DistrictResponse(
        id=district.id, name=district.name, description=district.description
    )


@router.post("/blocks", response_model=BlockResponse)
async def create_block(
    block_request: CreateBlockRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new block (Admin only)."""
    # Validate district exists
    district_result = await db.execute(
        select(District).where(District.id == block_request.district_id)
    )
    if not district_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="District not found")

    # Check if block name is unique within district
    existing_result = await db.execute(
        select(Block).where(
            Block.name == block_request.name,
            Block.district_id == block_request.district_id,
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail="Block name already exists in this district"
        )

    block = Block(
        name=block_request.name,
        description=block_request.description,
        district_id=block_request.district_id,
    )
    db.add(block)
    await db.commit()
    await db.refresh(block)

    return BlockResponse(
        id=block.id,
        name=block.name,
        description=block.description,
        district_id=block.district_id,
    )


@router.post("/villages", response_model=GPResponse)
async def create_village(
    village_request: CreateGPRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new village (Admin only)."""
    # Validate district exists
    district_result = await db.execute(
        select(District).where(District.id == village_request.district_id)
    )
    if not district_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="District not found")

    # Validate block exists and belongs to the district
    block_result = await db.execute(
        select(Block).where(
            Block.id == village_request.block_id,
            Block.district_id == village_request.district_id,
        )
    )
    if not block_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Block not found or doesn't belong to the specified district",
        )

    # Check if village name is unique within block
    existing_result = await db.execute(
        select(GramPanchayat).where(
            GramPanchayat.name == village_request.name,
            GramPanchayat.block_id == village_request.block_id,
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail="Village name already exists in this block"
        )

    village = GramPanchayat(
        name=village_request.name,
        description=village_request.description,
        block_id=village_request.block_id,
        district_id=village_request.district_id,
    )
    db.add(village)
    await db.commit()
    await db.refresh(village)

    return GPResponse(
        id=village.id,
        name=village.name,
        description=village.description,
        block_id=village.block_id,
        district_id=village.district_id,
    )


# Additional Geography CRUD operations


@router.put("/districts/{district_id}", response_model=DistrictResponse)
async def update_district(
    district_id: int,
    district_request: CreateDistrictRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update a district (Admin only)."""
    result = await db.execute(select(District).where(District.id == district_id))
    district = result.scalar_one_or_none()

    if not district:
        raise HTTPException(status_code=404, detail="District not found")

    district.name = district_request.name
    district.description = district_request.description

    await db.commit()
    await db.refresh(district)

    return DistrictResponse(
        id=district.id, name=district.name, description=district.description
    )


@router.delete("/districts/{district_id}")
async def delete_district(
    district_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a district (Admin only)."""
    result = await db.execute(select(District).where(District.id == district_id))
    district = result.scalar_one_or_none()

    if not district:
        raise HTTPException(status_code=404, detail="District not found")

    # Check if district has associated blocks
    blocks_result = await db.execute(
        select(func.count(Block.id)).where(Block.district_id == district_id)
    )
    blocks_count = blocks_result.scalar() or 0

    if blocks_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete district. It has {blocks_count} associated blocks.",
        )

    await db.delete(district)
    await db.commit()

    return {"message": "District deleted successfully"}


@router.put("/blocks/{block_id}", response_model=BlockResponse)
async def update_block(
    block_id: int,
    block_request: CreateBlockRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update a block (Admin only)."""
    result = await db.execute(select(Block).where(Block.id == block_id))
    block = result.scalar_one_or_none()

    if not block:
        raise HTTPException(status_code=404, detail="Block not found")

    # Validate district exists
    district_result = await db.execute(
        select(District).where(District.id == block_request.district_id)
    )
    if not district_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="District not found")

    block.name = block_request.name
    block.description = block_request.description
    block.district_id = block_request.district_id

    await db.commit()
    await db.refresh(block)

    return BlockResponse(
        id=block.id,
        name=block.name,
        description=block.description,
        district_id=block.district_id,
    )


@router.delete("/blocks/{block_id}")
async def delete_block(
    block_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a block (Admin only)."""
    result = await db.execute(select(Block).where(Block.id == block_id))
    block = result.scalar_one_or_none()

    if not block:
        raise HTTPException(status_code=404, detail="Block not found")

    # Check if block has associated villages
    villages_result = await db.execute(
        select(func.count(GramPanchayat.id)).where(GramPanchayat.block_id == block_id)
    )
    villages_count = villages_result.scalar() or 0

    if villages_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete block. It has {villages_count} associated villages.",
        )

    await db.delete(block)
    await db.commit()

    return {"message": "Block deleted successfully"}


@router.put("/villages/{village_id}", response_model=GPResponse)
async def update_village(
    village_id: int,
    village_request: CreateGPRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update a village (Admin only)."""
    result = await db.execute(
        select(GramPanchayat).where(GramPanchayat.id == village_id)
    )
    village = result.scalar_one_or_none()

    if not village:
        raise HTTPException(status_code=404, detail="Village not found")

    # Validate district exists
    district_result = await db.execute(
        select(District).where(District.id == village_request.district_id)
    )
    if not district_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="District not found")

    # Validate block exists and belongs to the district
    block_result = await db.execute(
        select(Block).where(
            Block.id == village_request.block_id,
            Block.district_id == village_request.district_id,
        )
    )
    if not block_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Block not found or doesn't belong to the specified district",
        )

    village.name = village_request.name
    village.description = village_request.description
    village.block_id = village_request.block_id
    village.district_id = village_request.district_id

    await db.commit()
    await db.refresh(village)

    return GPResponse(
        id=village.id,
        name=village.name,
        description=village.description,
        block_id=village.block_id,
        district_id=village.district_id,
    )


@router.delete("/villages/{village_id}")
async def delete_village(
    village_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a village (Admin only)."""
    result = await db.execute(
        select(GramPanchayat).where(GramPanchayat.id == village_id)
    )
    village = result.scalar_one_or_none()

    if not village:
        raise HTTPException(status_code=404, detail="Village not found")

    # Check if village has associated complaints
    complaints_result = await db.execute(
        select(func.count(Complaint.id)).where(Complaint.village_id == village_id)
    )
    complaints_count = complaints_result.scalar() or 0

    if complaints_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete village. It has {complaints_count} associated complaints.",
        )

    await db.delete(village)
    await db.commit()

    return {"message": "Village deleted successfully"}


# Analytics and Dashboard endpoints
class DashboardStatsResponse(BaseModel):
    total_complaints: int
    open_complaints: int
    in_progress_complaints: int
    completed_complaints: int
    verified_complaints: int
    closed_complaints: int
    invalid_complaints: int
    total_users: int
    total_workers: int
    total_districts: int
    total_blocks: int
    total_villages: int
    complaints_by_district: List[dict[str, int | str]]
    complaints_by_status: List[dict[str, int | str]]
    recent_complaints: List[dict[str, str | int]]


@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)
):
    """Get comprehensive dashboard statistics (Admin only)."""

    # Complaint statistics
    total_complaints_result = await db.execute(select(func.count(Complaint.id)))
    total_complaints = total_complaints_result.scalar() or 0

    # Complaints by status
    status_counts = await db.execute(
        select(ComplaintStatus.name, func.count(Complaint.id))
        .join(Complaint, Complaint.status_id == ComplaintStatus.id)
        .group_by(ComplaintStatus.name)
    )
    status_dict = {name: count for name, count in status_counts}

    open_complaints = status_dict.get("OPEN", 0)
    in_progress_complaints = status_dict.get("IN_PROGRESS", 0)
    completed_complaints = status_dict.get("RESOLVED", 0)
    verified_complaints = status_dict.get("VERIFIED", 0)
    closed_complaints = status_dict.get("CLOSED", 0)
    invalid_complaints = status_dict.get("INVALID", 0)

    # User statistics
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0

    # Worker count (users with WORKER role)
    worker_count_result = await db.execute(
        select(func.count(User.id.distinct()))
        .select_from(User)
        .join(PositionHolder)
        .join(Role)
        .where(Role.name == UserRole.WORKER)
    )
    total_workers = worker_count_result.scalar() or 0

    # Geography statistics
    total_districts_result = await db.execute(select(func.count(District.id)))
    total_districts = total_districts_result.scalar() or 0

    total_blocks_result = await db.execute(select(func.count(Block.id)))
    total_blocks = total_blocks_result.scalar() or 0

    total_villages_result = await db.execute(select(func.count(GramPanchayat.id)))
    total_villages = total_villages_result.scalar() or 0

    # Complaints by district
    district_complaints = await db.execute(
        select(District.name, func.count(Complaint.id))
        .join(Complaint, Complaint.district_id == District.id)
        .group_by(District.name)
        .order_by(func.count(Complaint.id).desc())
    )
    complaints_by_district = [
        {"district": district, "count": count}
        for district, count in district_complaints
    ]

    # Complaints by status for chart
    complaints_by_status = [
        {"status": status, "count": count} for status, count in status_dict.items()
    ]

    # Recent complaints (last 10)
    recent_complaints_result = await db.execute(
        select(
            Complaint.id,
            Complaint.description,
            Complaint.created_at,
            ComplaintStatus.name.label("status_name"),
            District.name.label("district_name"),
            GramPanchayat.name.label("village_name"),
        )
        .join(ComplaintStatus, Complaint.status_id == ComplaintStatus.id)
        .join(District, Complaint.district_id == District.id)
        .join(GramPanchayat, Complaint.village_id == GramPanchayat.id)
        .order_by(Complaint.created_at.desc())
        .limit(10)
    )
    recent_complaints: List[Any] = [
        {
            "id": row.id,
            "description": row.description[:100] + "..."
            if len(row.description) > 100
            else row.description,
            "created_at": row.created_at.isoformat(),
            "status_name": row.status_name,
            "location": f"{row.village_name}, {row.district_name}",
        }
        for row in recent_complaints_result
    ]

    return DashboardStatsResponse(
        total_complaints=total_complaints,
        open_complaints=open_complaints,
        in_progress_complaints=in_progress_complaints,
        completed_complaints=completed_complaints,
        verified_complaints=verified_complaints,
        closed_complaints=closed_complaints,
        invalid_complaints=invalid_complaints,
        total_users=total_users,
        total_workers=total_workers,
        total_districts=total_districts,
        total_blocks=total_blocks,
        total_villages=total_villages,
        complaints_by_district=complaints_by_district,
        complaints_by_status=complaints_by_status,
        recent_complaints=recent_complaints,
    )


# Initialize default data
@router.post("/init-default-data")
async def initialize_default_data(
    db: AsyncSession = Depends(get_db),
):
    """Initialize default roles and admin user (Admin only)."""
    auth_service = AuthService(db)

    # If an admin does not exist, create one
    admin_username = "admin"
    existing_admin = await auth_service.get_user_by_username(admin_username)
    if not existing_admin:
        await auth_service.create_user(
            username=admin_username,
            email=f"{admin_username}@sbm-rajasthan.gov.in",
            password=f"{admin_username}123",  # In production, use a secure password and environment variable
        )

    await db.commit()  # to save roles and user

    # If the default user has not been assigned ADMIN role, assign it
    existing_admin = await auth_service.get_user_by_username(admin_username)

    admin_role = await auth_service.get_role_by_name(UserRole.ADMIN)
    assert existing_admin is not None, "Admin user should exist here"
    if not admin_role:
        admin_role = Role(
            name=UserRole.ADMIN, description="Administrator role with full permissions"
        )
        db.add(admin_role)
        await db.commit()

    admin_role = await auth_service.get_role_by_name(UserRole.ADMIN)
    assert admin_role is not None, "Admin role should exist here"
    position_holders_result = await db.execute(
        select(PositionHolder).where(
            PositionHolder.user_id == existing_admin.id,
            PositionHolder.role_id == admin_role.id,
        )
    )
    position_holder = position_holders_result.scalar_one_or_none()
    if not position_holder:
        position_holder = await auth_service.create_position_holder(
            user_id=existing_admin.id,
            role_id=admin_role.id,
            first_name="Admin",
            last_name="User",
        )
        db.add(position_holder)

    await db.commit()

    # Create default roles
    default_roles = [
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
        UserRole.CEO,
        UserRole.BDO,
        UserRole.VDO,
        UserRole.WORKER,
        UserRole.PUBLIC,
    ]

    default_complaint_types = [
        "Garbage",
        "Dead Animal",
        "Street Light",
        "Water Supply",
        "Road Repair",
        "Drainage",
        "Public Toilet",
    ]

    workflow_statuses = [
        "OPEN",
        "IN_PROGRESS",
        "COMPLETED",
        "VERIFIED",
        "CLOSED",
        "INVALID",
    ]

    for status_name in workflow_statuses:
        existing_status = await db.execute(
            select(ComplaintStatus).where(ComplaintStatus.name == status_name)
        )
        if not existing_status.scalar_one_or_none():
            status = ComplaintStatus(
                name=status_name, description=f"{status_name} status"
            )
            db.add(status)

    for complaint_type_name in default_complaint_types:
        existing_type = await db.execute(
            select(ComplaintType).where(ComplaintType.name == complaint_type_name)
        )
        if not existing_type.scalar_one_or_none():
            complaint_type = ComplaintType(
                name=complaint_type_name, description=f"{complaint_type_name} type"
            )
            db.add(complaint_type)

    for role_name in default_roles:
        existing_role = await auth_service.get_role_by_name(role_name)
        if not existing_role:
            role = Role(name=role_name, description=f"{role_name} role")
            db.add(role)

    await db.commit()
    # Assign ADMIN role to the default admin user if not already assigned
    if not existing_admin:
        admin_user = await auth_service.get_user_by_username(admin_username)
        if admin_user:
            admin_role = await auth_service.get_role_by_name(UserRole.ADMIN)
            if admin_role:
                position_holder = await auth_service.create_position_holder(
                    user_id=admin_user.id,
                    role_id=admin_role.id,
                    first_name="Admin",
                    last_name="User",
                )
                db.add(position_holder)

    superadmin_username = "superadmin"
    existing_superadmin = await auth_service.get_user_by_username(superadmin_username)
    if not existing_superadmin:
        await auth_service.create_user(
            username=superadmin_username,
            email=f"{superadmin_username}@sbm-rajasthan.gov.in",
            password=f"{superadmin_username}123",  # In production, use a secure password and environment variable
        )
        # Assign SUPERADMIN role to the superadmin user
        superadmin_user = await auth_service.get_user_by_username(superadmin_username)
        if superadmin_user:
            superadmin_role = await auth_service.get_role_by_name(UserRole.SUPERADMIN)
            if superadmin_role:
                position_holder = await auth_service.create_position_holder(
                    user_id=superadmin_user.id,
                    role_id=superadmin_role.id,
                    first_name="Super",
                    last_name="Admin",
                )
                db.add(position_holder)

    return {
        "message": "Default data initialized successfully",
        "user": admin_username,
    }
