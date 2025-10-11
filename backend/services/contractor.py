from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database.contractor import Agency


class ContractorService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_agency_by_id(self, agency_id: int) -> Agency:
        result = await self.db.execute(select(Agency).where(Agency.id == agency_id))
        return result.scalar_one()
