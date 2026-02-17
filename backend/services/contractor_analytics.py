"""
Contractor Analytics Service
Handles business logic for contractor coverage analytics using database-level aggregations
"""

from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct
from sqlalchemy.orm import selectinload

from models.database.contractor import Contractor
from models.database.geography import District, Block, GramPanchayat
from models.response.annual_survey_analytics import VillageMasterDataCoverage
from models.response.contractor_analytics import (
    ContractorStateAnalytics,
    ContractorDistrictAnalytics,
    ContractorBlockAnalytics,
    ContractorGPAnalytics,
    ContractorSummary,
)


class ContractorAnalyticsService:
    """Service for contractor coverage analytics using database aggregations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_state_analytics(self) -> ContractorStateAnalytics:
        """Get state-level contractor analytics."""

        # Main aggregation query
        agg_query = (
            select(
                func.count(distinct(Contractor.gp_id)).label("gps_with_data"),  # type: ignore
                func.count(Contractor.id).label("total_contractors"),  # type: ignore
                func.coalesce(func.sum(Contractor.contract_amount), 0).label("total_contract_amount"),  # type: ignore
            )
            .select_from(Contractor)
        )

        result = await self.db.execute(agg_query)
        row = result.one()

        # Get total GPs
        total_gps_result = await self.db.execute(
            select(func.count()).select_from(GramPanchayat)  # type: ignore
        )
        total_gps = total_gps_result.scalar() or 0

        gps_with_data = row.gps_with_data or 0
        coverage_percentage = (gps_with_data / total_gps * 100) if total_gps > 0 else 0.0

        # District-wise breakdown
        district_wise_coverage = await self._get_district_coverage()

        return ContractorStateAnalytics(
            total_gps=total_gps,
            gps_with_contractor_data=gps_with_data,
            coverage_percentage=round(coverage_percentage, 2),
            total_contractors=row.total_contractors or 0,
            total_contract_amount=round(float(row.total_contract_amount or 0), 2),
            district_wise_coverage=district_wise_coverage,
        )

    async def get_district_analytics(self, district_id: int) -> ContractorDistrictAnalytics:
        """Get district-level contractor analytics."""

        # Get district info
        district_result = await self.db.execute(
            select(District).where(District.id == district_id)
        )
        district = district_result.scalar_one_or_none()
        if not district:
            raise ValueError("District not found")

        # Main aggregation query scoped to district
        agg_query = (
            select(
                func.count(distinct(Contractor.gp_id)).label("gps_with_data"),  # type: ignore
                func.count(Contractor.id).label("total_contractors"),  # type: ignore
                func.coalesce(func.sum(Contractor.contract_amount), 0).label("total_contract_amount"),  # type: ignore
            )
            .select_from(Contractor)
            .join(GramPanchayat, Contractor.gp_id == GramPanchayat.id)
            .where(GramPanchayat.district_id == district_id)
        )

        result = await self.db.execute(agg_query)
        row = result.one()

        # Get total GPs in district
        total_gps_result = await self.db.execute(
            select(func.count())
            .select_from(GramPanchayat)
            .where(  # type: ignore
                GramPanchayat.district_id == district_id
            )
        )
        total_gps = total_gps_result.scalar() or 0

        gps_with_data = row.gps_with_data or 0
        coverage_percentage = (gps_with_data / total_gps * 100) if total_gps > 0 else 0.0

        # Block-wise breakdown
        block_wise_coverage = await self._get_block_coverage(district_id)

        return ContractorDistrictAnalytics(
            district_id=district.id,
            district_name=district.name,
            total_gps=total_gps,
            gps_with_contractor_data=gps_with_data,
            coverage_percentage=round(coverage_percentage, 2),
            total_contractors=row.total_contractors or 0,
            total_contract_amount=round(float(row.total_contract_amount or 0), 2),
            block_wise_coverage=block_wise_coverage,
        )

    async def get_block_analytics(self, block_id: int) -> ContractorBlockAnalytics:
        """Get block-level contractor analytics."""

        # Get block info with district
        block_result = await self.db.execute(
            select(Block).options(selectinload(Block.district)).where(Block.id == block_id)
        )
        block = block_result.scalar_one_or_none()
        if not block:
            raise ValueError("Block not found")

        # Main aggregation query scoped to block
        agg_query = (
            select(
                func.count(distinct(Contractor.gp_id)).label("gps_with_data"),  # type: ignore
                func.count(Contractor.id).label("total_contractors"),  # type: ignore
                func.coalesce(func.sum(Contractor.contract_amount), 0).label("total_contract_amount"),  # type: ignore
            )
            .select_from(Contractor)
            .join(GramPanchayat, Contractor.gp_id == GramPanchayat.id)
            .where(GramPanchayat.block_id == block_id)
        )

        result = await self.db.execute(agg_query)
        row = result.one()

        # Get total GPs in block
        total_gps_result = await self.db.execute(
            select(func.count())
            .select_from(GramPanchayat)
            .where(  # type: ignore
                GramPanchayat.block_id == block_id
            )
        )
        total_gps = total_gps_result.scalar() or 0

        gps_with_data = row.gps_with_data or 0
        coverage_percentage = (gps_with_data / total_gps * 100) if total_gps > 0 else 0.0

        # GP-wise breakdown
        gp_wise_coverage = await self._get_gp_coverage(block_id)

        return ContractorBlockAnalytics(
            block_id=block.id,
            block_name=block.name,
            district_id=block.district.id,
            district_name=block.district.name,
            total_gps=total_gps,
            gps_with_contractor_data=gps_with_data,
            coverage_percentage=round(coverage_percentage, 2),
            total_contractors=row.total_contractors or 0,
            total_contract_amount=round(float(row.total_contract_amount or 0), 2),
            gp_wise_coverage=gp_wise_coverage,
        )

    async def get_gp_analytics(self, gp_id: int) -> ContractorGPAnalytics:
        """Get GP-level contractor analytics."""

        # Get GP info with block and district
        gp_result = await self.db.execute(
            select(GramPanchayat)
            .options(
                selectinload(GramPanchayat.block).selectinload(Block.district),
            )
            .where(GramPanchayat.id == gp_id)
        )
        gp = gp_result.scalar_one_or_none()
        if not gp:
            raise ValueError("Gram Panchayat not found")

        # Get all contractors for this GP with agency info
        contractors_result = await self.db.execute(
            select(Contractor)
            .options(selectinload(Contractor.agency))
            .where(Contractor.gp_id == gp_id)
        )
        contractors = contractors_result.scalars().all()

        has_contractor = len(contractors) > 0
        total_contract_amount = sum(c.contract_amount or 0 for c in contractors)

        contractor_summaries = [
            ContractorSummary(
                contractor_id=c.id,
                person_name=c.person_name,
                person_phone=c.person_phone,
                agency_name=c.agency.name if c.agency else None,
                contract_amount=c.contract_amount or 0,
                contract_start_date=c.contract_start_date,  # type: ignore
                contract_end_date=c.contract_end_date,  # type: ignore
                contract_frequency=c.contract_frequency.value if c.contract_frequency else None,
            )
            for c in contractors
        ]

        return ContractorGPAnalytics(
            gp_id=gp.id,
            gp_name=gp.name,
            block_id=gp.block.id,
            block_name=gp.block.name,
            district_id=gp.block.district.id,
            district_name=gp.block.district.name,
            has_contractor=has_contractor,
            contractor_data_status="Available" if has_contractor else "Not Available",
            total_contractors=len(contractors),
            total_contract_amount=round(total_contract_amount, 2),
            contractors=contractor_summaries,
        )

    # ---- Private helper methods ----

    async def _get_district_coverage(self) -> List[VillageMasterDataCoverage]:
        """Get district-wise contractor coverage using database aggregation."""

        coverage_query = (
            select(
                District.id.label("district_id"),
                District.name.label("district_name"),
                func.count(distinct(GramPanchayat.id)).label("total_gps"),  # type: ignore
                func.count(distinct(Contractor.gp_id)).label("gps_with_data"),  # type: ignore
            )
            .select_from(District)
            .join(GramPanchayat, District.id == GramPanchayat.district_id)
            .outerjoin(Contractor, Contractor.gp_id == GramPanchayat.id)
            .group_by(District.id, District.name)
        )

        result = await self.db.execute(coverage_query)
        rows = result.all()

        return [
            VillageMasterDataCoverage(
                geography_id=row.district_id,
                geography_name=row.district_name,
                total_gps=row.total_gps or 0,
                gps_with_data=row.gps_with_data or 0,
                coverage_percentage=round(
                    (row.gps_with_data / row.total_gps * 100) if row.total_gps and row.total_gps > 0 else 0.0, 2
                ),
                master_data_status="Available" if row.gps_with_data and row.gps_with_data > 0 else "Not Available",
            )
            for row in rows
        ]

    async def _get_block_coverage(self, district_id: int) -> List[VillageMasterDataCoverage]:
        """Get block-wise contractor coverage using database aggregation."""

        coverage_query = (
            select(
                Block.id.label("block_id"),
                Block.name.label("block_name"),
                func.count(distinct(GramPanchayat.id)).label("total_gps"),  # type: ignore
                func.count(distinct(Contractor.gp_id)).label("gps_with_data"),  # type: ignore
            )
            .select_from(Block)
            .join(GramPanchayat, Block.id == GramPanchayat.block_id)
            .outerjoin(Contractor, Contractor.gp_id == GramPanchayat.id)
            .where(Block.district_id == district_id)
            .group_by(Block.id, Block.name)
        )

        result = await self.db.execute(coverage_query)
        rows = result.all()

        return [
            VillageMasterDataCoverage(
                geography_id=row.block_id,
                geography_name=row.block_name,
                total_gps=row.total_gps or 0,
                gps_with_data=row.gps_with_data or 0,
                coverage_percentage=round(
                    (row.gps_with_data / row.total_gps * 100) if row.total_gps and row.total_gps > 0 else 0.0, 2
                ),
                master_data_status="Available" if row.gps_with_data and row.gps_with_data > 0 else "Not Available",
            )
            for row in rows
        ]

    async def _get_gp_coverage(self, block_id: int) -> List[VillageMasterDataCoverage]:
        """Get GP-wise contractor coverage using database aggregation."""

        coverage_query = (
            select(
                GramPanchayat.id.label("gp_id"),
                GramPanchayat.name.label("gp_name"),
                func.count(Contractor.id).label("contractor_count"),  # type: ignore
            )
            .select_from(GramPanchayat)
            .outerjoin(Contractor, Contractor.gp_id == GramPanchayat.id)
            .where(GramPanchayat.block_id == block_id)
            .group_by(GramPanchayat.id, GramPanchayat.name)
        )

        result = await self.db.execute(coverage_query)
        rows = result.all()

        return [
            VillageMasterDataCoverage(
                geography_id=row.gp_id,
                geography_name=row.gp_name,
                total_gps=1,
                gps_with_data=1 if row.contractor_count and row.contractor_count > 0 else 0,
                coverage_percentage=100.0 if row.contractor_count and row.contractor_count > 0 else 0.0,
                master_data_status="Available" if row.contractor_count and row.contractor_count > 0 else "Not Available",
            )
            for row in rows
        ]
