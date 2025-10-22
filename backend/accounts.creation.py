"""Module for creating districts from a CSV file."""

import asyncio
import random
from typing import List

import pandas as pd


from database import get_db
from services.geography import GeographyService
from services.auth import AuthService

from models.database.geography import Block, GramPanchayat

from models.requests.geography import CreateDistrictRequest, CreateBlockRequest, CreateGPRequest
from models.response.geography import BlockResponse, DistrictResponse

DOMAIN = "sbmg-raj.gov.in"
BASE_DIR = "preprocessing"
DISTRICTS_FILE = f"{BASE_DIR}/data/districts.csv"
BLOCKS_FILE = f"{BASE_DIR}/data/blocks.csv"
GPS_FILE = f"{BASE_DIR}/data/gps.csv"


def generate_random_10_digit_password() -> str:
    """Generate a random 10-digit password."""
    return str(random.randint(1_000_000_000, 9_999_999_999))


def get_district_username(district_name: str) -> str:
    """Generate a username for a district based on its name."""
    return str(district_name).lower().replace(" ", "-")


def get_block_username(district_name: str, block_name: str) -> str:
    """Generate a username for a block based on its district and block name."""
    return f"{district_name}.{block_name.lower().replace(' ', '-')}".lower().replace(" ", "-")


def get_gp_username(gp_name: str, block_name: str, district_name: str) -> str:
    """Generate a username for a gram panchayat based on its district, block, and gp name."""
    return f"{get_block_username(district_name, block_name)}.{gp_name.lower().replace(' ', '-')}".replace(" ", "-")


def get_gp_contractor_username(gp_name: str, block_name: str, district_name: str) -> str:
    """Generate a contractor username for a gram panchayat based on its district, block, and gp name."""
    return f"{get_gp_username(gp_name, block_name, district_name)}.contractor".replace(" ", "-")


async def create_districts(geography_service: GeographyService, auth_service: AuthService) -> None:
    """Create districts from the districts CSV file.
    This function reads the districts from a CSV file and creates them
    in the system using the GeographyService.
    """
    districts_df = pd.read_csv(DISTRICTS_FILE)  # type: ignore
    districts_df["Username"] = districts_df["New District"].apply(lambda x: get_district_username(x))
    districts_df["Password"] = districts_df.apply(
        lambda x: generate_random_10_digit_password(),
        axis=1,
    )
    districts_df.to_csv(DISTRICTS_FILE, index=False)
    await asyncio.gather(
        *[
            auth_service.create_user(
                username=row["Username"],
                password=row["Password"],
                email=f"{row['Username']}@{DOMAIN}",
                district_id=row["District ID"],
            )
            for _, row in districts_df.iterrows()
        ],
        return_exceptions=True,
    )
    print("Districts created successfully.")


async def create_blocks(geography_service: GeographyService, auth_service: AuthService) -> None:
    """Create blocks from the blocks CSV file.
    This function reads the blocks from a CSV file and creates them
    in the system using the GeographyService.
    """
    # Load existing districts to map district names to IDs
    blocks_df = pd.read_csv(BLOCKS_FILE)  # type: ignore
    print(blocks_df.head(500))
    blocks_df["Username"] = blocks_df.apply(
        lambda x: get_block_username(x["Block Name"], x["New District"]),
        axis=1,
    )
    blocks_df["Password"] = blocks_df.apply(
        lambda x: generate_random_10_digit_password(),
        axis=1,
    )
    blocks_df.to_csv(BLOCKS_FILE, index=False)
    for _, row in blocks_df.iterrows():
        print(f"Creating block user: {row['Username']} with password: {row['Password']}")
        await auth_service.create_user(
            username=row["Username"],
            password=row["Password"],
            email=f"{row['Username']}@{DOMAIN}",
            block_id=row["ID"],
            district_id=row["District ID"],
        )
    print("Blocks created successfully.")


async def create_gps(geography_service: GeographyService, auth_service: AuthService) -> None:
    """Create gram panchayats from the GPS CSV file.
    This function reads the gram panchayats from a CSV file and creates them
    in the system using the GeographyService.
    """
    gps_df = pd.read_csv(GPS_FILE)  # type: ignore
    gps_df["VDO Username"] = gps_df.apply(
        lambda x: get_gp_username(
            str(x["GP Name"]),
            str(x["Block Name"]),
            str(x["New District"]),
        ),
        axis=1,
    )
    gps_df["VDO Password"] = gps_df.apply(
        lambda x: generate_random_10_digit_password(),
        axis=1,
    )
    # Save in a different file to avoid overwriting original data
    gps_df.to_csv(f"{BASE_DIR}/data/gps-vdo.csv", index=False)
    # Create the users in the system
    for _, row in gps_df.iterrows():
        print(f"Creating GP VDO user: {row['VDO Username']} with password: {row['VDO Password']}")
        # await auth_service.create_user(
        #     username=row["VDO Username"],
        #     password=row["VDO Password"],
        #     email=f"{row['VDO Username']}@{DOMAIN}",
        #     gp_id=row["GP ID"],
        #     block_id=row["Block ID"],
        #     district_id=row["District ID"],
        # )
        continue
    print("Gram Panchayat VDOs created successfully.")

    del gps_df["VDO Username"]
    del gps_df["VDO Password"]

    gps_df["Contractor Username"] = gps_df.apply(
        lambda x: get_gp_contractor_username(
            str(x["GP Name"]),
            str(x["Block Name"]),
            str(x["New District"]),
        ),
        axis=1,
    )
    gps_df["Contractor Password"] = gps_df.apply(
        lambda x: generate_random_10_digit_password(),
        axis=1,
    )
    gps_df.to_csv(f"{BASE_DIR}/data/gps-contractor.csv", index=False)
    # Create contractor users in the system
    for _, row in gps_df.iterrows():
        print(f"Creating GP Contractor user: {row['Contractor Username']} with password: {row['Contractor Password']}")
        await auth_service.create_user(
            username=row["Contractor Username"],
            password=row["Contractor Password"],
            email=f"{row['Contractor Username']}@{DOMAIN}",
            gp_id=row["GP ID"],
            block_id=row["Block ID"],
            district_id=row["District ID"],
        )
    print("Gram Panchayat Contractors created successfully.")


async def main() -> None:
    """Main function to create districts, blocks, and gram panchayats."""
    async for db in get_db():
        geography_service = GeographyService(db)
        auth_service = AuthService(db)
        # await create_districts(geography_service, auth_service)
        # await create_blocks(geography_service, auth_service)
        await create_gps(geography_service, auth_service)


if __name__ == "__main__":
    asyncio.run(main())
