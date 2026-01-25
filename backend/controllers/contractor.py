"""Contractor related API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from controllers.auth import get_current_active_user
from database import get_db

from services.contractor import ContractorService
from services.permission import PermissionService

from models.database.auth import User
from models.requests.contractor import CreateAgencyRequest, CreateContractorRequest, UpdateContractorRequest
from models.response.contractor import AgencyResponse, ContractorResponse

router = APIRouter()


@router.get("/agencies", response_model=List[AgencyResponse])
async def list_agencies(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    name_like: Optional[str] = None,
) -> List[AgencyResponse]:
    """List all agencies with pagination."""
    agencies = await ContractorService(db).list_agencies(
        skip=skip,
        limit=limit,
        name_like=name_like,
    )
    return [agency for agency in agencies]


@router.get("/contractors", response_model=List[ContractorResponse])
async def list_contractors(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    gp_id: Optional[int] = None,
    block_id: Optional[int] = None,
    district_id: Optional[int] = None,
    agency_id: Optional[int] = None,
    person_name: Optional[str] = None,
    active_only: bool = False,
) -> List[ContractorResponse]:
    """
    List all contractors with optional filtering and pagination.
    
    Filters:
    - gp_id: Filter by Gram Panchayat (Village) ID
    - block_id: Filter by Block ID
    - district_id: Filter by District ID
    - agency_id: Filter by Agency ID
    - person_name: Search by person name (case-insensitive partial match)
    - active_only: If true, only return contractors with active contracts
    """
    contractors = await ContractorService(db).list_contractors(
        skip=skip,
        limit=limit,
        gp_id=gp_id,
        block_id=block_id,
        district_id=district_id,
        agency_id=agency_id,
        person_name=person_name,
        active_only=active_only,
    )
    return contractors


@router.post("/agencies", response_model=AgencyResponse)
async def create_agency(
    agency: CreateAgencyRequest,
    db: AsyncSession = Depends(get_db),
) -> AgencyResponse:
    """Create a new agency."""
    try:
        agency_res = await ContractorService(db).create_agency(agency)
        print(agency_res)
        return agency_res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.post("/contractors", response_model=ContractorResponse, status_code=status.HTTP_201_CREATED)
async def create_contractor(
    contractor: CreateContractorRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ContractorResponse:
    """
    Create a new contractor (VDO only).
    
    VDOs can only create contractors within their assigned Gram Panchayat.
    """
    permission_service = PermissionService(db)
    
    # Check if user is VDO
    if not permission_service.is_vdo(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only VDOs can create contractors",
        )
    
    # VDO can only create contractors in their own GP
    if current_user.gp_id != contractor.gp_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="VDOs can only create contractors within their own Gram Panchayat",
        )
    
    try:
        contractor_res = await ContractorService(db).create_contractor(contractor)
        return contractor_res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from e


@router.put("/contractors/{contractor_id}", response_model=ContractorResponse)
async def update_contractor(
    contractor_id: int,
    contractor: UpdateContractorRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ContractorResponse:
    """
    Update contractor details (VDO only).
    
    VDOs can only update contractors within their assigned Gram Panchayat.
    """
    permission_service = PermissionService(db)
    contractor_service = ContractorService(db)
    
    # Check if user is VDO
    if not permission_service.is_vdo(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only VDOs can update contractors",
        )
    
    try:
        # Get existing contractor to verify GP
        existing_contractor = await contractor_service.get_contractor_by_id(contractor_id)
        
        # VDO can only update contractors in their own GP
        if current_user.gp_id != existing_contractor.gp_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="VDOs can only update contractors within their own Gram Panchayat",
            )
        
        # If gp_id is being changed, verify it's still the VDO's GP
        if contractor.gp_id is not None and contractor.gp_id != current_user.gp_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="VDOs can only assign contractors to their own Gram Panchayat",
            )
        
        contractor_res = await contractor_service.update_contractor(contractor_id, contractor)
        return contractor_res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from e
