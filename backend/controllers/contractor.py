from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from services.contractor import ContractorService
from models.response.contractor import AgencyResponse
from models.requests.contractor import CreateAgencyRequest

router = APIRouter()


@router.get("/", response_model=List[AgencyResponse])
async def list_agencies(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    name_like: Optional[str] = None,
) -> List[AgencyResponse]:
    """List all agencies with pagination."""
    agencies = await ContractorService(db).list_agencies(
        skip=skip, limit=limit, name_like=name_like
    )
    return [agency for agency in agencies]


@router.post("/", response_model=AgencyResponse)
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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")
