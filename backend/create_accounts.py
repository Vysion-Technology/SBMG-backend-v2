import json
import os
from pydantic import BaseModel

# Password generation
import secrets
from models.requests.geography import (
    CreateDistrictRequest,
    CreateBlockRequest,
    CreateGPRequest,
)
from sqlalchemy.ext.asyncio import AsyncSession
from models.database.geography import District, Block, GramPanchayat
from services.geography import GeographyService
from services.auth import AuthService
from database import get_db

from typing import Dict, List, Optional
import pandas as pd


df = pd.read_csv("./Blocks.csv")  # type: ignore

# Get the unique district names
districts = df["District Name"].unique()


print("Unique Districts: ", len(districts))
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
    return await geo_service.create_gp(
        CreateGPRequest(district_id=district_id, block_id=block_id, name=name)
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
    contractor: bool = False,
) -> None:
    username: str = ""
    username, email = generate_username_and_email(
        district_id, block_id, village_id, district_name, block_name, village_name
    )
    # Create user
    # Check if the user with the username exists
    existing_user = await auth_service.get_user_by_username(username)
    if village_id and village_name and contractor:
        # Create contractor account as well
        contractor_username = f"{username}.contractor"
        existing_contractor = await auth_service.get_user_by_username(
            contractor_username
        )
        if not existing_contractor:
            contractor_email = contractor_username + "@sbmg-rajasthan.gov.in"
            contractor_user = await auth_service.create_user(
                username=contractor_username,
                email=contractor_email,
                password=password,
                district_id=district_id,
                block_id=block_id,
                gp_id=village_id,
            )
            print(f"Created contractor user: {contractor_user.username}")
        return
    if existing_user:
        print(f"User with username {username} already exists.")
        return

    user = await auth_service.create_user(
        username=username,
        email=email,
        password=password,
        district_id=district_id,
        block_id=block_id,
        gp_id=village_id,
    )
    print(f"Created user: {user.username}")


def generate_username_and_email(
    district_id: Optional[int] = None,
    block_id: Optional[int] = None,
    village_id: Optional[int] = None,
    district_name: Optional[str] = None,
    block_name: Optional[str] = None,
    village_name: Optional[str] = None,
):
    username = ""
    if district_id and district_name:
        username += f"{district_name.lower().replace(' ', '_')}"
    if block_id and block_name:
        username += f".{block_name.lower().replace(' ', '_')}"
    if village_id and village_name:
        username += f".{village_name.lower().replace(' ', '_')}"
    if not username:
        username = "smd"
    email: str = username + "@abmg-rajasthan.gov.in"
    return username, email


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
        print("District Data Saved")
        await save_block_data(auth_service, geo_service, district_name_to_id)
        print("Block Data Saved")
        await save_gp_data(auth_service, geo_service, district_name_to_id)
        print("Village Data Saved")


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
                "username": generate_username_and_email(  # type: ignore
                    district_id=district_id,
                    block_id=None,
                    village_id=None,
                    district_name=district_name,
                    block_name=None,
                    village_name=None,
                )[0],
                "password": district_name_to_pwd[district_name],
            }
            for district_name, district_id in district_name_to_id.items()
        ]
    )

    df_districts.to_csv("district_passwords.csv", index=False)
    return res


async def save_block_data(
    auth_service: AuthService,
    geo_service: GeographyService,
    district_name_to_id: Dict[str, int],
) -> List[Block]:
    res: List[Block] = []
    df_blocks = df[["District Name", "Block Name"]].drop_duplicates()
    block_passwords: Dict[str, str] = {}
    if os.path.exists("block_passwords.csv"):
        df_block_passwords: pd.DataFrame = pd.read_csv("block_passwords.csv")  # type: ignore
        block_passwords: Dict[str, str] = {
            f"{row['district']}/{row['block']}": row["password"]
            for _, row in df_block_passwords.iterrows()
        }
    else:
        print("block_passwords.csv not found. Creating new block passwords.")
    print(f"Block to password map: {json.dumps(block_passwords, indent=2)}")
    for _, row in df_blocks.iterrows():
        district_name: str = row["District Name"]
        block_name: str = row["Block Name"]
        district_id: int = district_name_to_id[district_name]
        existing_blocks = await geo_service.list_blocks(district_id=district_id)
        # Check that the block does not already exist
        geo_service = await get_geography_service(geo_service.db)
        if any(b.name == block_name for b in existing_blocks):
            print(f"Block {block_name} already exists in district {district_name}")
            continue
        block = await create_block(geo_service, district_id, block_name)
        res.append(block)
        print(f"Created block: {block.name} in district {district_name}")
        # For all blocks, create resp user accounts
        pwd: str = block_passwords.get(
            f"{district_name}/{block_name}"
        ) or secrets.token_urlsafe(8)
        print(f"Password for block {block.name}: {pwd}")
        block_passwords[f"{district_name}/{block_name}"] = pwd
        await create_account(
            auth_service,
            geo_service,
            password=pwd,
            district_id=district_id,
            block_id=block.id,
            district_name=district_name,
            block_name=block_name,
        )
    block_passwords_df = pd.DataFrame(
        [
            {
                "district": k.split("/")[0],
                "block": k.split("/")[1],
                "username": generate_username_and_email(  # type: ignore
                    district_id=None,
                    block_id=None,
                    village_id=None,
                    district_name=k.split("/")[0],
                    block_name=k.split("/")[1],
                    village_name=None,
                )[0],
                "password": v,
            }
            for k, v in block_passwords.items()
        ]
    )
    block_passwords_df.to_csv("block_passwords.csv", index=False)
    return res


async def save_gp_data(
    auth_service: AuthService,
    geo_service: GeographyService,
    district_name_to_id: Dict[str, int],
) -> List[GramPanchayat]:
    res: List[GramPanchayat] = []
    df_villages = df[
        ["District Name", "Block Name", "Gram Panchayat Name"]
    ].drop_duplicates()
    # for _, row in df_villages.iterrows():
    #     district_name: str = row["District Name"]
    #     block_name: str = row["Block Name"]
    #     village_name: str = row["Gram Panchayat Name"]
    #     district_id: int = district_name_to_id[district_name]
    #     existing_blocks = await geo_service.list_blocks(district_id=district_id)
    res: List[GramPanchayat] = []
    df_villages = df[
        ["District Name", "Block Name", "Gram Panchayat Name"]
    ].drop_duplicates()
    village_passwords: Dict[str, str] = {}
    contractor_passwords: Dict[str, str] = {}
    print("Loading existing village and contractor passwords if any")
    if os.path.exists("village_passwords.csv"):
        df_village_passwords: pd.DataFrame = pd.read_csv("village_passwords.csv")  # type: ignore
        village_passwords: Dict[str, str] = {
            f"{row['district']}/{row['block']}/{row['village']}": row["password"]
            for _, row in df_village_passwords.iterrows()
        }
    else:
        print("village_passwords.csv not found. Creating new village passwords.")
    if os.path.exists("contractor_passwords.csv"):
        df_contractor_passwords: pd.DataFrame = pd.read_csv(  # type: ignore
            "contractor_passwords.csv"
        )
        contractor_passwords: Dict[str, str] = {
            f"{row['district']}/{row['block']}/{row['village']}": row["password"]
            for _, row in df_contractor_passwords.iterrows()
        }
    else:
        print("contractor_passwords.csv not found. Creating new contractor passwords.")
    print(f"Village to password map: {json.dumps(village_passwords, indent=2)}")
    print(f"Contractor to password map: {json.dumps(contractor_passwords, indent=2)}")
    for _, row in df_villages.iterrows():
        district_name: str = row["District Name"]
        block_name: str = row["Block Name"]
        village_name: str = row["Gram Panchayat Name"]
        district_id: int = district_name_to_id[district_name]
        existing_blocks = await geo_service.list_blocks(district_id=district_id)
        block = next((b for b in existing_blocks if b.name == block_name), None)
        if not block:
            print(f"Block {block_name} does not exist in district {district_name}")
            continue
        existing_villages = await geo_service.list_villages(block_id=block.id)
        if any(v.name == village_name for v in existing_villages):
            print(
                f"Village {village_name} already exists in block {block_name}, district {district_name}"
            )
            village = next(v for v in existing_villages if v.name == village_name)
            # continue
        else:
            village = await create_village(
                geo_service, district_id, block.id, village_name
            )
        res.append(village)
        print(
            f"Created GP: {village.name} in block {block_name}, district {district_name}"
        )
        # For all villages, create resp user accounts
        pwd = village_passwords.get(
            f"{district_name}/{block_name}/{village_name}"
        ) or secrets.token_urlsafe(8)
        village_passwords[f"{district_name}/{block_name}/{village_name}"] = pwd
        print(f"Password for village {village.name}: {pwd}")
        await create_account(
            auth_service,
            geo_service,
            password=pwd,
            district_id=district_id,
            block_id=block.id,
            village_id=village.id,
            district_name=district_name,
            block_name=block_name,
            village_name=village_name,
        )
        # Create contractor account as well
        contractor_pwd = contractor_passwords.get(
            f"{district_name}/{block_name}/{village_name}"
        ) or secrets.token_urlsafe(8)
        contractor_passwords[f"{district_name}/{block_name}/{village_name}"] = (
            contractor_pwd
        )
        print(f"Password for contractor in village {village.name}: {contractor_pwd}")
        await create_account(
            auth_service,
            geo_service,
            password=contractor_pwd,
            district_id=district_id,
            block_id=block.id,
            village_id=village.id,
            district_name=district_name,
            block_name=block_name,
            village_name=village_name,
            contractor=True,
        )

    village_passwords_df = pd.DataFrame(
        [
            {
                "district": k.split("/")[0],
                "block": k.split("/")[1],
                "village": k.split("/")[2],
                "username": generate_username_and_email(  # type: ignore
                    district_id=None,
                    block_id=None,
                    village_id=None,
                    district_name=k.split("/")[0],
                    block_name=k.split("/")[1],
                    village_name=k.split("/")[2],
                )[0],
                "password": v,
            }
            for k, v in village_passwords.items()
        ]
    )
    village_passwords_df.to_csv("village_passwords.csv", index=False)
    contractor_passwords_df = pd.DataFrame(
        [
            {
                "district": k.split("/")[0],
                "block": k.split("/")[1],
                "village": k.split("/")[2],
                "username": generate_username_and_email(  # type: ignore
                    district_id=None,
                    block_id=None,
                    village_id=None,
                    district_name=k.split("/")[0],
                    block_name=k.split("/")[1],
                    village_name=k.split("/")[2],
                )[0]
                + ".contractor",
                "password": v,
            }
            for k, v in contractor_passwords.items()
        ]
    )
    contractor_passwords_df.to_csv("contractor_passwords.csv", index=False)
    return res


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
