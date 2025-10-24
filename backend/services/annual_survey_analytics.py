"""
Annual Survey Analytics Service
Handles business logic for annual survey analytics and reporting
"""

from typing import List, Optional, TypedDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct
from sqlalchemy.orm import selectinload

from models.database.survey_master import (
    AnnualSurvey,
    VillageData,
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


class SchemeData(TypedDict):
    """Type definition for scheme data."""

    name: str
    target: int
    achievement: int


class AnnualSurveyAnalyticsService:
    """Service for annual survey analytics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_state_analytics(self, fy_id: Optional[int] = None) -> StateAnalytics:
        """Get state-level analytics for annual surveys."""

        # Build base query
        query = select(AnnualSurvey)
        if fy_id:
            query = query.where(AnnualSurvey.fy_id == fy_id)

        # Get all surveys with related data
        result = await self.db.execute(
            query.options(
                selectinload(AnnualSurvey.fund_sanctioned),
                selectinload(AnnualSurvey.work_order),
                selectinload(AnnualSurvey.door_to_door_collection),
                selectinload(AnnualSurvey.sbmg_targets),
                selectinload(AnnualSurvey.village_data).selectinload(VillageData.sbmg_assets),
                selectinload(AnnualSurvey.village_data).selectinload(VillageData.gwm_assets),
                selectinload(AnnualSurvey.gp).selectinload(GramPanchayat.district),
                selectinload(AnnualSurvey.agency),
            )
        )
        surveys = result.scalars().all()

        # Get total GPs count
        total_gps_result = await self.db.execute(select(func.count()).select_from(GramPanchayat))  # type: ignore
        total_gps = total_gps_result.scalar() or 0

        # Calculate metrics
        total_surveys = len(surveys)
        gps_with_data = len(set(s.gp_id for s in surveys))
        coverage_percentage = (gps_with_data / total_gps * 100) if total_gps > 0 else 0.0

        # Calculate financial metrics (in Crores)
        total_funds_sanctioned = (
            sum(s.fund_sanctioned.amount or 0 for s in surveys if s.fund_sanctioned) / 10000000
        )  # Convert to Crores

        total_work_order_amount = (
            sum(s.work_order.work_order_amount or 0 for s in surveys if s.work_order) / 10000000
        )  # Convert to Crores

        # Calculate scheme-wise target and achievement
        scheme_data = self._calculate_scheme_aggregates(list(surveys))

        # Calculate overall achievement rate
        total_target = sum(s["target"] for s in scheme_data.values())
        total_achievement = sum(s["achievement"] for s in scheme_data.values())
        sbmg_target_achievement_rate = (total_achievement / total_target * 100) if total_target > 0 else 0.0

        # Build scheme-wise target achievement list
        scheme_wise_target_achievement = [
            SchemeTargetAchievement(
                scheme_code=code,
                scheme_name=data["name"],
                target=data["target"],
                achievement=data["achievement"],
                achievement_percentage=(data["achievement"] / data["target"] * 100) if data["target"] > 0 else 0.0,
            )
            for code, data in scheme_data.items()
        ]

        # Calculate annual overview
        annual_overview = self._calculate_annual_overview(list(surveys))

        # Calculate district-wise coverage
        district_wise_coverage = await self._get_district_coverage(fy_id)

        return StateAnalytics(
            total_village_master_data=total_surveys,
            village_master_data_coverage_percentage=round(coverage_percentage, 2),
            total_funds_sanctioned=round(total_funds_sanctioned, 2),
            total_work_order_amount=round(total_work_order_amount, 2),
            sbmg_target_achievement_rate=round(sbmg_target_achievement_rate, 2),
            scheme_wise_target_achievement=scheme_wise_target_achievement,
            annual_overview=annual_overview,
            district_wise_coverage=district_wise_coverage,
        )

    async def get_district_analytics(self, district_id: int, fy_id: Optional[int] = None) -> DistrictAnalytics:
        """Get district-level analytics for annual surveys."""

        # Get district info
        district_result = await self.db.execute(select(District).where(District.id == district_id))
        district = district_result.scalar_one_or_none()
        if not district:
            raise ValueError("District not found")

        # Build query for surveys in this district
        query = (
            select(AnnualSurvey)
            .join(GramPanchayat, AnnualSurvey.gp_id == GramPanchayat.id)
            .where(GramPanchayat.district_id == district_id)
        )

        if fy_id:
            query = query.where(AnnualSurvey.fy_id == fy_id)

        result = await self.db.execute(
            query.options(
                selectinload(AnnualSurvey.fund_sanctioned),
                selectinload(AnnualSurvey.work_order),
                selectinload(AnnualSurvey.door_to_door_collection),
                selectinload(AnnualSurvey.sbmg_targets),
                selectinload(AnnualSurvey.village_data).selectinload(VillageData.sbmg_assets),
                selectinload(AnnualSurvey.village_data).selectinload(VillageData.gwm_assets),
                selectinload(AnnualSurvey.gp).selectinload(GramPanchayat.block),
                selectinload(AnnualSurvey.agency),
            )
        )
        surveys = result.scalars().all()

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
        total_surveys = len(surveys)
        gps_with_data = len(set(s.gp_id for s in surveys))
        coverage_percentage = (gps_with_data / total_gps * 100) if total_gps > 0 else 0.0

        # Financial metrics
        total_funds_sanctioned = sum(s.fund_sanctioned.amount or 0 for s in surveys if s.fund_sanctioned) / 10000000

        total_work_order_amount = sum(s.work_order.work_order_amount or 0 for s in surveys if s.work_order) / 10000000

        # Scheme-wise calculations
        scheme_data = self._calculate_scheme_aggregates(list(surveys))
        total_target = sum(s["target"] for s in scheme_data.values())
        total_achievement = sum(s["achievement"] for s in scheme_data.values())
        sbmg_target_achievement_rate = (total_achievement / total_target * 100) if total_target > 0 else 0.0

        scheme_wise_target_achievement = [
            SchemeTargetAchievement(
                scheme_code=code,
                scheme_name=data["name"],
                target=data["target"],
                achievement=data["achievement"],
                achievement_percentage=(data["achievement"] / data["target"] * 100) if data["target"] > 0 else 0.0,
            )
            for code, data in scheme_data.items()
        ]

        # Annual overview
        annual_overview = self._calculate_annual_overview(list(surveys))

        # Block-wise coverage
        block_wise_coverage = await self._get_block_coverage(district_id, fy_id)

        return DistrictAnalytics(
            district_id=district.id,
            district_name=district.name,
            total_village_master_data=total_surveys,
            village_master_data_coverage_percentage=round(coverage_percentage, 2),
            total_funds_sanctioned=round(total_funds_sanctioned, 2),
            total_work_order_amount=round(total_work_order_amount, 2),
            sbmg_target_achievement_rate=round(sbmg_target_achievement_rate, 2),
            scheme_wise_target_achievement=scheme_wise_target_achievement,
            annual_overview=annual_overview,
            block_wise_coverage=block_wise_coverage,
        )

    async def get_block_analytics(self, block_id: int, fy_id: Optional[int] = None) -> BlockAnalytics:
        """Get block-level analytics for annual surveys."""

        # Get block info
        block_result = await self.db.execute(
            select(Block).options(selectinload(Block.district)).where(Block.id == block_id)
        )
        block = block_result.scalar_one_or_none()
        if not block:
            raise ValueError("Block not found")

        # Build query for surveys in this block
        query = (
            select(AnnualSurvey)
            .join(GramPanchayat, AnnualSurvey.gp_id == GramPanchayat.id)
            .where(GramPanchayat.block_id == block_id)
        )

        if fy_id:
            query = query.where(AnnualSurvey.fy_id == fy_id)

        result = await self.db.execute(
            query.options(
                selectinload(AnnualSurvey.fund_sanctioned),
                selectinload(AnnualSurvey.work_order),
                selectinload(AnnualSurvey.door_to_door_collection),
                selectinload(AnnualSurvey.sbmg_targets),
                selectinload(AnnualSurvey.village_data).selectinload(VillageData.sbmg_assets),
                selectinload(AnnualSurvey.village_data).selectinload(VillageData.gwm_assets),
                selectinload(AnnualSurvey.gp),
                selectinload(AnnualSurvey.agency),
            )
        )
        surveys = result.scalars().all()

        # Get total GPs in block
        total_gps_result = await self.db.execute(
            select(func.count()).select_from(GramPanchayat).where(GramPanchayat.block_id == block_id)  # type: ignore
        )
        total_gps = total_gps_result.scalar() or 0

        # Calculate metrics
        total_surveys = len(surveys)
        gps_with_data = len(set(s.gp_id for s in surveys))
        coverage_percentage = (gps_with_data / total_gps * 100) if total_gps > 0 else 0.0

        # Financial metrics
        total_funds_sanctioned = sum(s.fund_sanctioned.amount or 0 for s in surveys if s.fund_sanctioned) / 10000000

        total_work_order_amount = sum(s.work_order.work_order_amount or 0 for s in surveys if s.work_order) / 10000000

        # Scheme-wise calculations
        scheme_data = self._calculate_scheme_aggregates(list(surveys))
        total_target = sum(s["target"] for s in scheme_data.values())
        total_achievement = sum(s["achievement"] for s in scheme_data.values())
        sbmg_target_achievement_rate = (total_achievement / total_target * 100) if total_target > 0 else 0.0

        scheme_wise_target_achievement = [
            SchemeTargetAchievement(
                scheme_code=code,
                scheme_name=data["name"],
                target=data["target"],
                achievement=data["achievement"],
                achievement_percentage=(data["achievement"] / data["target"] * 100) if data["target"] > 0 else 0.0,
            )
            for code, data in scheme_data.items()
        ]

        # Annual overview
        annual_overview = self._calculate_annual_overview(list(surveys))

        # GP-wise coverage
        gp_wise_coverage = await self._get_gp_coverage(block_id, fy_id)

        return BlockAnalytics(
            block_id=block.id,
            block_name=block.name,
            district_id=block.district.id,
            district_name=block.district.name,
            total_village_master_data=total_surveys,
            village_master_data_coverage_percentage=round(coverage_percentage, 2),
            total_funds_sanctioned=round(total_funds_sanctioned, 2),
            total_work_order_amount=round(total_work_order_amount, 2),
            sbmg_target_achievement_rate=round(sbmg_target_achievement_rate, 2),
            scheme_wise_target_achievement=scheme_wise_target_achievement,
            annual_overview=annual_overview,
            gp_wise_coverage=gp_wise_coverage,
        )

    async def get_gp_analytics(self, gp_id: int, fy_id: Optional[int] = None) -> GPAnalytics:
        """Get GP-level analytics for annual surveys."""

        # Get GP info
        gp_result = await self.db.execute(
            select(GramPanchayat)
            .options(selectinload(GramPanchayat.block), selectinload(GramPanchayat.district))
            .where(GramPanchayat.id == gp_id)
        )
        gp = gp_result.scalar_one_or_none()
        if not gp:
            raise ValueError("Gram Panchayat not found")

        # Get survey for this GP
        query = select(AnnualSurvey).where(AnnualSurvey.gp_id == gp_id)
        if fy_id:
            query = query.where(AnnualSurvey.fy_id == fy_id)

        result = await self.db.execute(
            query.options(
                selectinload(AnnualSurvey.fund_sanctioned),
                selectinload(AnnualSurvey.work_order),
                selectinload(AnnualSurvey.door_to_door_collection),
                selectinload(AnnualSurvey.sbmg_targets),
                selectinload(AnnualSurvey.village_data).selectinload(VillageData.sbmg_assets),
                selectinload(AnnualSurvey.village_data).selectinload(VillageData.gwm_assets),
                selectinload(AnnualSurvey.agency),
            ).order_by(AnnualSurvey.survey_date.desc())
        )
        survey = result.scalars().first()

        has_master_data = survey is not None
        master_data_available = "Available" if has_master_data else "Not Available"

        # Initialize response
        response_data = {
            "gp_id": gp.id,
            "gp_name": gp.name,
            "block_id": gp.block.id,
            "block_name": gp.block.name,
            "district_id": gp.district.id,
            "district_name": gp.district.name,
            "has_master_data": has_master_data,
            "master_data_available": master_data_available,
        }

        if survey:
            # Calculate scheme-wise data
            scheme_data = self._calculate_scheme_aggregates([survey])
            scheme_wise_target_achievement = [
                SchemeTargetAchievement(
                    scheme_code=code,
                    scheme_name=data["name"],
                    target=data["target"],
                    achievement=data["achievement"],
                    achievement_percentage=(data["achievement"] / data["target"] * 100) if data["target"] > 0 else 0.0,
                )
                for code, data in scheme_data.items()
            ]

            # Calculate utilization rate
            fund_amount = survey.fund_sanctioned.amount if survey.fund_sanctioned else 0
            work_order_amount = survey.work_order.work_order_amount if survey.work_order else 0
            fund_utilization_rate = (work_order_amount / fund_amount * 100) if fund_amount > 0 else None

            response_data.update({
                "survey_id": survey.id,
                "survey_date": survey.survey_date.isoformat(),
                "total_funds_sanctioned": fund_amount / 10000000,  # In Crores
                "total_work_order_amount": work_order_amount / 10000000,  # In Crores
                "scheme_wise_target_achievement": scheme_wise_target_achievement,
                "fund_utilization_rate": round(fund_utilization_rate, 2) if fund_utilization_rate else None,
                "households_covered_d2d": (
                    survey.door_to_door_collection.num_households if survey.door_to_door_collection else None
                ),
                "num_villages": len(survey.village_data),
                "active_agency_name": survey.agency.name if survey.agency else None,
            })
        else:
            response_data["scheme_wise_target_achievement"] = []

        return GPAnalytics(**response_data)

    def _calculate_scheme_aggregates(self, surveys: List[AnnualSurvey]) -> dict[str, SchemeData]:
        """Calculate aggregated scheme targets and achievements."""

        scheme_map: dict[str, SchemeData] = {
            "IHHL": SchemeData(name="IHHL", target=0, achievement=0),
            "CSC": SchemeData(name="CSC", target=0, achievement=0),
            "RRC": SchemeData(name="RRC", target=0, achievement=0),
            "PWMU": SchemeData(name="PWMU", target=0, achievement=0),
            "Soak_pit": SchemeData(name="Soak pit", target=0, achievement=0),
            "Magic_pit": SchemeData(name="Magic pit", target=0, achievement=0),
            "Leach_pit": SchemeData(name="Leach pit", target=0, achievement=0),
            "WSP": SchemeData(name="WSP", target=0, achievement=0),
            "DEWATS": SchemeData(name="DEWATS", target=0, achievement=0),
        }

        for survey in surveys:
            if survey.sbmg_targets:
                targets = survey.sbmg_targets
                scheme_map["IHHL"]["target"] += targets.ihhl or 0
                scheme_map["CSC"]["target"] += targets.csc or 0
                scheme_map["RRC"]["target"] += targets.rrc or 0
                scheme_map["PWMU"]["target"] += targets.pwmu or 0
                scheme_map["Soak_pit"]["target"] += targets.soak_pit or 0
                scheme_map["Magic_pit"]["target"] += targets.magic_pit or 0
                scheme_map["Leach_pit"]["target"] += targets.leach_pit or 0
                scheme_map["WSP"]["target"] += targets.wsp or 0
                scheme_map["DEWATS"]["target"] += targets.dewats or 0

            # Aggregate achievements from village data
            for village_data in survey.village_data:
                if village_data.sbmg_assets:
                    assets = village_data.sbmg_assets
                    scheme_map["IHHL"]["achievement"] += assets.ihhl or 0
                    scheme_map["CSC"]["achievement"] += assets.csc or 0

                if village_data.gwm_assets:
                    gwm = village_data.gwm_assets
                    scheme_map["Soak_pit"]["achievement"] += gwm.soak_pit or 0
                    scheme_map["Magic_pit"]["achievement"] += gwm.magic_pit or 0
                    scheme_map["Leach_pit"]["achievement"] += gwm.leach_pit or 0
                    scheme_map["WSP"]["achievement"] += gwm.wsp or 0
                    scheme_map["DEWATS"]["achievement"] += gwm.dewats or 0

        return scheme_map

    def _calculate_annual_overview(self, surveys: List[AnnualSurvey]) -> AnnualOverview:
        """Calculate annual overview metrics."""

        total_funds = sum(s.fund_sanctioned.amount or 0 for s in surveys if s.fund_sanctioned)
        total_work_orders = sum(s.work_order.work_order_amount or 0 for s in surveys if s.work_order)

        fund_utilization_rate = (total_work_orders / total_funds * 100) if total_funds > 0 else 0.0

        # Calculate D2D metrics
        total_households_d2d = sum(
            s.door_to_door_collection.num_households or 0 for s in surveys if s.door_to_door_collection
        )

        # Average cost per household (work order amount / households)
        avg_cost_per_household = (total_work_orders / total_households_d2d) if total_households_d2d > 0 else None

        # GPs with asset gaps (where targets > achievements)
        gps_with_gaps = 0
        for survey in surveys:
            if survey.sbmg_targets:
                targets = survey.sbmg_targets
                total_target = sum([
                    targets.ihhl or 0,
                    targets.csc or 0,
                    targets.rrc or 0,
                    targets.pwmu or 0,
                    targets.soak_pit or 0,
                    targets.magic_pit or 0,
                    targets.leach_pit or 0,
                    targets.wsp or 0,
                    targets.dewats or 0,
                ])

                total_achievement = 0
                for vd in survey.village_data:
                    if vd.sbmg_assets:
                        total_achievement += (vd.sbmg_assets.ihhl or 0) + (vd.sbmg_assets.csc or 0)
                    if vd.gwm_assets:
                        total_achievement += sum([
                            vd.gwm_assets.soak_pit or 0,
                            vd.gwm_assets.magic_pit or 0,
                            vd.gwm_assets.leach_pit or 0,
                            vd.gwm_assets.wsp or 0,
                            vd.gwm_assets.dewats or 0,
                        ])

                if total_target > total_achievement:
                    gps_with_gaps += 1

        # Unique agencies
        unique_agencies = len(set(s.agency_id for s in surveys if s.agency_id))

        return AnnualOverview(
            fund_utilization_rate=round(fund_utilization_rate, 2),
            average_cost_per_household_d2d=round(avg_cost_per_household, 2) if avg_cost_per_household else None,
            households_covered_d2d=total_households_d2d,
            gps_with_asset_gaps=gps_with_gaps,
            active_sanitation_bidders=unique_agencies,
        )

    async def _get_district_coverage(self, fy_id: Optional[int] = None) -> List[VillageMasterDataCoverage]:
        """Get district-wise coverage data."""

        # Get all districts
        districts_result = await self.db.execute(select(District))
        districts = districts_result.scalars().all()

        coverage_list = []
        for district in districts:
            # Get total GPs in district
            total_gps_result = await self.db.execute(
                select(func.count())
                .select_from(GramPanchayat)
                .where(  # type: ignore
                    GramPanchayat.district_id == district.id
                )
            )
            total_gps = total_gps_result.scalar() or 0

            # Get GPs with surveys
            query = (
                select(func.count(distinct(AnnualSurvey.gp_id)))
                .join(  # type: ignore
                    GramPanchayat, AnnualSurvey.gp_id == GramPanchayat.id
                )
                .where(GramPanchayat.district_id == district.id)
            )

            if fy_id:
                query = query.where(AnnualSurvey.fy_id == fy_id)

            gps_with_data_result = await self.db.execute(query)
            gps_with_data = gps_with_data_result.scalar() or 0

            coverage_percentage = (gps_with_data / total_gps * 100) if total_gps > 0 else 0.0

            coverage_list.append(
                VillageMasterDataCoverage(
                    geography_id=district.id,
                    geography_name=district.name,
                    total_gps=total_gps,
                    gps_with_data=gps_with_data,
                    coverage_percentage=round(coverage_percentage, 2),
                    master_data_status="Available" if gps_with_data > 0 else "Not Available",
                )
            )

        return coverage_list

    async def _get_block_coverage(
        self, district_id: int, fy_id: Optional[int] = None
    ) -> List[VillageMasterDataCoverage]:
        """Get block-wise coverage data within a district."""

        # Get all blocks in district
        blocks_result = await self.db.execute(select(Block).where(Block.district_id == district_id))
        blocks = blocks_result.scalars().all()

        coverage_list = []
        for block in blocks:
            # Get total GPs in block
            total_gps_result = await self.db.execute(
                select(func.count())
                .select_from(GramPanchayat)
                .where(  # type: ignore
                    GramPanchayat.block_id == block.id
                )
            )
            total_gps = total_gps_result.scalar() or 0

            # Get GPs with surveys
            query = (
                select(func.count(distinct(AnnualSurvey.gp_id)))
                .join(  # type: ignore
                    GramPanchayat, AnnualSurvey.gp_id == GramPanchayat.id
                )
                .where(GramPanchayat.block_id == block.id)
            )

            if fy_id:
                query = query.where(AnnualSurvey.fy_id == fy_id)

            gps_with_data_result = await self.db.execute(query)
            gps_with_data = gps_with_data_result.scalar() or 0

            coverage_percentage = (gps_with_data / total_gps * 100) if total_gps > 0 else 0.0

            coverage_list.append(
                VillageMasterDataCoverage(
                    geography_id=block.id,
                    geography_name=block.name,
                    total_gps=total_gps,
                    gps_with_data=gps_with_data,
                    coverage_percentage=round(coverage_percentage, 2),
                    master_data_status="Available" if gps_with_data > 0 else "Not Available",
                )
            )

        return coverage_list

    async def _get_gp_coverage(self, block_id: int, fy_id: Optional[int] = None) -> List[VillageMasterDataCoverage]:
        """Get GP-wise coverage data within a block."""

        # Get all GPs in block
        gps_result = await self.db.execute(select(GramPanchayat).where(GramPanchayat.block_id == block_id))
        gps = gps_result.scalars().all()

        coverage_list = []
        for gp in gps:
            # Check if GP has survey
            query = (
                select(func.count())
                .select_from(AnnualSurvey)
                .where(  # type: ignore
                    AnnualSurvey.gp_id == gp.id
                )
            )

            if fy_id:
                query = query.where(AnnualSurvey.fy_id == fy_id)

            survey_count_result = await self.db.execute(query)
            survey_count = survey_count_result.scalar() or 0

            has_data = survey_count > 0

            coverage_list.append(
                VillageMasterDataCoverage(
                    geography_id=gp.id,
                    geography_name=gp.name,
                    total_gps=1,
                    gps_with_data=1 if has_data else 0,
                    coverage_percentage=100.0 if has_data else 0.0,
                    master_data_status="Available" if has_data else "Not Available",
                )
            )

        return coverage_list
