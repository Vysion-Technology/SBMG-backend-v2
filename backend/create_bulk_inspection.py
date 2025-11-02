"""Create bulk inspection records for testing.

This script is inspired by `create_annual_gp_master_data.py` and creates
inspection records for Gram Panchayats using the existing services.

Usage: python create_bulk_inspection.py
"""

import asyncio
import random
from datetime import date, datetime, timedelta
from typing import List, Optional

from faker import Faker

from database import get_db
from services.geography import GeographyService
from services.auth import AuthService
from services.inspection import InspectionService
from models.requests.inspection import (
    CreateInspectionRequest,
    HouseHoldWasteCollectionRequest,
    RoadAndDrainCleaningRequest,
    CommunitySanitationRequest,
    OtherInspectionItemsRequest,
)
from models.database.auth import PositionHolder
from models.database.inspection import (
    WasteCollectionFrequency,
    RoadCleaningFrequency,
    DrainCleaningFrequency,
    CSCCleaningFrequency,
)


faker = Faker()


def _random_enum_choice(enum_cls: Optional[object]) -> object:
    """Return a random choice from the given Enum class."""
    choices = list(enum_cls)  # type: ignore
    return random.choice(choices)  # type: ignore


def _random_bool(prob: float = 0.7) -> bool:
    return random.random() < prob


async def main():
    """Main function to create bulk inspections."""
    async for db in get_db():
        geo_svc = GeographyService(db)
        auth_svc = AuthService(db)
        insp_svc = InspectionService(db)

        gps = await geo_svc.list_villages()
        # gps = gps[:1]

        # Get all position holders and filter to active non-VDO inspectors
        all_position_holders = await auth_svc.get_all_position_holders()
        inspectors: List[PositionHolder] = []
        for ph in all_position_holders:
            # Keep only active positions and exclude VDO role (they cannot inspect)
            user = getattr(ph, "user", None)
            inspectors.append(ph)

        if not inspectors:
            print("No eligible inspectors found (non-VDO, active). Exiting.")
            return

        print(f"Found {len(inspectors)} eligible inspectors")

        created = 0
        skipped = 0

        # For each GP create a few inspections
        for gp in gps:
            # Check if this GP should be inspected
            if _random_bool(0.3):
                print(f"Skipping GP {gp.id} based on random choice")
                continue
            # Create between 1 and 3 inspections per GP
            for _ in range(random.randint(1, 3)):
                eligible_inspectors = [
                    ph
                    for ph in inspectors
                    if any([
                        ph.gp_id == gp.id,
                        (ph.block_id == gp.block_id and ph.gp_id is None),
                        (ph.district_id == gp.district_id and ph.block_id is None),
                    ])
                ]
                print(f"GP {gp.id} has {len(eligible_inspectors)} eligible inspectors before adding general inspectors")
                eligible_inspectors.extend(
                    ph for ph in inspectors if all([ph.gp_id is None, ph.block_id is None, ph.district_id is None])
                )
                inspector_ph = random.choice(eligible_inspectors)
                user = inspector_ph.user

                # Build random inspection items (randomly include each item)
                household_waste = HouseHoldWasteCollectionRequest(
                    waste_collection_frequency=_random_enum_choice(WasteCollectionFrequency),  # type: ignore
                    dry_wet_vehicle_segregation=_random_bool(),
                    covered_collection_in_vehicles=_random_bool(),
                    waste_disposed_at_rrc=_random_bool(),
                    rrc_waste_collection_and_disposal_arrangement=_random_bool(),
                    waste_collection_vehicle_functional=_random_bool(),
                )

                road_and_drain = RoadAndDrainCleaningRequest(
                    road_cleaning_frequency=_random_enum_choice(RoadCleaningFrequency),  # type: ignore
                    drain_cleaning_frequency=_random_enum_choice(DrainCleaningFrequency),  # type: ignore
                    disposal_of_sludge_from_drains=_random_bool(),
                    drain_waste_colllected_on_roadside=_random_bool(),
                )

                community_sanitation = None
                if _random_bool(0.6):
                    community_sanitation = CommunitySanitationRequest(
                        csc_cleaning_frequency=_random_enum_choice(CSCCleaningFrequency),  # type: ignore
                        electricity_and_water=_random_bool(),
                        csc_used_by_community=_random_bool(),
                        pink_toilets_cleaning=_random_bool(),
                        pink_toilets_used=_random_bool(),
                    )

                other_items = OtherInspectionItemsRequest(
                    firm_paid_regularly=_random_bool(),
                    cleaning_staff_paid_regularly=_random_bool(),
                    firm_provided_safety_equipment=_random_bool(),
                    regular_feedback_register_entry=_random_bool(),
                    chart_prepared_for_cleaning_work=_random_bool(),
                    village_visibly_clean=_random_bool(),
                    rate_chart_displayed=_random_bool(),
                )

                # Random date in the last 200 days
                inspection_date = date.today() - timedelta(days=random.randint(0, 200))
                # Random start time (keep today's date + random seconds)
                start_time = datetime.now()

                request = CreateInspectionRequest(
                    gp_id=gp.id,
                    village_name=random.choice(gp.villages).name,
                    remarks=faker.sentence(nb_words=8),
                    inspection_date=inspection_date,
                    start_time=start_time,
                    lat=str(faker.latitude()),
                    long=str(faker.longitude()),
                    register_maintenance=_random_bool(0.6),
                    household_waste=household_waste,
                    road_and_drain=road_and_drain,
                    community_sanitation=community_sanitation,
                    other_items=other_items,
                )

                try:
                    inspection = await insp_svc.create_inspection(user, request)
                    created += 1
                    print(f"Created inspection id={inspection.id} gp_id={gp.id} block_id={gp.block_id} district_id={gp.district_id} by user_id={user.id}")
                except Exception as exc:  # pylint: disable=broad-except
                    import traceback

                    traceback.print_exc()
                    skipped += 1
                    print(f"Skipped creating inspection for gp {gp.id} with user {getattr(user, 'id', None)}: {exc}")

        print(f"Done. Created={created}, Skipped={skipped}")


if __name__ == "__main__":
    asyncio.run(main())
