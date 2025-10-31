"""Script to create bulk agencies for testing purposes."""

import asyncio
from datetime import datetime
import random
from typing import List

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.database.geography import GramPanchayat
from models.response.contractor import AgencyResponse
from services.contractor import ContractorService, CreateContractorRequest
from services.geography import GeographyService


async def get_all_agencies(contractor_service: ContractorService) -> List[AgencyResponse]:
    """Fetch all agencies from the database."""
    result = await contractor_service.list_agencies(limit=1000)
    return result


async def get_all_gps(geo_svc: GeographyService) -> List[GramPanchayat]:
    """Fetch all Gram Panchayat IDs from the database."""
    gps = await geo_svc.list_villages()
    return gps


async def create_bulk_contractors(db: AsyncSession):
    """Create bulk contractors for testing purposes."""
    fake = Faker()
    contractor_service = ContractorService(db)
    geo_svc = GeographyService(db)

    agencies = await get_all_agencies(contractor_service)
    print(f"Fetched {len(agencies)} agencies.")
    agency_ids = [agency.id for agency in agencies]

    gps = await get_all_gps(geo_svc)
    print(f"Fetched {len(gps)} Gram Panchayats.")
    gp_ids = [gp.id for gp in gps]
    print(f"Creating contractors for {len(gp_ids)} Gram Panchayats...")

    for contractor_batch in range(0, len(gp_ids), 500):
        batch_gp_ids = gp_ids[contractor_batch : contractor_batch + 500]
        await contractor_service.create_contractors_bulk([
            CreateContractorRequest(
                agency_id=random.choice(agency_ids),
                person_name=fake.name(),
                person_phone=fake.phone_number(),
                gp_id=gp_id,
                contract_start_date=datetime(2025, 4, 1),
                contract_end_date=datetime(2026, 3, 31),
            )
            for gp_id in batch_gp_ids
        ])
    print("Bulk contractor creation completed.")


async def main():
    """Main function to run the bulk agency creation."""
    async for db in get_db():
        await create_bulk_contractors(db)


if __name__ == "__main__":
    asyncio.run(main())
