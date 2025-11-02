"""Script to create bulk notices for testing purposes."""

import asyncio
import random
from typing import List

from faker import Faker

from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.database.geography import GramPanchayat
from models.requests.geography import CreateVillageRequest
from models.database.auth import PositionHolder, User
from services.annual_survey import AnnualSurveyService
from services.auth import AuthService
from services.geography import GeographyService
from services.notice import NoticeService


SMD_POS_HOLDER_ID = 17781  # Replace with actual SMD position holder ID


async def get_all_position_holders(auth_svc: AuthService) -> List[PositionHolder]:
    """Fetch all position holders from the database."""
    position_holders = await auth_svc.get_all_position_holders()
    return position_holders


async def notices_from_smd(
    db: AsyncSession,
    position_holders: List[PositionHolder],
) -> None:
    """Create bulk notices from SMD to CEO for testing."""
    notice_svc = NoticeService(db)
    auth_svc = AuthService(db)

    ceo_position_holders = filter(lambda ph: ph.user.role == "CEO", position_holders)
    await notice_svc.send_bulk_notices(
        notice_type_id=random.randint(1, 7),  # Assuming notice type IDs 1-7 exist
        sender_id=SMD_POS_HOLDER_ID,
        receiver_ids=[ph.id for ph in ceo_position_holders],
        title="Important Notice from SMD",
        text="This is a bulk notice sent from SMD to all CEOs for testing purposes.",
    )
    # Get BDO position holders
    bdo_position_holders = filter(lambda ph: ph.user.role == "BDO", position_holders)
    # Select 10% randomly
    bdo_position_holders = random.sample(
        list(bdo_position_holders),
        k=max(1, len(list(bdo_position_holders)) // 10),
    )
    await notice_svc.send_bulk_notices(
        notice_type_id=random.randint(1, 7),  # Assuming notice type IDs 1-7 exist
        sender_id=SMD_POS_HOLDER_ID,
        receiver_ids=[ph.id for ph in bdo_position_holders],
        title="Important Notice from SMD",
        text="This is a bulk notice sent from SMD to selected BDOs for testing purposes.",
    )
    # Send notices to random VDOs
    vdo_position_holders = filter(lambda ph: ph.user.role == "VDO", position_holders)
    vdo_position_holders = random.sample(
        list(vdo_position_holders),
        k=max(1, len(list(vdo_position_holders)) // 20),
    )
    await notice_svc.send_bulk_notices(
        notice_type_id=random.randint(1, 7),  # Assuming notice type IDs 1-7 exist
        sender_id=SMD_POS_HOLDER_ID,
        receiver_ids=[ph.id for ph in vdo_position_holders],
        title="Important Notice from SMD",
        text="This is a bulk notice sent from SMD to selected VDOs for testing purposes.",
    )


async def notices_from_ceo(
    db: AsyncSession,
    position_holders: List[PositionHolder],
) -> None:
    """Create bulk notices from CEO to BDOs for testing."""
    notice_svc = NoticeService(db)
    auth_svc = AuthService(db)

    ceo_position_holders = list(filter(lambda ph: ph.user.role == "CEO", position_holders))
    for ceo_ph in ceo_position_holders:
        bdo_position_holders = filter(
            lambda ph: ph.user.role == "BDO" and ph.user.district_id == ceo_ph.user.district_id,
            position_holders,
        )
        # Select 20% randomly
        bdo_position_holders = random.sample(
            list(bdo_position_holders),
            k=max(1, len(list(bdo_position_holders)) // 5),
        )
        await notice_svc.send_bulk_notices(
            notice_type_id=random.randint(1, 7),  # Assuming notice type IDs 1-7 exist
            sender_id=ceo_ph.id,
            receiver_ids=[ph.id for ph in bdo_position_holders],
            title="Important Notice from CEO",
            text="This is a bulk notice sent from CEO to selected BDOs for testing purposes.",
        )
    # send notice to 20% of VDOs from random CEOs with same district
    vdo_position_holders = list(filter(lambda ph: ph.user.role == "VDO", position_holders))
    for ceo_ph in ceo_position_holders:
        vdos_in_district = filter(
            lambda ph: ph.user.district_id == ceo_ph.user.district_id,
            vdo_position_holders,
        )
        vdos_in_district = random.sample(
            list(vdos_in_district),
            k=max(1, len(list(vdos_in_district)) // 5),
        )
        await notice_svc.send_bulk_notices(
            notice_type_id=random.randint(1, 7),  # Assuming notice type IDs 1-7 exist
            sender_id=ceo_ph.id,
            receiver_ids=[ph.id for ph in vdos_in_district],
            title="Important Notice from CEO",
            text="This is a bulk notice sent from CEO to selected VDOs for testing purposes.",
        )


async def notices_from_bdo(
    db: AsyncSession,
    position_holders: List[PositionHolder],
) -> None:
    """Create bulk notices from BDO to VDOs for testing."""
    notice_svc = NoticeService(db)
    auth_svc = AuthService(db)

    bdo_position_holders = list(filter(lambda ph: ph.user.role == "BDO", position_holders))
    for bdo_ph in bdo_position_holders:
        vdo_position_holders = filter(
            lambda ph: ph.user.role == "VDO" and ph.user.block_id == bdo_ph.user.block_id,
            position_holders,
        )
        # Select 30% randomly
        vdo_position_holders = random.sample(
            list(vdo_position_holders),
            k=max(1, len(list(vdo_position_holders)) * 3 // 10),
        )
        await notice_svc.send_bulk_notices(
            notice_type_id=random.randint(1, 7),  # Assuming notice type IDs 1-7 exist
            sender_id=bdo_ph.id,
            receiver_ids=[ph.id for ph in vdo_position_holders],
            title="Important Notice from BDO",
            text="This is a bulk notice sent from BDO to selected VDOs for testing purposes.",
        )


async def main():
    """Main function to create bulk notices."""
    async for db in get_db():
        auth_svc = AuthService(db)
        position_holders = await get_all_position_holders(auth_svc)
        print(f"Fetched {len(position_holders)} position holders.")

        print("Starting to create bulk notices from SMD to CEOs, BDOs, and VDOs...")
        await notices_from_smd(db, position_holders)
        print("Finished creating bulk notices.")


        print("Starting to create bulk notices from CEOs to BDOs and VDOs...")
        await notices_from_ceo(db, position_holders)
        print("Finished creating bulk notices.")

        print("Starting to create bulk notices from BDOs to VDOs...")
        await notices_from_bdo(db, position_holders)
        print("Finished creating bulk notices.")


if __name__ == "__main__":
    asyncio.run(main())
