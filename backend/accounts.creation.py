"""Module for creating districts from a CSV file."""

import asyncio
from typing import List

import pandas as pd


from services.geography import GeographyService
from services.auth import AuthService

from models.database.geography import Block

from models.requests.geography import CreateDistrictRequest, CreateBlockRequest, CreateGPRequest
from models.response.geography import BlockResponse, DistrictResponse, GPResponse


BASE_DIR = "preprocessing"
DISTRICTS_FILE = f"{BASE_DIR}/data/districts.csv"
BLOCKS_FILE = f"{BASE_DIR}/data/blocks.csv"
GPS_FILE = f"{BASE_DIR}/data/gps.csv"


def get_district_username(district: DistrictResponse) -> str:
    """Generate a username for a district based on its name."""
    return district.name.lower().replace(" ", "-")


def get_block_username(block: Block) -> str:
    """Generate a username for a block based on its district and block name."""
    return f"{get_district_username(block.district)}-{block.name.lower().replace(' ', '-')}"


def get_gp_username(gp: GPResponse) -> str:
    """Generate a username for a gram panchayat based on its district, block, and gp name."""
    return f"{get_block_username(gp.block)}-{gp.name.lower().replace(' ', '-')}"


async def create_districts(geography_service: GeographyService, auth_service: AuthService) -> None:
    """Create districts from the districts CSV file.
    This function reads the districts from a CSV file and creates them
    in the system using the GeographyService.
    """
    # Check if a district with the same name already exists
    existing_districts = await geography_service.list_districts()
    existing_district_names = {district.name for district in existing_districts}
    # Load districts from the CSV file
    districts_df = pd.read_csv(DISTRICTS_FILE)  # type: ignore
    new_districts: List[CreateDistrictRequest] = []
    for _, row in districts_df.iterrows():
        district_name = row["New District"]
        if district_name not in existing_district_names:
            new_districts.append(CreateDistrictRequest(name=district_name, description="Auto Created"))
    # Create new districts concurrently
    await asyncio.gather(
        *[geography_service.create_district(district_request) for district_request in new_districts],
        return_exceptions=True,
    )
    # Get the list of newly created districts to create corresponding user accounts
    created_districts = await geography_service.list_districts()
    new_created_districts: List[DistrictResponse] = [
        district for district in created_districts if district.name not in existing_district_names
    ]
    await asyncio.gather(
        *[
            auth_service.create_user(
                username=district.name.lower().replace(" ", "-"),
                password="password",
                email=f"{district.name.lower().replace(' ', '-')}@example.com",
                district_id=district.id,
            )
            for district in new_created_districts
        ],
        return_exceptions=True,
    )


async def create_blocks(geography_service: GeographyService, auth_service: AuthService) -> None:
    """Create blocks from the blocks CSV file.
    This function reads the blocks from a CSV file and creates them
    in the system using the GeographyService.
    """
    # Load existing districts to map district names to IDs
    existing_districts = await geography_service.list_districts()
    blocks_df = pd.read_csv(BLOCKS_FILE)  # type: ignore
    new_blocks: List[CreateBlockRequest] = []
    for _, row in blocks_df.iterrows():
        block_name = row["Block Name"]
        district_name = row["New District"]
        district_id = next(
            (district.id for district in existing_districts if district.name == district_name),
            None,
        )
        if district_id is not None:
            new_blocks.append(
                CreateBlockRequest(
                    name=block_name,
                    description="Auto Created",
                    district_id=district_id,
                )
            )
    # Create new blocks concurrently
    new_created_blocks = await asyncio.gather(
        *[geography_service.create_block(block_request) for block_request in new_blocks],
        return_exceptions=True,
    )
    await asyncio.gather(
        *[
            auth_service.create_user(
                username=get_block_username(block),
                password="password",
                email=f"{get_block_username(block)}@example.com",
                block_id=block.id,
            )
            for block in new_created_blocks
            if isinstance(block, BlockResponse)
        ],
        return_exceptions=True,
    )


async def create_gps(geography_service: GeographyService) -> None:
    """Create gram panchayats from the GPS CSV file.
    This function reads the gram panchayats from a CSV file and creates them
    in the system using the GeographyService.
    """
    # Load existing districts and blocks to map names to IDs
    existing_districts = await geography_service.list_districts()
    existing_blocks = await geography_service.list_blocks()
    gps_df = pd.read_csv(GPS_FILE)  # type: ignore
    new_gps: List[CreateGPRequest] = []
    for _, row in gps_df.iterrows():
        gp_name = row["GP Name"]
        block_name = row["Block Name"]
        district_name = row["New District"]
        district_id = next(
            (district.id for district in existing_districts if district.name == district_name),
            None,
        )
        block_id = next(
            (block.id for block in existing_blocks if block.name == block_name and block.district_id == district_id),
            None,
        )
        if district_id is not None and block_id is not None:
            new_gps.append(
                CreateGPRequest(
                    name=gp_name,
                    description="Auto Created",
                    block_id=block_id,
                    district_id=district_id,
                )
            )
    # Create new gram panchayats concurrently
    await asyncio.gather(
        *[geography_service.create_gp(gp_request) for gp_request in new_gps],
        return_exceptions=True,
    )
