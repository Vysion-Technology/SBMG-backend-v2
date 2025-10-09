from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from models.database.auth import User


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_users_by_geo(
        self,
        district_id: int,
        block_id: Optional[int] = None,
        village_id: Optional[int] = None,
    ) -> List[User]:
        query = select(User).where(User.district_id == district_id)

        if block_id is not None:
            query = query.where(User.block_id == block_id)
        if village_id is not None:
            query = query.where(User.village_id == village_id)

        result = await self.db.execute(query)
        users = result.scalars().all()
        return list(users)
