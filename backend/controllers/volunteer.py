import json
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.database.auth import User, PublicUser
from controllers.auth import get_current_any_user, get_current_active_user
from auth_utils import require_staff_role
from models.requests.volunteer import VolunteerRegistrationRequest
from models.response.volunteer import VolunteerResponse
from services.volunteer import VolunteerService


router = APIRouter()


@router.post("/register", response_model=VolunteerResponse, status_code=status.HTTP_201_CREATED)
async def register_volunteer(
    registration_data: str = Form(...),
    photo: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: Union[User, PublicUser] = Depends(get_current_any_user),
):
    """
    Register a new volunteer.
    Accessible by Public Users (Citizens).
    """
    if not isinstance(current_user, PublicUser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can register as volunteers"
        )

    try:
        data_dict = json.loads(registration_data)
        request = VolunteerRegistrationRequest(**data_dict)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid registration data: {str(e)}"
        )

    service = VolunteerService(db)
    volunteer = await service.register_volunteer(current_user, request, photo)
    
    return volunteer


@router.get("/me", response_model=VolunteerResponse)
async def get_my_volunteer_status(
    db: AsyncSession = Depends(get_db),
    current_user: Union[User, PublicUser] = Depends(get_current_any_user),
):
    """Get the current citizen's volunteer registration status."""
    if not isinstance(current_user, PublicUser):
        raise HTTPException(status_code=403, detail="Only citizens have volunteer profiles")

    service = VolunteerService(db)
    volunteer = await service.get_volunteer_by_public_user_id(current_user.id)
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer registration not found")
    
    return volunteer


@router.get("/list", response_model=List[VolunteerResponse])
async def list_volunteers(
    district_id: Optional[int] = None,
    block_id: Optional[int] = None,
    gp_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """
    List volunteers for the 'Interest Module'.
    Filtered by jurisdiction of the logged-in authority member.
    """
    # Enforcement of jurisdiction
    if current_user.gp_id:
        gp_id = current_user.gp_id
        block_id = current_user.block_id
        district_id = current_user.district_id
    elif current_user.block_id:
        block_id = current_user.block_id
        district_id = current_user.district_id
    elif current_user.district_id:
        district_id = current_user.district_id

    service = VolunteerService(db)
    volunteers = await service.get_volunteers_list(
        district_id=district_id,
        block_id=block_id,
        gp_id=gp_id,
        skip=skip,
        limit=limit
    )
    return volunteers


@router.get("/{volunteer_id}", response_model=VolunteerResponse)
async def get_volunteer_detail(
    volunteer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_role),
):
    """Get full details of a volunteer registration."""
    service = VolunteerService(db)
    volunteer = await service.get_volunteer_by_id(volunteer_id)
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")

    # Check jurisdiction access
    if current_user.district_id and volunteer.district_id != current_user.district_id:
        raise HTTPException(status_code=403, detail="Access denied: Outside district jurisdiction")
    if current_user.block_id and volunteer.block_id != current_user.block_id:
        raise HTTPException(status_code=403, detail="Access denied: Outside block jurisdiction")
    if current_user.gp_id and volunteer.gp_id != current_user.gp_id:
        raise HTTPException(status_code=403, detail="Access denied: Outside GP jurisdiction")

    return volunteer
