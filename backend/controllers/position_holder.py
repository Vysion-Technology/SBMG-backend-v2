"""Position Holder controller with Role-Based Access Control."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth_utils import require_admin
from database import get_db
from models.database.auth import User
from models.requests.position_holder import (
    CreatePositionHolderRequest,
    UpdatePositionHolderRequest,
)
from models.response.auth import PositionHolderResponse
from services.position_holder import PositionHolderService
from services.auth import AuthService, UserRole
from controllers.auth import get_current_active_user


router = APIRouter()


def get_user_role(user: User) -> str:
    """Get the highest role of a user based on their positions."""
    role_hierarchy: dict[str, int] = {
        UserRole.SUPERADMIN: 6,
        UserRole.ADMIN: 5,
        UserRole.SMD: 4,
        UserRole.CEO: 3,
        UserRole.BDO: 2,
        UserRole.VDO: 1,
        UserRole.WORKER: 0,
    }
    
    # Check for special admin roles based on geography
    if not user.village_id and not user.block_id and not user.district_id:
        return UserRole.ADMIN
    
    # Get role from positions
    highest_role = UserRole.WORKER
    highest_priority = -1
    
    for position in user.positions:
        if position.role and position.role.name in role_hierarchy:
            priority = role_hierarchy.get(position.role.name, -1)
            if priority > highest_priority:
                highest_priority = priority
                highest_role = position.role.name
    
    return highest_role


def can_create_role(creator_role: str, target_role: str) -> bool:
    """Check if a user with creator_role can create a position with target_role.
    
    Rules:
    - SMD can create CEO/BDO/VDO
    - CEO can create BDO/VDO
    - BDO can create VDO
    - ADMIN and SUPERADMIN can create any role
    """
    permissions: dict[str, list[str]] = {
        UserRole.SUPERADMIN: [UserRole.SMD, UserRole.CEO, UserRole.BDO, UserRole.VDO, UserRole.WORKER],
        UserRole.ADMIN: [UserRole.SMD, UserRole.CEO, UserRole.BDO, UserRole.VDO, UserRole.WORKER],
        UserRole.SMD: [UserRole.CEO, UserRole.BDO, UserRole.VDO],
        UserRole.CEO: [UserRole.BDO, UserRole.VDO],
        UserRole.BDO: [UserRole.VDO],
    }
    
    allowed_roles = permissions.get(creator_role, [])
    return target_role in allowed_roles


def validate_geographical_assignment(role_name: str, district_id: Optional[int], 
                                     block_id: Optional[int], village_id: Optional[int]):
    """Validate that geographical assignment matches the role requirements."""
    if role_name == UserRole.CEO:
        if not district_id or block_id or village_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CEO must have district_id only (no block or village)"
            )
    elif role_name == UserRole.BDO:
        if not district_id or not block_id or village_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="BDO must have district_id and block_id (no village)"
            )
    elif role_name == UserRole.VDO:
        if not district_id or not block_id or not village_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="VDO must have district_id, block_id, and village_id"
            )


def validate_geographical_hierarchy(creator: User, district_id: Optional[int],
                                    block_id: Optional[int], village_id: Optional[int]):
    """Validate that the creator can assign to the specified geography.
    
    - CEO can only assign within their district
    - BDO can only assign within their block
    - VDO can only assign within their village (for lower roles)
    """
    creator_role = get_user_role(creator)
    
    # Admin and SMD can assign anywhere
    if creator_role in [UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.SMD]:
        return
    
    # CEO can only assign within their district
    if creator_role == UserRole.CEO:
        if creator.district_id != district_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CEO can only create positions within their own district"
            )
    
    # BDO can only assign within their block
    elif creator_role == UserRole.BDO:
        if creator.district_id != district_id or creator.block_id != block_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="BDO can only create positions within their own block"
            )
    
    # VDO validation (if needed for future worker assignments)
    elif creator_role == UserRole.VDO and village_id:
        if creator.village_id != village_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="VDO can only create positions within their own village"
            )


@router.post("/position-holders", response_model=PositionHolderResponse, status_code=status.HTTP_201_CREATED)
async def create_position_holder(
    request: CreatePositionHolderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new position holder with RBAC.
    
    - SMD can create CEO/BDO/VDO
    - CEO can create BDO/VDO
    - BDO can create VDO
    - ADMIN and SUPERADMIN can create any role
    """
    position_service = PositionHolderService(db)
    auth_svc = AuthService(db)
    
    # Get creator's role
    creator_role = get_user_role(current_user)
    
    # Check if creator can create this role
    if not can_create_role(creator_role, request.role_name):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{creator_role} cannot create {request.role_name} positions"
        )
    
    # Validate geographical assignment matches role
    validate_geographical_assignment(
        request.role_name,
        request.district_id,
        request.block_id,
        request.village_id
    )
    
    # Validate creator can assign to this geography
    validate_geographical_hierarchy(
        current_user,
        request.district_id,
        request.block_id,
        request.village_id
    )
    
    # Verify user exists
    user = await auth_svc.get_user_by_id(request.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {request.user_id} not found"
        )
    
    # Get role by name
    role = await position_service.get_role_by_name(request.role_name)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{request.role_name}' not found"
        )
    
    # Create position holder
    position = await position_service.create_position_holder(
        user_id=request.user_id,
        role_id=role.id,
        first_name=request.first_name,
        middle_name=request.middle_name,
        last_name=request.last_name,
        village_id=request.village_id,
        block_id=request.block_id,
        district_id=request.district_id,
        start_date=request.start_date,
        end_date=request.end_date,
        date_of_joining=request.date_of_joining,
    )
    
    # Refresh to load relationships
    position = await position_service.get_position_holder_by_id(position.id)
    
    if not position:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create position holder"
        )
    
    # Build response
    return PositionHolderResponse(
        id=position.id,
        user_id=position.user_id,
        username=position.user.username if position.user else "",
        email=position.user.email if position.user else None,
        first_name=position.first_name,
        middle_name=position.middle_name,
        last_name=position.last_name,
        role_id=position.role_id,
        role_name=position.role.name if position.role else None,
        district_id=position.district_id,
        district_name=position.district.name if position.district else None,
        block_id=position.block_id,
        block_name=position.block.name if position.block else None,
        village_id=position.village_id,
        village_name=position.village.name if position.village else None,
        date_of_joining=position.date_of_joining,
        start_date=position.start_date,
        end_date=position.end_date,
    )


@router.get("/position-holders/{position_id}", response_model=PositionHolderResponse)
async def get_position_holder(
    position_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),  # pylint: disable=unused-argument
):
    """Get a position holder by ID."""
    position_service = PositionHolderService(db)
    
    position = await position_service.get_position_holder_by_id(position_id)
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Position holder with id {position_id} not found"
        )
    
    # Build response
    return PositionHolderResponse(
        id=position.id,
        user_id=position.user_id,
        username=position.user.username if position.user else "",
        email=position.user.email if position.user else None,
        first_name=position.first_name,
        middle_name=position.middle_name,
        last_name=position.last_name,
        role_id=position.role_id,
        role_name=position.role.name if position.role else None,
        district_id=position.district_id,
        district_name=position.district.name if position.district else None,
        block_id=position.block_id,
        block_name=position.block.name if position.block else None,
        village_id=position.village_id,
        village_name=position.village.name if position.village else None,
        date_of_joining=position.date_of_joining,
        start_date=position.start_date,
        end_date=position.end_date,
    )


@router.get("/position-holders", response_model=List[PositionHolderResponse])
async def get_all_position_holders(
    role_name: Optional[str] = None,
    district_id: Optional[int] = None,
    block_id: Optional[int] = None,
    village_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all position holders with optional filtering.
    
    Users can only see position holders within their geographical jurisdiction:
    - CEO can see all in their district
    - BDO can see all in their block
    - VDO can see all in their village
    """
    position_service = PositionHolderService(db)
    creator_role = get_user_role(current_user)
    
    # Apply geographical filtering based on user role
    if creator_role not in [UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.SMD]:
        if creator_role == UserRole.CEO:
            # CEO can only see positions in their district
            if district_id and district_id != current_user.district_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CEO can only view positions within their district"
                )
            district_id = current_user.district_id
        elif creator_role == UserRole.BDO:
            # BDO can only see positions in their block
            if district_id and district_id != current_user.district_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="BDO can only view positions within their district"
                )
            if block_id and block_id != current_user.block_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="BDO can only view positions within their block"
                )
            district_id = current_user.district_id
            block_id = current_user.block_id
        elif creator_role == UserRole.VDO:
            # VDO can only see positions in their village
            if village_id and village_id != current_user.village_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="VDO can only view positions within their village"
                )
            district_id = current_user.district_id
            block_id = current_user.block_id
            village_id = current_user.village_id
    
    # Get role_id if role_name is provided
    role_id = None
    if role_name:
        role = await position_service.get_role_by_name(role_name)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{role_name}' not found"
            )
        role_id = role.id
    
    positions = await position_service.get_all_position_holders(
        role_id=role_id,
        district_id=district_id,
        block_id=block_id,
        village_id=village_id,
        skip=skip,
        limit=limit,
    )
    
    # Build response list
    return [
        PositionHolderResponse(
            id=position.id,
            user_id=position.user_id,
            username=position.user.username if position.user else "",
            email=position.user.email if position.user else None,
            first_name=position.first_name,
            middle_name=position.middle_name,
            last_name=position.last_name,
            role_id=position.role_id,
            role_name=position.role.name if position.role else None,
            district_id=position.district_id,
            district_name=position.district.name if position.district else None,
            block_id=position.block_id,
            block_name=position.block.name if position.block else None,
            village_id=position.village_id,
            village_name=position.village.name if position.village else None,
            date_of_joining=position.date_of_joining,
            start_date=position.start_date,
            end_date=position.end_date,
        )
        for position in positions
    ]


@router.put("/position-holders/{position_id}", response_model=PositionHolderResponse)
async def update_position_holder(
    position_id: int,
    request: UpdatePositionHolderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a position holder with RBAC.
    
    Users can only update position holders they have permission to create.
    """
    position_service = PositionHolderService(db)
    
    # Get existing position
    existing_position = await position_service.get_position_holder_by_id(position_id)
    if not existing_position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Position holder with id {position_id} not found"
        )
    
    creator_role = get_user_role(current_user)
    
    # Check if user can modify this position based on the current role
    current_role_name = existing_position.role.name if existing_position.role else None
    if current_role_name and not can_create_role(creator_role, current_role_name):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{creator_role} cannot modify {current_role_name} positions"
        )
    
    # If role is being changed, check permission for new role
    role_id = None
    if request.role_name:
        if not can_create_role(creator_role, request.role_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{creator_role} cannot assign {request.role_name} role"
            )
        
        role = await position_service.get_role_by_name(request.role_name)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{request.role_name}' not found"
            )
        role_id = role.id
        
        # Validate new geographical assignment
        new_district = request.district_id if request.district_id is not None else existing_position.district_id
        new_block = request.block_id if request.block_id is not None else existing_position.block_id
        new_village = request.village_id if request.village_id is not None else existing_position.village_id
        
        validate_geographical_assignment(request.role_name, new_district, new_block, new_village)
    
    # Update position holder
    updated_position = await position_service.update_position_holder(
        position_id=position_id,
        first_name=request.first_name,
        middle_name=request.middle_name,
        last_name=request.last_name,
        role_id=role_id,
        village_id=request.village_id,
        block_id=request.block_id,
        district_id=request.district_id,
        start_date=request.start_date,
        end_date=request.end_date,
        date_of_joining=request.date_of_joining,
    )
    
    if not updated_position:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update position holder"
        )
    
    # Build response
    return PositionHolderResponse(
        id=updated_position.id,
        user_id=updated_position.user_id,
        username=updated_position.user.username if updated_position.user else "",
        email=updated_position.user.email if updated_position.user else None,
        first_name=updated_position.first_name,
        middle_name=updated_position.middle_name,
        last_name=updated_position.last_name,
        role_id=updated_position.role_id,
        role_name=updated_position.role.name if updated_position.role else None,
        district_id=updated_position.district_id,
        district_name=updated_position.district.name if updated_position.district else None,
        block_id=updated_position.block_id,
        block_name=updated_position.block.name if updated_position.block else None,
        village_id=updated_position.village_id,
        village_name=updated_position.village.name if updated_position.village else None,
        date_of_joining=updated_position.date_of_joining,
        start_date=updated_position.start_date,
        end_date=updated_position.end_date,
    )


@router.delete("/position-holders/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_position_holder(
    position_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a position holder with RBAC.
    
    Users can only delete position holders they have permission to create.
    """
    position_service = PositionHolderService(db)
    
    # Get existing position
    existing_position = await position_service.get_position_holder_by_id(position_id)
    if not existing_position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Position holder with id {position_id} not found"
        )
    
    creator_role = get_user_role(current_user)
    
    # Check if user can delete this position
    current_role_name = existing_position.role.name if existing_position.role else None
    if current_role_name and not can_create_role(creator_role, current_role_name):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{creator_role} cannot delete {current_role_name} positions"
        )
    
    # Delete position holder
    deleted = await position_service.delete_position_holder(position_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete position holder"
        )
    
    return None
