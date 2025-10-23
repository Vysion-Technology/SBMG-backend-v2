"""Contractor Service Module."""
from typing import Optional
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.requests.contractor import CreateAgencyRequest
from models.database.contractor import Agency
from models.response.contractor import AgencyResponse


def map_agency_to_response(agency: Agency) -> AgencyResponse:
    """Map Agency database model to AgencyResponse model."""
    return AgencyResponse(
        id=agency.id,
        name=agency.name,
        phone=agency.phone,
        email=agency.email,
        address=agency.address,
    )


class ContractorService:
    """Service class for managing contractors."""
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_agency_by_id(self, agency_id: int) -> Agency:
        """Get agency by its ID."""
        result = await self.db.execute(select(Agency).where(Agency.id == agency_id))
        return result.scalar_one()

    async def list_agencies(
        self,
        skip: int = 0,
        limit: int = 100,
        name_like: Optional[str] = None,
    ) -> list[AgencyResponse]:
        """List agencies with optional name filtering and pagination."""
        query = select(Agency).offset(skip).limit(limit)
        if name_like:
            query = query.where(Agency.name.ilike(f"%{name_like}%"))
        result = await self.db.execute(query)
        agencies = result.scalars().all()
        return [map_agency_to_response(agency) for agency in agencies]

    async def create_agency(
        self,
        agency_req: CreateAgencyRequest,
    ) -> AgencyResponse:
        """Create a new agency."""
        existing = await self.db.execute(
            select(Agency).where(Agency.name == agency_req.name)
        )
        agency = existing.all()
        print("Existing Agency: ", agency)
        if agency:
            raise ValueError(f"Agency with name '{agency_req.name}' already exists.")

        result = await self.db.execute(
            insert(Agency)
            .values(
                name=agency_req.name,
                phone=agency_req.phone,
                email=agency_req.email,
                address=agency_req.address,
            )
            .returning(Agency)
        )
        new_agency = result.scalar_one()
        await self.db.refresh(new_agency)
        return map_agency_to_response(new_agency)
