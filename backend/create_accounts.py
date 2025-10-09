import json
import os
from pydantic import BaseModel

# Password generation
import secrets
from models.requests.geography import (
    CreateDistrictRequest,
    CreateBlockRequest,
    CreateVillageRequest,
)
from sqlalchemy.ext.asyncio import AsyncSession
from models.database.geography import District, Block, GramPanchayat
from services.geography import GeographyService
from services.auth import AuthService
from database import get_db

from typing import Dict, List, Optional
import pandas as pd


df = pd.read_csv("./Villages.csv")  # type: ignore

# Get the unique district names
districts = df["District Name"].unique()


print("Unique Districts:")
for district in districts:
    print(district)


# Verify that no two districts have the same name
if len(districts) != len(set(districts)):
    print("Error: Duplicate district names found!")
else:
    print("No duplicate district names found.")


async def get_geography_service(db: AsyncSession) -> GeographyService:
    return GeographyService(db)


async def create_district(geo_service: GeographyService, name: str) -> District:
    return await geo_service.create_district(CreateDistrictRequest(name=name))


async def create_block(
    geo_service: GeographyService, district_id: int, name: str
) -> Block:
    return await geo_service.create_block(
        CreateBlockRequest(district_id=district_id, name=name)
    )


async def create_village(
    geo_service: GeographyService, district_id: int, block_id: int, name: str
) -> GramPanchayat:
    return await geo_service.create_village(
        CreateVillageRequest(district_id=district_id, block_id=block_id, name=name)
    )


async def create_account(
    auth_service: AuthService,
    geo_service: GeographyService,
    password: str,
    district_id: Optional[int] = None,
    block_id: Optional[int] = None,
    village_id: Optional[int] = None,
    district_name: Optional[str] = None,
    block_name: Optional[str] = None,
    village_name: Optional[str] = None,
) -> None:
    username: str = ""
    if district_id and district_name:
        username += f"{district_name.lower().replace(' ', '_')}"
    if block_id and block_name:
        username += f".{block_name.lower().replace(' ', '_')}"
    if village_id and village_name:
        username += f".{village_name.lower().replace(' ', '_')}"
    if not username:
        username = "smd"
    email: str = username + "@abmg-rajasthan.gov.in"
    # Create user
    # Check if the user with the username exists
    existing_user = await auth_service.get_user_by_username(username)
    if existing_user:
        print(f"User with username {username} already exists.")
        return

    user = await auth_service.create_user(
        username=username,
        email=email,
        password=password,
        district_id=district_id,
        block_id=block_id,
        village_id=village_id,
    )
    print(f"Created user: {user.username}")


class DistrictItem(BaseModel):
    name: str


class BlockItem(BaseModel):
    name: str
    district: DistrictItem


class VillageItem(BaseModel):
    name: str
    block: BlockItem


async def main():
    async for db in get_db():
        auth_service = AuthService(db)
        geo_service = await get_geography_service(db)
        db_districts = await geo_service.list_districts()
        district_name_to_id: Dict[str, int] = {d.name: d.id for d in db_districts}
        print(f"Existing districts in DB: {[d.name for d in db_districts]}")
        # Create district that do not exist
        await save_district_data(auth_service, geo_service, district_name_to_id)


async def save_district_data(
    auth_service: AuthService,
    geo_service: GeographyService,
    district_name_to_id: Dict[str, int],
) -> List[District]:
    res: List[District] = []
    for district_name in districts:
        if district_name not in district_name_to_id:
            district = await create_district(geo_service, district_name)
            res.append(district)
            district_name_to_id[district.name] = district.id
            print(f"Created district: {district.name}")
        # For all districts, create resp user accounts
    district_name_to_pwd: Dict[str, str] = {}
    if os.path.exists("district_passwords.csv"):
        district_passwords: pd.DataFrame = pd.read_csv("district_passwords.csv")  # type: ignore
        district_name_to_pwd = {
            row["district"]: row["password"] for _, row in district_passwords.iterrows()
        }
    else:
        print("district_passwords.csv not found. Creating new district passwords.")
    print(f"District to password map: {json.dumps(district_name_to_pwd, indent=2)}")
    for district_name in districts:
        district_id = district_name_to_id[district_name]
        pwd: str = secrets.token_urlsafe(8)
        district_name_to_pwd[district_name] = (
            district_name_to_pwd.get(district_name) or pwd
        )
        district = await create_account(
            auth_service,
            geo_service,
            password=district_name_to_pwd[district_name],
            district_id=district_id,
            district_name=district_name,
        )
        # Save district passwords to a CSV file using pandas
    df_districts = pd.DataFrame(
        [
            {
                "id": district_id,
                "district": district_name,
                "password": district_name_to_pwd[district_name],
            }
            for district_name, district_id in district_name_to_id.items()
        ]
    )

    df_districts.to_csv("district_passwords.csv", index=False)
    return res


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
