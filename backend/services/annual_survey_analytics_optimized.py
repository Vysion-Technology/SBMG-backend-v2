"""
Annual Survey Analytics Service (Optimized)
Handles business logic for annual survey analytics using database-level aggregations
"""

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct, and_
from sqlalchemy.orm import selectinload

from models.database.survey_master import (
    AnnualSurvey,
    VillageData,
    VillageSBMGAssets,
    VillageGWMAssets,
    SBMGYearTargets,
    WorkOrderDetails,
    FundSanctioned,
    DoorToDoorCollectionDetails,
)
from models.database.geography import District, Block, GramPanchayat
from models.response.annual_survey_analytics import (
    StateAnalytics,
    DistrictAnalytics,
    BlockAnalytics,
    GPAnalytics,
    SchemeTargetAchievement,
    VillageMasterDataCoverage,
    AnnualOverview,
)


class AnnualSurveyAnalyticsServiceOptimized:
    """Optimized service for annual survey analytics using database aggregations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_state_analytics(self, fy_id: Optional[int] = None) -> StateAnalytics:
        """Get state-level analytics for annual surveys."""

        # Build base query
        base_filter: List = []
        if fy_id:
            base_filter.append(AnnualSurvey.fy_id == fy_id)

        # Main aggregation query
        agg_query = (
            select(
                func.count(distinct(AnnualSurvey.id)).label("total_surveys"),  # type: ignore
                func.count(distinct(AnnualSurvey.gp_id)).label("gps_with_data"),  # type: ignore
                func.coalesce(func.sum(FundSanctioned.amount), 0).label("total_funds"),  # type: ignore
                func.coalesce(func.sum(WorkOrderDetails.work_order_amount), 0).label(
                    "total_work_orders"
                ),  # type: ignore
                func.coalesce(
                    func.sum(DoorToDoorCollectionDetails.num_households), 0
                ).label("total_households_d2d"),  # type: ignore
                func.count(distinct(AnnualSurvey.agency_id)).label("unique_agencies"),  # type: ignore
            )
            .select_from(AnnualSurvey)
            .outerjoin(FundSanctioned, AnnualSurvey.id == FundSanctioned.id)
            .outerjoin(WorkOrderDetails, AnnualSurvey.id == WorkOrderDetails.id)
            .outerjoin(
                DoorToDoorCollectionDetails,
                AnnualSurvey.id == DoorToDoorCollectionDetails.id,
            )
        )

        if base_filter:
            agg_query = agg_query.where(and_(*base_filter))

        result = await self.db.execute(agg_query)
        row = result.one()

        # Get total GPs
        total_gps_result = await self.db.execute(
            select(func.count()).select_from(GramPanchayat)  # type: ignore
        )
        total_gps = total_gps_result.scalar() or 0

        # Calculate coverage percentage
        gps_with_data = row.gps_with_data or 0
        coverage_percentage = (
            (gps_with_data / total_gps * 100) if total_gps > 0 else 0.0
        )

        # Convert to Crores
        total_funds_sanctioned = (row.total_funds or 0) / 10000000
        total_work_order_amount = (row.total_work_orders or 0) / 10000000

        # Get scheme-wise aggregations
        scheme_data = await self._get_scheme_aggregations(fy_id)

        # Calculate overall achievement rate
        total_target = sum(s.target for s in scheme_data)
        total_achievement = sum(s.achievement for s in scheme_data)
        sbmg_target_achievement_rate = (
            (total_achievement / total_target * 100) if total_target > 0 else 0.0
        )

        # Calculate annual overview metrics
        fund_utilization_rate = (
            (row.total_work_orders / row.total_funds * 100)
            if row.total_funds and row.total_funds > 0
            else 0.0
        )

        avg_cost_per_household = (
            (row.total_work_orders / row.total_households_d2d)
            if row.total_households_d2d and row.total_households_d2d > 0
            else None
        )

        # Get GPs with asset gaps
        gps_with_gaps = await self._count_gps_with_asset_gaps(fy_id)

        annual_overview = AnnualOverview(
            fund_utilization_rate=round(fund_utilization_rate, 2),
            average_cost_per_household_d2d=round(avg_cost_per_household, 2)
            if avg_cost_per_household
            else None,
            households_covered_d2d=row.total_households_d2d or 0,
            gps_with_asset_gaps=gps_with_gaps,
            active_sanitation_bidders=row.unique_agencies or 0,
        )

        # Get district-wise coverage
        district_wise_coverage = await self._get_district_coverage(fy_id)

        return StateAnalytics(
            total_village_master_data=row.total_surveys or 0,
            village_master_data_coverage_percentage=round(coverage_percentage, 2),
            total_funds_sanctioned=round(total_funds_sanctioned, 2),
            total_work_order_amount=round(total_work_order_amount, 2),
            sbmg_target_achievement_rate=round(sbmg_target_achievement_rate, 2),
            scheme_wise_target_achievement=scheme_data,
            annual_overview=annual_overview,
            district_wise_coverage=district_wise_coverage,
        )

    async def get_district_analytics(
        self, district_id: int, fy_id: Optional[int] = None
    ) -> DistrictAnalytics:
        """Get district-level analytics for annual surveys."""

        # Get district info
        district_result = await self.db.execute(
            select(District).where(District.id == district_id)
        )
        district = district_result.scalar_one_or_none()
        if not district:
            raise ValueError("District not found")

        # Build filters
        filters = [GramPanchayat.district_id == district_id]
        if fy_id:
            filters.append(AnnualSurvey.fy_id == fy_id)

        # Main aggregation query
        agg_query = (
            select(
                func.count(distinct(AnnualSurvey.id)).label("total_surveys"),  # type: ignore
                func.count(distinct(AnnualSurvey.gp_id)).label("gps_with_data"),  # type: ignore
                func.coalesce(func.sum(FundSanctioned.amount), 0).label("total_funds"),  # type: ignore
                func.coalesce(func.sum(WorkOrderDetails.work_order_amount), 0).label(
                    "total_work_orders"
                ),  # type: ignore
                func.coalesce(
                    func.sum(DoorToDoorCollectionDetails.num_households), 0
                ).label("total_households_d2d"),  # type: ignore
                func.count(distinct(AnnualSurvey.agency_id)).label("unique_agencies"),  # type: ignore
            )
            .select_from(AnnualSurvey)
            .join(GramPanchayat, AnnualSurvey.gp_id == GramPanchayat.id)
            .outerjoin(FundSanctioned, AnnualSurvey.id == FundSanctioned.id)
            .outerjoin(WorkOrderDetails, AnnualSurvey.id == WorkOrderDetails.id)
            .outerjoin(
                DoorToDoorCollectionDetails,
                AnnualSurvey.id == DoorToDoorCollectionDetails.id,
            )
            .where(and_(*filters))
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

        # Calculate metrics
        gps_with_data = row.gps_with_data or 0
        coverage_percentage = (
            (gps_with_data / total_gps * 100) if total_gps > 0 else 0.0
        )

        total_funds_sanctioned = (row.total_funds or 0) / 10000000
        total_work_order_amount = (row.total_work_orders or 0) / 10000000

        # Get scheme-wise aggregations
        scheme_data = await self._get_scheme_aggregations(
            fy_id, district_id=district_id
        )

        total_target = sum(s.target for s in scheme_data)
        total_achievement = sum(s.achievement for s in scheme_data)
        sbmg_target_achievement_rate = (
            (total_achievement / total_target * 100) if total_target > 0 else 0.0
        )

        # Annual overview
        fund_utilization_rate = (
            (row.total_work_orders / row.total_funds * 100)
            if row.total_funds and row.total_funds > 0
            else 0.0
        )

        avg_cost_per_household = (
            (row.total_work_orders / row.total_households_d2d)
            if row.total_households_d2d and row.total_households_d2d > 0
            else None
        )

        gps_with_gaps = await self._count_gps_with_asset_gaps(
            fy_id, district_id=district_id
        )

        annual_overview = AnnualOverview(
            fund_utilization_rate=round(fund_utilization_rate, 2),
            average_cost_per_household_d2d=round(avg_cost_per_household, 2)
            if avg_cost_per_household
            else None,
            households_covered_d2d=row.total_households_d2d or 0,
            gps_with_asset_gaps=gps_with_gaps,
            active_sanitation_bidders=row.unique_agencies or 0,
        )

        # Block-wise coverage
        block_wise_coverage = await self._get_block_coverage(district_id, fy_id)

        return DistrictAnalytics(
            district_id=district.id,
            district_name=district.name,
            total_village_master_data=row.total_surveys or 0,
            village_master_data_coverage_percentage=round(coverage_percentage, 2),
            total_funds_sanctioned=round(total_funds_sanctioned, 2),
            total_work_order_amount=round(total_work_order_amount, 2),
            sbmg_target_achievement_rate=round(sbmg_target_achievement_rate, 2),
            scheme_wise_target_achievement=scheme_data,
            annual_overview=annual_overview,
            block_wise_coverage=block_wise_coverage,
        )

    async def get_block_analytics(
        self, block_id: int, fy_id: Optional[int] = None
    ) -> BlockAnalytics:
        """Get block-level analytics for annual surveys."""

        # Get block info
        block_result = await self.db.execute(
            select(Block)
            .options(selectinload(Block.district))
            .where(Block.id == block_id)
        )
        block = block_result.scalar_one_or_none()
        if not block:
            raise ValueError("Block not found")

        # Build filters
        filters = [GramPanchayat.block_id == block_id]
        if fy_id:
            filters.append(AnnualSurvey.fy_id == fy_id)

        # Main aggregation query
        agg_query = (
            select(
                func.count(distinct(AnnualSurvey.id)).label("total_surveys"),  # type: ignore
                func.count(distinct(AnnualSurvey.gp_id)).label("gps_with_data"),  # type: ignore
                func.coalesce(func.sum(FundSanctioned.amount), 0).label("total_funds"),  # type: ignore
                func.coalesce(func.sum(WorkOrderDetails.work_order_amount), 0).label(
                    "total_work_orders"
                ),  # type: ignore
                func.coalesce(
                    func.sum(DoorToDoorCollectionDetails.num_households), 0
                ).label("total_households_d2d"),  # type: ignore
                func.count(distinct(AnnualSurvey.agency_id)).label("unique_agencies"),  # type: ignore
            )
            .select_from(AnnualSurvey)
            .join(GramPanchayat, AnnualSurvey.gp_id == GramPanchayat.id)
            .outerjoin(FundSanctioned, AnnualSurvey.id == FundSanctioned.id)
            .outerjoin(WorkOrderDetails, AnnualSurvey.id == WorkOrderDetails.id)
            .outerjoin(
                DoorToDoorCollectionDetails,
                AnnualSurvey.id == DoorToDoorCollectionDetails.id,
            )
            .where(and_(*filters))
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

        # Calculate metrics
        gps_with_data = row.gps_with_data or 0
        coverage_percentage = (
            (gps_with_data / total_gps * 100) if total_gps > 0 else 0.0
        )

        total_funds_sanctioned = (row.total_funds or 0) / 10000000
        total_work_order_amount = (row.total_work_orders or 0) / 10000000

        # Get scheme-wise aggregations
        scheme_data = await self._get_scheme_aggregations(fy_id, block_id=block_id)

        total_target = sum(s.target for s in scheme_data)
        total_achievement = sum(s.achievement for s in scheme_data)
        sbmg_target_achievement_rate = (
            (total_achievement / total_target * 100) if total_target > 0 else 0.0
        )

        # Annual overview
        fund_utilization_rate = (
            (row.total_work_orders / row.total_funds * 100)
            if row.total_funds and row.total_funds > 0
            else 0.0
        )

        avg_cost_per_household = (
            (row.total_work_orders / row.total_households_d2d)
            if row.total_households_d2d and row.total_households_d2d > 0
            else None
        )

        gps_with_gaps = await self._count_gps_with_asset_gaps(fy_id, block_id=block_id)

        annual_overview = AnnualOverview(
            fund_utilization_rate=round(fund_utilization_rate, 2),
            average_cost_per_household_d2d=round(avg_cost_per_household, 2)
            if avg_cost_per_household
            else None,
            households_covered_d2d=row.total_households_d2d or 0,
            gps_with_asset_gaps=gps_with_gaps,
            active_sanitation_bidders=row.unique_agencies or 0,
        )

        # GP-wise coverage
        gp_wise_coverage = await self._get_gp_coverage(block_id, fy_id)

        return BlockAnalytics(
            block_id=block.id,
            block_name=block.name,
            district_id=block.district.id,
            district_name=block.district.name,
            total_village_master_data=row.total_surveys or 0,
            village_master_data_coverage_percentage=round(coverage_percentage, 2),
            total_funds_sanctioned=round(total_funds_sanctioned, 2),
            total_work_order_amount=round(total_work_order_amount, 2),
            sbmg_target_achievement_rate=round(sbmg_target_achievement_rate, 2),
            scheme_wise_target_achievement=scheme_data,
            annual_overview=annual_overview,
            gp_wise_coverage=gp_wise_coverage,
        )

    async def get_gp_analytics(
        self, gp_id: int, fy_id: Optional[int] = None
    ) -> GPAnalytics:
        """Get GP-level analytics for annual surveys."""

        # Get GP info
        gp_result = await self.db.execute(
            select(GramPanchayat)
            .options(
                selectinload(GramPanchayat.block), selectinload(GramPanchayat.district)
            )
            .where(GramPanchayat.id == gp_id)
        )
        gp = gp_result.scalar_one_or_none()
        if not gp:
            raise ValueError("Gram Panchayat not found")

        # Build query for latest survey
        query = select(AnnualSurvey).where(AnnualSurvey.gp_id == gp_id)
        if fy_id:
            query = query.where(AnnualSurvey.fy_id == fy_id)

        result = await self.db.execute(
            query.options(
                selectinload(AnnualSurvey.fund_sanctioned),
                selectinload(AnnualSurvey.work_order),
                selectinload(AnnualSurvey.door_to_door_collection),
                selectinload(AnnualSurvey.agency),
            ).order_by(AnnualSurvey.survey_date.desc())
        )
        survey = result.scalars().first()

        has_master_data = survey is not None

        # Initialize response
        response_data = {
            "gp_id": gp.id,
            "gp_name": gp.name,
            "block_id": gp.block.id,
            "block_name": gp.block.name,
            "district_id": gp.district.id,
            "district_name": gp.district.name,
            "has_master_data": has_master_data,
            "master_data_available": "Available"
            if has_master_data
            else "Not Available",
        }

        if survey:
            # Get scheme-wise data for this GP
            scheme_data = await self._get_scheme_aggregations(fy_id, gp_id=gp_id)

            # Get village count
            village_count_result = await self.db.execute(
                select(func.count())
                .select_from(VillageData)
                .where(  # type: ignore
                    VillageData.survey_id == survey.id
                )
            )
            village_count = village_count_result.scalar() or 0

            # Calculate utilization rate (with division by zero protection)
            fund_amount = survey.fund_sanctioned.amount if survey.fund_sanctioned else 0
            work_order_amount = (
                survey.work_order.work_order_amount if survey.work_order else 0
            )
            fund_utilization_rate = (
                (work_order_amount / fund_amount * 100) if fund_amount > 0 else None
            )

            response_data.update(
                {
                    "survey_id": survey.id,
                    "survey_date": survey.survey_date.isoformat(),
                    "total_funds_sanctioned": fund_amount / 10000000,
                    "total_work_order_amount": work_order_amount / 10000000,
                    "scheme_wise_target_achievement": scheme_data,
                    "fund_utilization_rate": round(fund_utilization_rate, 2)
                    if fund_utilization_rate
                    else None,
                    "households_covered_d2d": (
                        survey.door_to_door_collection.num_households
                        if survey.door_to_door_collection
                        else None
                    ),
                    "num_villages": village_count,
                    "active_agency_name": survey.agency.name if survey.agency else None,
                }
            )
        else:
            response_data["scheme_wise_target_achievement"] = []

        return GPAnalytics(**response_data)

    async def _get_scheme_aggregations(
        self,
        fy_id: Optional[int] = None,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        gp_id: Optional[int] = None,
    ) -> List[SchemeTargetAchievement]:
        """Get scheme-wise target and achievement aggregations using database queries."""

        # Build base filters
        filters = []
        if fy_id:
            filters.append(AnnualSurvey.fy_id == fy_id)
        if district_id:
            filters.append(GramPanchayat.district_id == district_id)
        if block_id:
            filters.append(GramPanchayat.block_id == block_id)
        if gp_id:
            filters.append(AnnualSurvey.gp_id == gp_id)

        # Query for targets
        targets_query = (
            select(
                func.coalesce(func.sum(SBMGYearTargets.ihhl), 0).label("ihhl_target"),  # type: ignore
                func.coalesce(func.sum(SBMGYearTargets.csc), 0).label("csc_target"),  # type: ignore
                func.coalesce(func.sum(SBMGYearTargets.rrc), 0).label("rrc_target"),  # type: ignore
                func.coalesce(func.sum(SBMGYearTargets.pwmu), 0).label("pwmu_target"),  # type: ignore
                func.coalesce(func.sum(SBMGYearTargets.soak_pit), 0).label(
                    "soak_pit_target"
                ),  # type: ignore
                func.coalesce(func.sum(SBMGYearTargets.magic_pit), 0).label(
                    "magic_pit_target"
                ),  # type: ignore
                func.coalesce(func.sum(SBMGYearTargets.leach_pit), 0).label(
                    "leach_pit_target"
                ),  # type: ignore
                func.coalesce(func.sum(SBMGYearTargets.wsp), 0).label("wsp_target"),  # type: ignore
                func.coalesce(func.sum(SBMGYearTargets.dewats), 0).label(
                    "dewats_target"
                ),  # type: ignore
            )
            .select_from(AnnualSurvey)
            .join(GramPanchayat, AnnualSurvey.gp_id == GramPanchayat.id)
            .outerjoin(SBMGYearTargets, AnnualSurvey.id == SBMGYearTargets.id)
        )

        if filters:
            targets_query = targets_query.where(and_(*filters))

        targets_result = await self.db.execute(targets_query)
        targets_row = targets_result.one()

        # Query for achievements (from village data)
        achievements_query = (
            select(
                func.coalesce(func.sum(VillageSBMGAssets.ihhl), 0).label(
                    "ihhl_achievement"
                ),  # type: ignore
                func.coalesce(func.sum(VillageSBMGAssets.csc), 0).label(
                    "csc_achievement"
                ),  # type: ignore
                func.coalesce(func.sum(VillageGWMAssets.soak_pit), 0).label(
                    "soak_pit_achievement"
                ),  # type: ignore
                func.coalesce(func.sum(VillageGWMAssets.magic_pit), 0).label(
                    "magic_pit_achievement"
                ),  # type: ignore
                func.coalesce(func.sum(VillageGWMAssets.leach_pit), 0).label(
                    "leach_pit_achievement"
                ),  # type: ignore
                func.coalesce(func.sum(VillageGWMAssets.wsp), 0).label(
                    "wsp_achievement"
                ),  # type: ignore
                func.coalesce(func.sum(VillageGWMAssets.dewats), 0).label(
                    "dewats_achievement"
                ),  # type: ignore
            )
            .select_from(AnnualSurvey)
            .join(GramPanchayat, AnnualSurvey.gp_id == GramPanchayat.id)
            .join(VillageData, AnnualSurvey.id == VillageData.id)
            .outerjoin(VillageSBMGAssets, VillageData.id == VillageSBMGAssets.id)
            .outerjoin(VillageGWMAssets, VillageData.id == VillageGWMAssets.id)
        )

        if filters:
            achievements_query = achievements_query.where(and_(*filters))

        achievements_result = await self.db.execute(achievements_query)
        achievements_row = achievements_result.one()

        # Build scheme data with division by zero protection
        schemes = [
            (
                "IHHL",
                "IHHL",
                targets_row.ihhl_target,
                achievements_row.ihhl_achievement,
            ),
            ("CSC", "CSC", targets_row.csc_target, achievements_row.csc_achievement),
            ("RRC", "RRC", targets_row.rrc_target, 0),  # No achievement data for RRC
            (
                "PWMU",
                "PWMU",
                targets_row.pwmu_target,
                0,
            ),  # No achievement data for PWMU
            (
                "Soak_pit",
                "Soak pit",
                targets_row.soak_pit_target,
                achievements_row.soak_pit_achievement,
            ),
            (
                "Magic_pit",
                "Magic pit",
                targets_row.magic_pit_target,
                achievements_row.magic_pit_achievement,
            ),
            (
                "Leach_pit",
                "Leach pit",
                targets_row.leach_pit_target,
                achievements_row.leach_pit_achievement,
            ),
            ("WSP", "WSP", targets_row.wsp_target, achievements_row.wsp_achievement),
            (
                "DEWATS",
                "DEWATS",
                targets_row.dewats_target,
                achievements_row.dewats_achievement,
            ),
        ]

        return [
            SchemeTargetAchievement(
                scheme_code=code,
                scheme_name=name,
                target=target or 0,
                achievement=achievement or 0,
                achievement_percentage=(
                    (achievement / target * 100) if target and target > 0 else 0.0
                ),
            )
            for code, name, target, achievement in schemes
        ]

    async def _count_gps_with_asset_gaps(
        self,
        fy_id: Optional[int] = None,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
    ) -> int:
        """Count GPs where targets exceed achievements using database aggregation."""

        # Build filters
        filters = []
        if fy_id:
            filters.append(AnnualSurvey.fy_id == fy_id)
        if district_id:
            filters.append(GramPanchayat.district_id == district_id)
        if block_id:
            filters.append(GramPanchayat.block_id == block_id)

        # Subquery for total targets per survey
        targets_subq = (
            select(
                AnnualSurvey.id.label("survey_id"),  # type: ignore
                (
                    func.coalesce(SBMGYearTargets.ihhl, 0)
                    + func.coalesce(SBMGYearTargets.csc, 0)
                    + func.coalesce(SBMGYearTargets.rrc, 0)
                    + func.coalesce(SBMGYearTargets.pwmu, 0)
                    + func.coalesce(SBMGYearTargets.soak_pit, 0)
                    + func.coalesce(SBMGYearTargets.magic_pit, 0)
                    + func.coalesce(SBMGYearTargets.leach_pit, 0)
                    + func.coalesce(SBMGYearTargets.wsp, 0)
                    + func.coalesce(SBMGYearTargets.dewats, 0)
                ).label("total_target"),
            )
            .select_from(AnnualSurvey)
            .join(GramPanchayat, AnnualSurvey.gp_id == GramPanchayat.id)
            .outerjoin(SBMGYearTargets, AnnualSurvey.id == SBMGYearTargets.id)
        )

        if filters:
            targets_subq = targets_subq.where(and_(*filters))

        targets_subq = targets_subq.subquery()

        # Subquery for total achievements per survey
        achievements_subq = (
            select(
                VillageData.id.label("village_id"),  # type: ignore
                func.sum(  # type: ignore
                    func.coalesce(VillageSBMGAssets.ihhl, 0)
                    + func.coalesce(VillageSBMGAssets.csc, 0)
                    + func.coalesce(VillageGWMAssets.soak_pit, 0)
                    + func.coalesce(VillageGWMAssets.magic_pit, 0)
                    + func.coalesce(VillageGWMAssets.leach_pit, 0)
                    + func.coalesce(VillageGWMAssets.wsp, 0)
                    + func.coalesce(VillageGWMAssets.dewats, 0)
                ).label("total_achievement"),
            )
            .select_from(VillageData)
            .outerjoin(VillageSBMGAssets, VillageData.id == VillageSBMGAssets.id)
            .outerjoin(VillageGWMAssets, VillageData.id == VillageGWMAssets.id)
            .group_by(VillageData.id)
            .subquery()
        )

        # Count surveys where target > achievement
        count_query = (
            select(
                func.count().label("gap_count")  # type: ignore
            )
            .select_from(targets_subq)
            .outerjoin(
                achievements_subq,
                targets_subq.c.survey_id == achievements_subq.c.village_id,
            )
            .where(
                targets_subq.c.total_target
                > func.coalesce(achievements_subq.c.total_achievement, 0)
            )
        )

        result = await self.db.execute(count_query)
        return result.scalar() or 0

    async def _get_district_coverage(
        self, fy_id: Optional[int] = None
    ) -> List[VillageMasterDataCoverage]:
        """Get district-wise coverage using database aggregation."""

        # Subquery for GPs with surveys
        filters = []
        if fy_id:
            filters.append(AnnualSurvey.fy_id == fy_id)

        coverage_query = (
            select(
                District.id.label("district_id"),
                District.name.label("district_name"),
                func.count(distinct(GramPanchayat.id)).label("total_gps"),  # type: ignore
                func.count(distinct(AnnualSurvey.gp_id)).label("gps_with_data"),  # type: ignore
            )
            .select_from(District)
            .join(GramPanchayat, District.id == GramPanchayat.district_id)
            .outerjoin(
                AnnualSurvey,
                and_(AnnualSurvey.gp_id == GramPanchayat.id, *filters)
                if filters
                else AnnualSurvey.gp_id == GramPanchayat.id,
            )
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
                    (row.gps_with_data / row.total_gps * 100)
                    if row.total_gps and row.total_gps > 0
                    else 0.0,
                    2,
                ),
                master_data_status="Available"
                if row.gps_with_data and row.gps_with_data > 0
                else "Not Available",
            )
            for row in rows
        ]

    async def _get_block_coverage(
        self, district_id: int, fy_id: Optional[int] = None
    ) -> List[VillageMasterDataCoverage]:
        """Get block-wise coverage using database aggregation."""

        filters = [Block.district_id == district_id]
        fy_filter = [AnnualSurvey.fy_id == fy_id] if fy_id else []

        coverage_query = (
            select(
                Block.id.label("block_id"),
                Block.name.label("block_name"),
                func.count(distinct(GramPanchayat.id)).label("total_gps"),  # type: ignore
                func.count(distinct(AnnualSurvey.gp_id)).label("gps_with_data"),  # type: ignore
            )
            .select_from(Block)
            .join(GramPanchayat, Block.id == GramPanchayat.block_id)
            .outerjoin(
                AnnualSurvey, and_(AnnualSurvey.gp_id == GramPanchayat.id, *fy_filter)
            )
            .where(and_(*filters))
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
                    (row.gps_with_data / row.total_gps * 100)
                    if row.total_gps and row.total_gps > 0
                    else 0.0,
                    2,
                ),
                master_data_status="Available"
                if row.gps_with_data and row.gps_with_data > 0
                else "Not Available",
            )
            for row in rows
        ]

    async def _get_gp_coverage(
        self, block_id: int, fy_id: Optional[int] = None
    ) -> List[VillageMasterDataCoverage]:
        """Get GP-wise coverage using database aggregation."""

        filters = [GramPanchayat.block_id == block_id]
        fy_filter = [AnnualSurvey.fy_id == fy_id] if fy_id else []

        coverage_query = (
            select(
                GramPanchayat.id.label("gp_id"),
                GramPanchayat.name.label("gp_name"),
                func.count(distinct(AnnualSurvey.id)).label("survey_count"),  # type: ignore
            )
            .select_from(GramPanchayat)
            .outerjoin(
                AnnualSurvey, and_(AnnualSurvey.gp_id == GramPanchayat.id, *fy_filter)
            )
            .where(and_(*filters))
            .group_by(GramPanchayat.id, GramPanchayat.name)
        )

        result = await self.db.execute(coverage_query)
        rows = result.all()

        return [
            VillageMasterDataCoverage(
                geography_id=row.gp_id,
                geography_name=row.gp_name,
                total_gps=1,
                gps_with_data=1 if row.survey_count and row.survey_count > 0 else 0,
                coverage_percentage=100.0
                if row.survey_count and row.survey_count > 0
                else 0.0,
                master_data_status="Available"
                if row.survey_count and row.survey_count > 0
                else "Not Available",
            )
            for row in rows
        ]
