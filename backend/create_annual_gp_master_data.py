"""Script to create bulk agencies for testing purposes."""

import asyncio
import random
from typing import List

from faker import Faker

from database import get_db
from models.database.geography import GramPanchayat
from models.requests.geography import CreateVillageRequest
from models.database.auth import PositionHolder, User
from services.annual_survey import AnnualSurveyService
from services.auth import AuthService
from services.geography import GeographyService


faker = Faker()


async def get_all_gps(geo_svc: GeographyService) -> List[GramPanchayat]:
    """Fetch all Gram Panchayat IDs from the database."""
    gps = await geo_svc.list_villages()
    return gps


async def create_bulk_villages(gps: List[GramPanchayat], geo_svc: GeographyService):
    """Create bulk villages for testing."""
    create_village_req: List[CreateVillageRequest] = []
    for gp in gps:
        create_village_req.extend([
            CreateVillageRequest(
                name=faker.city() + "".join(random.sample("abcdefghijlmnopqrstuvwxyz1234567890", 5)),
                gp_id=gp.id,
                description=None,
            )
            for _ in range(random.randint(4, 15))
        ])
    # Insert in batches of 1000
    batch_size = 1000
    for i in range(0, len(create_village_req), batch_size):
        print(f"Creating villages {i} to {i + batch_size}...")
        batch = create_village_req[i : i + batch_size]
        await geo_svc.create_bulk_villages(batch)


async def get_all_vdos(auth_svc: AuthService) -> List[PositionHolder]:
    """Fetch all Village Development Officers from the database."""
    vdos = await auth_svc.get_all_active_vdo_position_holders()
    return vdos


async def get_gp_villages_map(geo_svc: GeographyService) -> dict[int, List[int]]:
    """Get a mapping of GP IDs to their village IDs."""
    gp_villages_map: dict[int, List[int]] = {}
    villages = await geo_svc.list_village_entities()
    for village in villages:
        gp_id = village.gp_id
        if gp_id not in gp_villages_map:
            gp_villages_map[gp_id] = []
        gp_villages_map[gp_id].append(village.id)
    return gp_villages_map


async def main():
    """Main function to create annual Gram Panchayat master data."""
    async for db in get_db():
        geo_svc = GeographyService(db)
        auth_svc = AuthService(db)
        annual_survey_svc = AnnualSurveyService(db)

        gps = await get_all_gps(geo_svc)
        print(f"Fetched {len(gps)} Gram Panchayats.")

        # print("Starting to create village entries...")
        # await create_bulk_villages(gps, geo_svc)
        # print("Finished creating village entries.")

        # Get all VDOs
        vdos = await get_all_vdos(auth_svc)
        print(f"Fetched {len(vdos)} Village Development Officers.")

        # ignore gp ids 1, 2, 37 as they are already populated
        ignore_gp_ids = {1, 2, 37}
        ignore_gp_ids.update(
            [num for num in range(1, 204)]  # Ignoring test GPs created earlier
        )
        gp_villages_map = await get_gp_villages_map(geo_svc)
        print(f"Total GPs with villages: {len(gp_villages_map)}")

        # # Remove ignored GP IDs from the map
        for gp_id in ignore_gp_ids:
            gp_villages_map.pop(gp_id, None)
        print(f"GPs to be processed after ignoring some: {len(gp_villages_map)}")

        # Remove VDOs assigned to ignored GPs
        vdos = [
            vdo for vdo in vdos if vdo.user.gp_id not in ignore_gp_ids
        ]
        print(f"VDOs to be processed after ignoring some: {len(vdos)}")

        await annual_survey_svc.fill_annual_survey_bulk(
            fy_id=1,
            vdo_list=vdos,
            gp_villages_map=gp_villages_map,
        )


if __name__ == "__main__":
    asyncio.run(main())
