"""Script to create bulk agencies for testing purposes."""

import asyncio

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.contractor import ContractorService, CreateAgencyRequest


async def create_bulk_agencies(db: AsyncSession, num_agencies: int = 100):
    """Create bulk agencies for testing purposes."""
    fake = Faker()
    contractor_service = ContractorService(db)

    for _ in range(num_agencies):
        await create_agency(fake, contractor_service)


async def create_agency(fake: Faker, contractor_service: ContractorService):
    """Helper function to create a single agency."""
    try:
        await contractor_service.create_agency(
            CreateAgencyRequest(
                name=fake.company(),
                email=fake.company_email(),
                phone=fake.phone_number(),
                address=fake.address(),
            )
        )
    except Exception as e: # pylint: disable=broad-except
        print(f"Error creating agency: {e}")


async def main():
    """Main function to run the bulk agency creation."""
    async for db in get_db():
        await create_bulk_agencies(db, num_agencies=500)


if __name__ == "__main__":
    asyncio.run(main())
