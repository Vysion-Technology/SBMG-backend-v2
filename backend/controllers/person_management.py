"""
Person Management Controller
Handles person profiles, roles, designations, and position assignments.
"""

from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from database import get_db
from models.database.auth import User
from services.person_management_service import PersonManagementService
from services.login_user_service import LoginUserService
from auth_utils import require_admin, require_admin_or_ceo, get_current_active_user, PermissionChecker, UserRole

router = APIRouter()


# Pydantic models for Person Management
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


class CreatePersonWithPositionRequest(BaseModel):
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


class UpdatePersonRequest(BaseModel):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_joining: Optional[date] = None  # Admin only
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class TransferPositionRequest(BaseModel):
    new_user_id: int
    transfer_date: date
    new_first_name: str
    new_last_name: str
    new_middle_name: Optional[str] = None


class PersonResponse(BaseModel):
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


class PersonWithLoginResponse(BaseModel):
    person: PersonResponse
    login_user: dict


# Role Management APIs
@router.post("/roles", response_model=RoleResponse)
async def create_role(
    request: CreateRoleRequest, current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    """Create a new role (Admin only)."""
    try:
        person_service = PersonManagementService(db)
        role = await person_service.create_role(request.name, request.description)
        return RoleResponse(id=role.id, name=role.name, description=role.description)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/roles", response_model=List[RoleResponse])
async def get_all_roles(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    """Get all roles."""
    person_service = PersonManagementService(db)
    roles = await person_service.get_all_roles()
    return [RoleResponse(id=role.id, name=role.name, description=role.description) for role in roles]


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role_by_id(
    role_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
):
    """Get role by ID."""
    person_service = PersonManagementService(db)
    role = await person_service.get_role_by_id(role_id)

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
    """Update an existing role (Admin only)."""
    try:
        person_service = PersonManagementService(db)
        role = await person_service.update_role(role_id, request.name, request.description)

        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

        return RoleResponse(id=role.id, name=role.name, description=role.description)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Person Management APIs
@router.post("/persons", response_model=PersonWithLoginResponse)
async def create_person_with_position(
    request: CreatePersonWithPositionRequest,
    current_user: User = Depends(require_admin_or_ceo),
    db: AsyncSession = Depends(get_db),
):
    """Create a new person with position and login account."""
    try:
        person_service = PersonManagementService(db)
        login_service = LoginUserService(db)

        # Check permissions for date_of_joining field (admin only)
        permission_checker = PermissionChecker(db)
        current_roles = await permission_checker.get_user_roles(current_user.id)

        if request.date_of_joining and UserRole.ADMIN not in current_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can set date_of_joining")

        # Get role
        role = await person_service.get_role_by_name(request.role_name)
        if not role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Role '{request.role_name}' not found")

        # Generate username
        username = await person_service.generate_username(
            role_name=request.role_name,
            district_id=request.district_id,
            block_id=request.block_id,
            village_id=request.village_id,
            contractor_name=request.contractor_name,
        )

        # Create login user
        password = request.password or "defaultpassword"  # Should be randomized in production
        login_user = await login_service.create_login_user(username=username, email=None, password=password)

        # Create position holder
        position = await person_service.create_position_holder(
            user_id=login_user.id,
            role_id=role.id,
            first_name=request.first_name,
            last_name=request.last_name,
            middle_name=request.middle_name,
            date_of_joining=request.date_of_joining,
            start_date=request.start_date,
            end_date=request.end_date,
            district_id=request.district_id,
            block_id=request.block_id,
            village_id=request.village_id,
        )

        # Prepare response
        person_response = PersonResponse(
            id=position.id,
            user_id=position.user_id,
            role_id=position.role_id,
            role_name=role.name,
            first_name=position.first_name,
            middle_name=position.middle_name,
            last_name=position.last_name,
            username=username,
            date_of_joining=position.date_of_joining,
            start_date=position.start_date,
            end_date=position.end_date,
            email=login_user.email,
            district_id=position.district_id,
            district_name=position.district.name if position.district else None,
            block_id=position.block_id,
            block_name=position.block.name if position.block else None,
            village_id=position.village_id,
            village_name=position.village.name if position.village else None,
        )

        login_response = {
            "id": login_user.id,
            "username": login_user.username,
            "email": login_user.email,
            "is_active": login_user.is_active,
        }

        return PersonWithLoginResponse(person=person_response, login_user=login_response)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/persons", response_model=List[PersonResponse])
async def get_all_persons(
    role_id: Optional[int] = None,
    district_id: Optional[int] = None,
    block_id: Optional[int] = None,
    village_id: Optional[int] = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all persons with optional filters."""
    person_service = PersonManagementService(db)
    positions = await person_service.get_all_position_holders(
        role_id=role_id,
        district_id=district_id,
        block_id=block_id,
        village_id=village_id,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )

    return [
        PersonResponse(
            id=pos.id,
            user_id=pos.user_id,
            role_id=pos.role_id,
            role_name=pos.role.name,
            first_name=pos.first_name,
            middle_name=pos.middle_name,
            last_name=pos.last_name,
            username=pos.user.username,
            date_of_joining=pos.date_of_joining,
            start_date=pos.start_date,
            end_date=pos.end_date,
            email=pos.user.email,
            district_id=pos.district_id,
            district_name=pos.district.name if pos.district else None,
            block_id=pos.block_id,
            block_name=pos.block.name if pos.block else None,
            village_id=pos.village_id,
            village_name=pos.village.name if pos.village else None,
        )
        for pos in positions
    ]


@router.get("/persons/{person_id}", response_model=PersonResponse)
async def get_person_by_id(
    person_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
):
    """Get person by ID."""
    person_service = PersonManagementService(db)
    position = await person_service.get_position_holder_by_id(person_id)

    if not position:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    return PersonResponse(
        id=position.id,
        user_id=position.user_id,
        role_id=position.role_id,
        role_name=position.role.name,
        first_name=position.first_name,
        middle_name=position.middle_name,
        last_name=position.last_name,
        username=position.user.username,
        date_of_joining=position.date_of_joining,
        start_date=position.start_date,
        end_date=position.end_date,
        email=position.user.email,
        district_id=position.district_id,
        district_name=position.district.name if position.district else None,
        block_id=position.block_id,
        block_name=position.block.name if position.block else None,
        village_id=position.village_id,
        village_name=position.village.name if position.village else None,
    )


@router.put("/persons/{person_id}", response_model=PersonResponse)
async def update_person(
    person_id: int,
    request: UpdatePersonRequest,
    current_user: User = Depends(require_admin_or_ceo),
    db: AsyncSession = Depends(get_db),
):
    """Update person information."""
    try:
        person_service = PersonManagementService(db)

        # Check permissions for date_of_joining field (admin only)
        if request.date_of_joining:
            permission_checker = PermissionChecker(db)
            current_roles = await permission_checker.get_user_roles(current_user.id)

            if UserRole.ADMIN not in current_roles:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can set date_of_joining")

        position = await person_service.update_position_holder(
            position_id=person_id,
            first_name=request.first_name,
            middle_name=request.middle_name,
            last_name=request.last_name,
            date_of_joining=request.date_of_joining,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        if not position:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

        return PersonResponse(
            id=position.id,
            user_id=position.user_id,
            role_id=position.role_id,
            role_name=position.role.name,
            first_name=position.first_name,
            middle_name=position.middle_name,
            last_name=position.last_name,
            username=position.user.username,
            date_of_joining=position.date_of_joining,
            start_date=position.start_date,
            end_date=position.end_date,
            email=position.user.email,
            district_id=position.district_id,
            district_name=position.district.name if position.district else None,
            block_id=position.block_id,
            block_name=position.block.name if position.block else None,
            village_id=position.village_id,
            village_name=position.village.name if position.village else None,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Position Transfer and History
@router.post("/persons/{person_id}/transfer", response_model=PersonResponse)
async def transfer_position(
    person_id: int,
    request: TransferPositionRequest,
    current_user: User = Depends(require_admin_or_ceo),
    db: AsyncSession = Depends(get_db),
):
    """Transfer a position from one person to another."""
    try:
        person_service = PersonManagementService(db)
        new_position = await person_service.transfer_position(
            current_position_id=person_id,
            new_user_id=request.new_user_id,
            transfer_date=request.transfer_date,
            new_first_name=request.new_first_name,
            new_last_name=request.new_last_name,
            new_middle_name=request.new_middle_name,
        )

        return PersonResponse(
            id=new_position.id,
            user_id=new_position.user_id,
            role_id=new_position.role_id,
            role_name=new_position.role.name,
            first_name=new_position.first_name,
            middle_name=new_position.middle_name,
            last_name=new_position.last_name,
            username=new_position.user.username,
            date_of_joining=new_position.date_of_joining,
            start_date=new_position.start_date,
            end_date=new_position.end_date,
            email=new_position.user.email,
            district_id=new_position.district_id,
            district_name=new_position.district.name if new_position.district else None,
            block_id=new_position.block_id,
            block_name=new_position.block.name if new_position.block else None,
            village_id=new_position.village_id,
            village_name=new_position.village.name if new_position.village else None,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/positions/history", response_model=List[PersonResponse])
async def get_position_history(
    role_id: Optional[int] = None,
    district_id: Optional[int] = None,
    block_id: Optional[int] = None,
    village_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get historical data of position assignments."""
    person_service = PersonManagementService(db)
    history = await person_service.get_position_history(
        role_id=role_id,
        district_id=district_id,
        block_id=block_id,
        village_id=village_id,
        from_date=from_date,
        to_date=to_date,
    )

    return [
        PersonResponse(
            id=pos.id,
            user_id=pos.user_id,
            role_id=pos.role_id,
            role_name=pos.role.name,
            first_name=pos.first_name,
            middle_name=pos.middle_name,
            last_name=pos.last_name,
            username=pos.user.username,
            date_of_joining=pos.date_of_joining,
            start_date=pos.start_date,
            end_date=pos.end_date,
            email=pos.user.email,
            district_id=pos.district_id,
            district_name=pos.district.name if pos.district else None,
            block_id=pos.block_id,
            block_name=pos.block.name if pos.block else None,
            village_id=pos.village_id,
            village_name=pos.village.name if pos.village else None,
        )
        for pos in history
    ]


@router.get("/users/{user_id}/positions", response_model=List[PersonResponse])
async def get_user_position_history(
    user_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
):
    """Get all positions held by a specific user (historical and current)."""
    person_service = PersonManagementService(db)
    positions = await person_service.get_position_holders_by_user(user_id)

    return [
        PersonResponse(
            id=pos.id,
            user_id=pos.user_id,
            role_id=pos.role_id,
            role_name=pos.role.name,
            first_name=pos.first_name,
            middle_name=pos.middle_name,
            last_name=pos.last_name,
            username=pos.user.username,
            date_of_joining=pos.date_of_joining,
            start_date=pos.start_date,
            end_date=pos.end_date,
            email=pos.user.email,
            district_id=pos.district_id,
            district_name=pos.district.name if pos.district else None,
            block_id=pos.block_id,
            block_name=pos.block.name if pos.block else None,
            village_id=pos.village_id,
            village_name=pos.village.name if pos.village else None,
        )
        for pos in positions
    ]


# Search functionality
@router.get("/persons/search", response_model=List[PersonResponse])
async def search_persons_by_name(
    name: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Search persons by name."""
    person_service = PersonManagementService(db)
    persons = await person_service.search_persons_by_name(name, skip, limit)

    return [
        PersonResponse(
            id=pos.id,
            user_id=pos.user_id,
            role_id=pos.role_id,
            role_name=pos.role.name,
            first_name=pos.first_name,
            middle_name=pos.middle_name,
            last_name=pos.last_name,
            username=pos.user.username,
            date_of_joining=pos.date_of_joining,
            start_date=pos.start_date,
            end_date=pos.end_date,
            email=pos.user.email,
            district_id=pos.district_id,
            district_name=pos.district.name if pos.district else None,
            block_id=pos.block_id,
            block_name=pos.block.name if pos.block else None,
            village_id=pos.village_id,
            village_name=pos.village.name if pos.village else None,
        )
        for pos in persons
    ]
