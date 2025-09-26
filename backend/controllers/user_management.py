from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from database import get_db
from models.database.auth import User, PositionHolder
from services.user_management import UserManagementService
from auth_utils import require_admin, require_admin_or_ceo, get_current_active_user, PermissionChecker, UserRole

router = APIRouter()


# Pydantic models for requests/responses
class CreateRoleRequest(BaseModel):
    name: str
    description: Optional[str] = None


class UpdateRoleRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]


class CreateUserWithPositionRequest(BaseModel):
    role_name: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    date_of_joining: Optional[date] = None  # Admin only
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    district_id: Optional[int] = None
    block_id: Optional[int] = None
    village_id: Optional[int] = None
    contractor_name: Optional[str] = None  # For Worker role only
    password: Optional[str] = None


class UpdatePositionHolderRequest(BaseModel):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_joining: Optional[date] = None  # Admin only
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ChangePasswordRequest(BaseModel):
    new_password: str


class PositionHolderResponse(BaseModel):
    id: int
    user_id: int
    role_id: int
    role_name: str
    first_name: str
    middle_name: Optional[str]
    last_name: str
    username: str
    date_of_joining: Optional[date]
    start_date: Optional[date]
    end_date: Optional[date]
    email: Optional[str]
    district_id: Optional[int]
    district_name: Optional[str]
    block_id: Optional[int]
    block_name: Optional[str]
    village_id: Optional[int]
    village_name: Optional[str]


class UserWithPositionResponse(BaseModel):
    user: dict
    position: PositionHolderResponse


# Role Management APIs
@router.post("/roles", response_model=RoleResponse)
async def create_role(
    request: CreateRoleRequest, current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    """Create a new role (Admin only)."""
    try:
        user_mgmt_service = UserManagementService(db)
        role = await user_mgmt_service.create_role(request.name, request.description)
        return RoleResponse(id=role.id, name=role.name, description=role.description)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/roles", response_model=List[RoleResponse])
async def get_all_roles(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    """Get all roles."""
    user_mgmt_service = UserManagementService(db)
    roles = await user_mgmt_service.get_all_roles()
    return [RoleResponse(id=role.id, name=role.name, description=role.description) for role in roles]


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
):
    """Get role by ID."""
    user_mgmt_service = UserManagementService(db)
    role = await user_mgmt_service.get_role_by_id(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return RoleResponse(id=role.id, name=role.name, description=role.description)


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    request: UpdateRoleRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update role (Admin only)."""
    try:
        user_mgmt_service = UserManagementService(db)
        role = await user_mgmt_service.update_role(role_id, request.name, request.description)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        return RoleResponse(id=role.id, name=role.name, description=role.description)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# User and Position Holder Management APIs
@router.post("/users", response_model=UserWithPositionResponse)
async def create_user_with_position(
    request: CreateUserWithPositionRequest,
    current_user: User = Depends(require_admin_or_ceo),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user with position (Admin or CEO only)."""
    try:
        user_mgmt_service = UserManagementService(db)

        # Additional permission check: CEOs can only create users in their district
        if not PermissionChecker.user_has_role(current_user, [UserRole.ADMIN]):
            if request.district_id:
                if not PermissionChecker.user_can_access_district(current_user, request.district_id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create user in this district"
                    )

        user, position = await user_mgmt_service.create_user_with_position(
            role_name=request.role_name,
            first_name=request.first_name,
            last_name=request.last_name,
            middle_name=request.middle_name,
            date_of_joining=request.date_of_joining,
            district_id=request.district_id,
            block_id=request.block_id,
            village_id=request.village_id,
            contractor_name=request.contractor_name,
            password=request.password,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        # Reload position with relationships
        position = await user_mgmt_service.get_position_holder_by_id(position.id)

        position_response = PositionHolderResponse(
            id=position.id,
            user_id=position.user_id,
            role_id=position.role_id,
            role_name=position.role.name if position.role else "",
            first_name=position.first_name,
            middle_name=position.middle_name,
            last_name=position.last_name,
            date_of_joining=position.date_of_joining,
            start_date=position.start_date,
            end_date=position.end_date,
            username=user.username,
            email=user.email,
            district_id=position.district_id,
            district_name=position.district.name if position.district else None,
            block_id=position.block_id,
            block_name=position.block.name if position.block else None,
            village_id=position.village_id,
            village_name=position.village.name if position.village else None,
        )

        return UserWithPositionResponse(
            user={"id": user.id, "username": user.username, "email": user.email, "is_active": user.is_active},
            position=position_response,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/position-holders", response_model=List[PositionHolderResponse])
async def get_all_position_holders(
    skip: int = 0,
    limit: int = 100,
    role_name: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all position holders with optional role filtering."""
    user_mgmt_service = UserManagementService(db)

    if role_name:
        positions = await user_mgmt_service.get_position_holders_by_role(role_name, skip, limit)
    else:
        positions = await user_mgmt_service.get_all_position_holders(skip, limit)

    # Filter based on user permissions
    filtered_positions: List[PositionHolder] = []
    for position in positions:
        can_access = False

        if PermissionChecker.user_has_role(current_user, [UserRole.ADMIN]):
            can_access = True
        elif position.district_id and PermissionChecker.user_can_access_district(current_user, position.district_id):
            can_access = True
        elif position.block_id and PermissionChecker.user_can_access_block(current_user, position.block_id):
            can_access = True
        elif position.village_id and PermissionChecker.user_can_access_village(current_user, position.village_id):
            can_access = True

        if can_access:
            filtered_positions.append(position)

    return [
        PositionHolderResponse(
            id=position.id,
            user_id=position.user_id,
            role_id=position.role_id,
            role_name=position.role.name if position.role else "",
            first_name=position.first_name,
            middle_name=position.middle_name,
            last_name=position.last_name,
            date_of_joining=position.date_of_joining,
            start_date=position.start_date,
            end_date=position.end_date,
            username=position.user.username if position.user else "",
            email=position.user.email if position.user else None,
            district_id=position.district_id,
            district_name=position.district.name if position.district else None,
            block_id=position.block_id,
            block_name=position.block.name if position.block else None,
            village_id=position.village_id,
            village_name=position.village.name if position.village else None,
        )
        for position in filtered_positions
    ]


@router.get("/position-holders/{position_id}", response_model=PositionHolderResponse)
async def get_position_holder(
    position_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
):
    """Get position holder by ID."""
    user_mgmt_service = UserManagementService(db)
    position = await user_mgmt_service.get_position_holder_by_id(position_id)

    if not position:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position holder not found")

    # Check permissions
    can_access = False
    if PermissionChecker.user_has_role(current_user, [UserRole.ADMIN]):
        can_access = True
    elif position.district_id and PermissionChecker.user_can_access_district(current_user, position.district_id):
        can_access = True
    elif position.block_id and PermissionChecker.user_can_access_block(current_user, position.block_id):
        can_access = True
    elif position.village_id and PermissionChecker.user_can_access_village(current_user, position.village_id):
        can_access = True

    if not can_access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return PositionHolderResponse(
        id=position.id,
        user_id=position.user_id,
        role_id=position.role_id,
        role_name=position.role.name if position.role else "",
        first_name=position.first_name,
        middle_name=position.middle_name,
        last_name=position.last_name,
        date_of_joining=position.date_of_joining,
        start_date=position.start_date,
        end_date=position.end_date,
        username=position.user.username if position.user else "",
        email=position.user.email if position.user else None,
        district_id=position.district_id,
        district_name=position.district.name if position.district else None,
        block_id=position.block_id,
        block_name=position.block.name if position.block else None,
        village_id=position.village_id,
        village_name=position.village.name if position.village else None,
    )


@router.put("/position-holders/{position_id}", response_model=PositionHolderResponse)
async def update_position_holder(
    position_id: int,
    request: UpdatePositionHolderRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update position holder. Only admins can update critical fields (name, DOJ)."""
    user_mgmt_service = UserManagementService(db)

    # Check if position exists and user has access
    position = await user_mgmt_service.get_position_holder_by_id(position_id)
    if not position:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position holder not found")

    # Check permissions
    can_access = False
    if PermissionChecker.user_has_role(current_user, [UserRole.ADMIN]):
        can_access = True
    elif position.district_id and PermissionChecker.user_can_access_district(current_user, position.district_id):
        can_access = True
    elif position.block_id and PermissionChecker.user_can_access_block(current_user, position.block_id):
        can_access = True
    elif position.village_id and PermissionChecker.user_can_access_village(current_user, position.village_id):
        can_access = True

    if not can_access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Determine if this is an admin update
    is_admin_update = PermissionChecker.user_has_role(current_user, [UserRole.ADMIN])

    # Update the position holder
    updated_position = await user_mgmt_service.update_position_holder(
        position_id=position_id,
        first_name=request.first_name,
        middle_name=request.middle_name,
        last_name=request.last_name,
        date_of_joining=request.date_of_joining,
        start_date=request.start_date,
        end_date=request.end_date,
        is_admin_update=is_admin_update,
    )

    if not updated_position:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position holder not found")

    return PositionHolderResponse(
        id=updated_position.id,
        user_id=updated_position.user_id,
        role_id=updated_position.role_id,
        role_name=updated_position.role.name if updated_position.role else "",
        first_name=updated_position.first_name,
        middle_name=updated_position.middle_name,
        last_name=updated_position.last_name,
        date_of_joining=updated_position.date_of_joining,
        start_date=updated_position.start_date,
        end_date=updated_position.end_date,
        username=updated_position.user.username if updated_position.user else "",
        email=updated_position.user.email if updated_position.user else None,
        district_id=updated_position.district_id,
        district_name=updated_position.district.name if updated_position.district else None,
        block_id=updated_position.block_id,
        block_name=updated_position.block.name if updated_position.block else None,
        village_id=updated_position.village_id,
        village_name=updated_position.village.name if updated_position.village else None,
    )


@router.put("/users/{user_id}/password", status_code=200)
async def change_user_password(
    user_id: int,
    request: ChangePasswordRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Change user password (Admin only)."""
    try:
        user_mgmt_service = UserManagementService(db)
        success = await user_mgmt_service.change_user_password(user_id, request.new_password)
        
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
