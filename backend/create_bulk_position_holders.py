"""Script to create bulk position holders (contractors) for testing purposes."""

import asyncio
from datetime import date
from uuid import uuid4

import faker
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.requests.position_holder import CreateEmployeeRequest
from services.auth import AuthService
from services.position_holder import PositionHolderService, CreatePositionHolderRequest

fake = faker.Faker()


async def create_bulk_ceo(db: AsyncSession):
    """Create bulk position holders for testing purposes."""
    # Create number of employees equal to number of districts
    auth_svc = AuthService(db)
    ph_svc = PositionHolderService(db)
    ceo_users = await auth_svc.get_ceo_users()
    print(f"Fetched {len(ceo_users)} CEO users.")
    employees = await ph_svc.create_employees_bulk([
        CreateEmployeeRequest(
            first_name=fake.first_name(),
            middle_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.email(),
            employee_id=uuid4().hex[:10],
            mobile_number=fake.phone_number(),
        )
        for _ in range(len(ceo_users))
    ])
    employees.sort(key=lambda emp: emp.id)
    print(f"Created {len(employees)} employees.")
    # Create position holders for each district
    position_holders = await ph_svc.create_position_holders_bulk([
        CreatePositionHolderRequest(
            user_id=ceo_user.id,
            role_id=3,
            employee_id=employee.id,
            district_id=ceo_user.district_id,
            start_date=date(2025, 4, 1),
            date_of_joining=date(2025, 4, 1),
            end_date=None,
            block_id=None,
            gp_id=None,
        )
        for employee, ceo_user in zip(employees, ceo_users)
    ])
    print(f"Created {len(position_holders)} position holders.")


async def create_bulk_bdo(db: AsyncSession):
    """Create bulk BDO position holders for testing purposes."""
    # Implementation would be similar to create_bulk_ceo but for BDOs
    auth_svc = AuthService(db)
    bdo_users = await auth_svc.get_bdo_users()
    print(f"Fetched {len(bdo_users)} BDO users.")
    # Create employees and position holders similarly
    ph_svc = PositionHolderService(db)

    # Process in batches of 500
    batch_size = 500
    total_created = 0

    for i in range(0, len(bdo_users), batch_size):
        batch_users = bdo_users[i : i + batch_size]
        print(f"Processing batch {i // batch_size + 1} ({len(batch_users)} users)...")

        employees = await ph_svc.create_employees_bulk([
            CreateEmployeeRequest(
                first_name=fake.first_name(),
                middle_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.email(),
                employee_id=uuid4().hex[:10],
                mobile_number=fake.phone_number(),
            )
            for _ in range(len(batch_users))
        ])
        employees.sort(key=lambda emp: emp.id)
        print(f"Created {len(employees)} employees in this batch.")

        position_holders = await ph_svc.create_position_holders_bulk([
            CreatePositionHolderRequest(
                user_id=bdo_user.id,
                role_id=4,
                employee_id=employee.id,
                district_id=bdo_user.district_id,
                block_id=bdo_user.block_id,
                start_date=date(2025, 4, 1),
                date_of_joining=date(2025, 4, 1),
                end_date=None,
                gp_id=None,
            )
            for employee, bdo_user in zip(employees, batch_users)
        ])
        total_created += len(position_holders)
        print(f"Created {len(position_holders)} BDO position holders in this batch.")

    print(f"Total BDO position holders created: {total_created}")


async def create_bulk_vdo(db: AsyncSession):
    """Create bulk VDO position holders for testing purposes."""
    # Implementation would be similar to create_bulk_ceo but for VDOs
    auth_svc = AuthService(db)
    vdo_users = await auth_svc.get_vdo_users()
    print(f"Fetched {len(vdo_users)} VDO users.")
    # Create employees and position holders similarly
    ph_svc = PositionHolderService(db)

    # Process in batches of 500
    batch_size = 500
    total_created = 0

    for i in range(0, len(vdo_users), batch_size):
        batch_users = vdo_users[i : i + batch_size]
        print(f"Processing batch {i // batch_size + 1} ({len(batch_users)} users)...")

        employees = await ph_svc.create_employees_bulk([
            CreateEmployeeRequest(
                first_name=fake.first_name(),
                middle_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.email(),
                employee_id=uuid4().hex[:10],
                mobile_number=fake.phone_number(),
            )
            for _ in range(len(batch_users))
        ])
        employees.sort(key=lambda emp: emp.id)
        print(f"Created {len(employees)} employees in this batch.")

        position_holders = await ph_svc.create_position_holders_bulk([
            CreatePositionHolderRequest(
                user_id=vdo_user.id,
                role_id=5,
                employee_id=employee.id,
                district_id=vdo_user.district_id,
                block_id=vdo_user.block_id,
                gp_id=vdo_user.gp_id,
                start_date=date(2025, 4, 1),
                date_of_joining=date(2025, 4, 1),
                end_date=None,
            )
            for employee, vdo_user in zip(employees, batch_users)
        ])
        total_created += len(position_holders)
        print(f"Created {len(position_holders)} VDO position holders in this batch.")

    print(f"Total VDO position holders created: {total_created}")


async def main():  # type: ignore
    """Main function to run the bulk agency creation."""
    async for db in get_db():
        await create_bulk_ceo(db)


if __name__ == "__main__":
    asyncio.run(main())
