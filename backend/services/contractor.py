"""Contractor Service Module."""

from typing import Optional
from sqlalchemy import func, insert, select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.database.contractor import Agency, Contractor
from models.database.geography import GramPanchayat, Block, District
from models.requests.contractor import CreateAgencyRequest, CreateContractorRequest, UpdateContractorRequest
from models.response.contractor import AgencyResponse, ContractorResponse


def map_agency_to_response(agency: Agency) -> AgencyResponse:
    """Map Agency database model to AgencyResponse model."""
    return AgencyResponse(
        id=agency.id,
        name=agency.name,
        phone=agency.phone,
        email=agency.email,
        address=agency.address,
    )


def map_contractor_to_response(contractor: Contractor) -> ContractorResponse:
    """Map Contractor database model to ContractorResponse model."""
    return ContractorResponse(
        id=contractor.id,
        agency=map_agency_to_response(contractor.agency) if contractor.agency else None,
        person_name=contractor.person_name,
        person_phone=contractor.person_phone,
        village_id=contractor.gp_id,
        village_name=contractor.gp.name if contractor.gp else None,
        block_name=contractor.gp.block.name if contractor.gp and contractor.gp.block else None,
        district_name=contractor.gp.block.district.name
        if contractor.gp and contractor.gp.block and contractor.gp.block.district
        else None,
        contract_start_date=contractor.contract_start_date,
        contract_end_date=contractor.contract_end_date,
    )


class ContractorService:
    """Service class for managing contractors."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_agency_by_id(self, agency_id: int) -> Agency:
        """Get agency by its ID."""
        result = await self.db.execute(select(Agency).where(Agency.id == agency_id))
        return result.scalar_one()

    async def get_contractor_by_id(self, contractor_id: int) -> Contractor:
        """Get contractor by its ID with all relationships loaded."""

        result = await self.db.execute(
            select(Contractor)
            .options(
                selectinload(Contractor.agency),
                selectinload(Contractor.gp).selectinload(GramPanchayat.block).selectinload(Block.district),
            )
            .where(Contractor.id == contractor_id)
        )
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

    async def list_contractors(
        self,
        skip: int = 0,
        limit: int = 100,
        gp_id: Optional[int] = None,
        block_id: Optional[int] = None,
        district_id: Optional[int] = None,
        agency_id: Optional[int] = None,
        person_name: Optional[str] = None,
        active_only: bool = False,
    ) -> list[ContractorResponse]:
        """List contractors with optional filtering and pagination."""
        # Build query with relationships loaded
        query = select(Contractor).options(
            selectinload(Contractor.agency),
            selectinload(Contractor.gp).selectinload(GramPanchayat.block).selectinload(Block.district),
        )

        # Build filter conditions
        filters = []
        if gp_id is not None:
            filters.append(Contractor.gp_id == gp_id)
        if agency_id is not None:
            filters.append(Contractor.agency_id == agency_id)
        if person_name is not None:
            filters.append(Contractor.person_name.ilike(f"%{person_name}%"))
        if active_only:
            # A contract is active if it has started and not yet ended
            filters.append(
                and_(
                    Contractor.contract_start_date <= func.current_date(),
                    Contractor.contract_end_date >= func.current_date()
                )
            )

        # Track if we've already joined GramPanchayat and Block tables
        gp_joined = False
        block_joined = False

        # Apply block_id filter by joining with GramPanchayat
        if block_id is not None:
            query = query.join(Contractor.gp)
            gp_joined = True
            filters.append(GramPanchayat.block_id == block_id)

        # Apply district_id filter by joining with GramPanchayat and Block
        if district_id is not None:
            if not gp_joined:
                query = query.join(Contractor.gp)
                gp_joined = True
            query = query.join(GramPanchayat.block)
            block_joined = True
            filters.append(Block.district_id == district_id)

        # Apply all filters
        if filters:
            query = query.where(and_(*filters))

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        contractors = result.scalars().unique().all()

        return [map_contractor_to_response(contractor) for contractor in contractors]

    async def create_agency(
        self,
        agency_req: CreateAgencyRequest,
    ) -> AgencyResponse:
        """Create a new agency."""
        existing = await self.db.execute(select(Agency).where(Agency.name == agency_req.name))
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
        await self.db.commit()
        await self.db.refresh(new_agency)
        return map_agency_to_response(new_agency)

    async def create_contractor(
        self,
        contractor_req: CreateContractorRequest,
    ) -> ContractorResponse:
        """Create a new contractor."""
        # Verify agency exists
        agency_result = await self.db.execute(select(Agency).where(Agency.id == contractor_req.agency_id))
        agency = agency_result.scalar_one_or_none()
        if not agency:
            raise ValueError(f"Agency with id '{contractor_req.agency_id}' not found.")

        # Create contractor
        result = await self.db.execute(
            insert(Contractor)
            .values(
                agency_id=contractor_req.agency_id,
                person_name=contractor_req.person_name,
                person_phone=contractor_req.person_phone,
                gp_id=contractor_req.gp_id,
                contract_start_date=contractor_req.contract_start_date,
                contract_end_date=contractor_req.contract_end_date,
            )
            .returning(Contractor)
        )
        await self.db.commit()
        new_contractor = result.scalar_one()
        print("New Contractor: ", new_contractor)
        await self.db.refresh(new_contractor)

        # Fetch with relationships for response
        contractor_with_relations = await self.get_contractor_by_id(new_contractor.id)
        return map_contractor_to_response(contractor_with_relations)

    async def update_contractor(
        self,
        contractor_id: int,
        contractor_req: UpdateContractorRequest,
    ) -> ContractorResponse:
        """Update an existing contractor."""
        # Check if contractor exists
        contractor_result = await self.db.execute(select(Contractor).where(Contractor.id == contractor_id))
        contractor = contractor_result.scalar_one_or_none()
        if not contractor:
            raise ValueError(f"Contractor with id '{contractor_id}' not found.")

        # If agency_id is being updated, verify it exists
        if contractor_req.agency_id is not None:
            agency_result = await self.db.execute(select(Agency).where(Agency.id == contractor_req.agency_id))
            agency = agency_result.scalar_one_or_none()
            if not agency:
                raise ValueError(f"Agency with id '{contractor_req.agency_id}' not found.")

        # Build update values (only include fields that are provided)
        update_values = {}
        if contractor_req.agency_id is not None:
            update_values["agency_id"] = contractor_req.agency_id
        if contractor_req.person_name is not None:
            update_values["person_name"] = contractor_req.person_name
        if contractor_req.person_phone is not None:
            update_values["person_phone"] = contractor_req.person_phone
        if contractor_req.gp_id is not None:
            update_values["gp_id"] = contractor_req.gp_id
        if contractor_req.contract_start_date is not None:
            update_values["contract_start_date"] = contractor_req.contract_start_date
        if contractor_req.contract_end_date is not None:
            update_values["contract_end_date"] = contractor_req.contract_end_date

        # Update contractor
        if update_values:
            await self.db.execute(update(Contractor).where(Contractor.id == contractor_id).values(**update_values))
            await self.db.commit()

        # Fetch updated contractor with relationships
        updated_contractor = await self.get_contractor_by_id(contractor_id)
        return map_contractor_to_response(updated_contractor)

    async def get_active_contractor(
        self,
        gp_id: int,
    ) -> Optional[Contractor]:
        """Get active contractor for a given Gram Panchayat."""
        result = await self.db.execute(
            select(Contractor).where(
                Contractor.gp_id == gp_id,
                Contractor.contract_end_date >= func.current_date(),
            )
        )
        return result.scalars().one_or_none()

    async def create_contractors_bulk(
        self,
        contractors_req: list[CreateContractorRequest],
    ) -> list[ContractorResponse]:
        """Create multiple contractors in bulk."""
        contractors = await self.db.execute(
            insert(Contractor)
            .values([
                {
                    "agency_id": req.agency_id,
                    "person_name": req.person_name,
                    "person_phone": req.person_phone,
                    "gp_id": req.gp_id,
                    "contract_start_date": req.contract_start_date,
                    "contract_end_date": req.contract_end_date,
                }
                for req in contractors_req
            ])
            .returning(Contractor)
            .options(
                selectinload(Contractor.agency),
                selectinload(Contractor.gp).selectinload(GramPanchayat.block).selectinload(Block.district),
            )
        )
        contractors = contractors.scalars().all()
        await self.db.commit()
        return [map_contractor_to_response(contractor) for contractor in contractors]
