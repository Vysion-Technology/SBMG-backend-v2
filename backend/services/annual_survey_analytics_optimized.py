"""
Annual Survey Analytics Service (Optimized)
Handles business logic for annual survey analytics using database-level aggregations
"""

import calendar
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import and_, case, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.database.geography import Block, District, GramPanchayat
from models.database.contractor import Contractor
from models.database.survey_master import (
    AnnualSurvey,
    D2DActivities,
    DoorToDoorCollectionDetails,
    FSMDetails,
    FundSanctioned,
    GobardhanProject,
    LWMAssets,
    ODFSustainability,
    PWMUDetails,
    SBMGYearTargets,
    SWMAssetsCategory,
    VillageData,
    VillageGWMAssets,
    VillageSBMGAssets,
    WorkOrderDetails,
    BartanBank,
    VehicleAssets,
)
from models.response.annual_survey_analytics import (
    AnnualOverview,
    AssetsDashboardResponse,
    BlockAnalytics,
    D2DActivitiesStats,
    DistrictAnalytics,
    FSMStats,
    GobardhanStats,
    GPAnalytics,
    LWMAssetsStats,
    ODFSustainabilityStats,
    PWMUStats,
    SchemeTargetAchievement,
    StateAnalytics,
    SWMAssetsStats,
    VillageMasterDataCoverage,
    HierarchicalAssetsResponse,
    GeographyAssetBreakdown,
    BartanBankStats,
    VehicleStats,
    WorkFrequencyCount,
)


class AnnualSurveyAnalyticsServiceOptimized:
    """Optimized service for annual survey analytics using database aggregations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_assets_dashboard_totals(
        self,
        fy_id: Optional[int] = None,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        gp_id: Optional[int] = None,
    ) -> AssetsDashboardResponse:
        """Get aggregated totals for the Assets Dashboard."""

        # Build base filters based on jurisdiction and FY
        filters = []
        if fy_id:
            filters.append(AnnualSurvey.fy_id == fy_id)
        if district_id:
            filters.append(GramPanchayat.district_id == district_id)
        if block_id:
            filters.append(GramPanchayat.block_id == block_id)
        if gp_id:
            filters.append(AnnualSurvey.gp_id == gp_id)

        has_filters = len(filters) > 0
        needs_gp_join = bool(district_id or block_id)

        # Helper function to apply dynamic joins and filters
        def apply_filters(query, model_class):
            if has_filters:
                # Join AnnualSurvey to access fy_id and gp_id
                query = query.select_from(model_class).join(
                    AnnualSurvey, AnnualSurvey.id == model_class.id
                )
                # Join GramPanchayat if we need to filter by block_id or district_id
                if needs_gp_join:
                    query = query.join(
                        GramPanchayat, AnnualSurvey.gp_id == GramPanchayat.id
                    )
                query = query.where(and_(*filters))
            return query

        # 1. ODF Sustainability
        odf_query = select(
            func.coalesce(func.sum(ODFSustainability.ihhl), 0).label("ihhl"),
            func.coalesce(func.sum(ODFSustainability.retrofitting), 0).label(
                "retrofitting"
            ),
            func.coalesce(func.sum(ODFSustainability.csc), 0).label("csc"),
            func.coalesce(func.sum(ODFSustainability.csc_shala_darpan), 0).label(
                "csc_shala_darpan"
            ),
        )
        odf_query = apply_filters(odf_query, ODFSustainability)

        # 2. SWM Assets
        swm_query = select(
            func.coalesce(func.sum(SWMAssetsCategory.bins_hh_level), 0).label(
                "bins_hh_level"
            ),
            func.coalesce(func.sum(SWMAssetsCategory.bins_public_places), 0).label(
                "bins_public_places"
            ),
            func.coalesce(func.sum(SWMAssetsCategory.community_compost_pits), 0).label(
                "community_compost_pits"
            ),
            func.coalesce(func.sum(SWMAssetsCategory.hh_compost_pit), 0).label(
                "hh_compost_pit"
            ),
            func.coalesce(func.sum(SWMAssetsCategory.segregation_sheds), 0).label(
                "segregation_sheds"
            ),
            func.coalesce(func.sum(SWMAssetsCategory.tricycles_manual), 0).label(
                "tricycles_manual"
            ),
            func.coalesce(func.sum(SWMAssetsCategory.e_rickshaws), 0).label(
                "e_rickshaws"
            ),
            func.coalesce(func.sum(SWMAssetsCategory.motorized_vehicles), 0).label(
                "motorized_vehicles"
            ),
        )
        swm_query = apply_filters(swm_query, SWMAssetsCategory)

        # 3. LWM Assets
        lwm_query = select(
            func.coalesce(func.sum(LWMAssets.pits_hh_level), 0).label("pits_hh_level"),
            func.coalesce(func.sum(LWMAssets.community_pits), 0).label(
                "community_pits"
            ),
            func.coalesce(func.sum(LWMAssets.wsp), 0).label("wsp"),
            func.coalesce(func.sum(LWMAssets.dewats), 0).label("dewats"),
            func.coalesce(func.sum(LWMAssets.wetlands), 0).label("wetlands"),
            func.coalesce(func.sum(LWMAssets.other_treatments), 0).label(
                "other_treatments"
            ),
            func.coalesce(func.sum(LWMAssets.drainage_channels), 0).label(
                "drainage_channels"
            ),
        )
        lwm_query = apply_filters(lwm_query, LWMAssets)

        # 4. PWMU Details
        pwmu_query = select(
            func.coalesce(func.sum(PWMUDetails.established_pwmu), 0).label(
                "established_pwmu"
            ),
            func.coalesce(func.sum(PWMUDetails.blocks_covered_pwmu), 0).label(
                "blocks_covered_pwmu"
            ),
            func.coalesce(func.sum(PWMUDetails.urban_mrfs), 0).label("urban_mrfs"),
            func.coalesce(func.sum(PWMUDetails.blocks_covered_urban_mrf), 0).label(
                "blocks_covered_urban_mrf"
            ),
        )
        pwmu_query = apply_filters(pwmu_query, PWMUDetails)

        # 5. FSM Details
        fsm_query = select(
            func.coalesce(func.sum(FSMDetails.twin_pit_toilets), 0).label(
                "twin_pit_toilets"
            ),
            func.coalesce(func.sum(FSMDetails.single_pit_toilets), 0).label(
                "single_pit_toilets"
            ),
            func.coalesce(func.sum(FSMDetails.septic_tank_toilets), 0).label(
                "septic_tank_toilets"
            ),
            func.coalesce(func.sum(FSMDetails.retrofitted_toilets), 0).label(
                "retrofitted_toilets"
            ),
            func.coalesce(func.sum(FSMDetails.mechanized_desludging), 0).label(
                "mechanized_desludging"
            ),
            func.coalesce(func.sum(FSMDetails.fstps_rural), 0).label("fstps_rural"),
            func.coalesce(func.sum(FSMDetails.fstps_urban), 0).label("fstps_urban"),
        )
        fsm_query = apply_filters(fsm_query, FSMDetails)

        # 6. Gobardhan Project
        gobardhan_query = select(
            func.coalesce(func.sum(GobardhanProject.total_sanctioned), 0).label(
                "total_sanctioned"
            ),
            func.coalesce(func.sum(GobardhanProject.total_functional), 0).label(
                "total_functional"
            ),
            func.coalesce(func.sum(GobardhanProject.gas_production), 0).label(
                "gas_production"
            ),
        )
        gobardhan_query = apply_filters(gobardhan_query, GobardhanProject)

        # 7. D2D Activities (Special case since it queries directly from AnnualSurvey)
        d2d_query = (
            select(
                func.count(distinct(AnnualSurvey.gp_id)).label("total_gps"),
                func.count(
                    distinct(
                        case(
                            (D2DActivities.is_active.is_(True), AnnualSurvey.gp_id),
                            else_=None,
                        )
                    )
                ).label("gps_with_d2d_active"),
                func.count(
                    distinct(
                        case(
                            (D2DActivities.is_active.is_(True), AnnualSurvey.gp_id),
                            else_=None,
                        )
                    )
                ).label("running_started_gps"),
                func.count(
                    distinct(
                        case(
                            (
                                (D2DActivities.is_active.is_(False)) | (D2DActivities.id.is_(None)),
                                AnnualSurvey.gp_id,
                            ),
                            else_=None,
                        )
                    )
                ).label("not_started_gps"),
                func.count(
                    distinct(
                        case(
                            (D2DActivities.work_frequency == "daily", AnnualSurvey.gp_id),
                            else_=None,
                        )
                    )
                ).label("freq_daily"),
                func.count(
                    distinct(
                        case(
                            (D2DActivities.work_frequency == "weekly", AnnualSurvey.gp_id),
                            else_=None,
                        )
                    )
                ).label("freq_weekly"),
                func.count(
                    distinct(
                        case(
                            (D2DActivities.work_frequency == "15 days", AnnualSurvey.gp_id),
                            else_=None,
                        )
                    )
                ).label("freq_fifteen_days"),
                func.count(
                    distinct(
                        case(
                            (D2DActivities.work_frequency == "monthly", AnnualSurvey.gp_id),
                            else_=None,
                        )
                    )
                ).label("freq_monthly"),
                func.coalesce(func.sum(D2DActivities.sanctioned_tender), 0).label(
                    "sanctioned_tender"
                ),
                func.coalesce(func.sum(D2DActivities.sanctioned_self_gp), 0).label(
                    "sanctioned_self_gp"
                ),
                func.coalesce(func.sum(D2DActivities.sanctioned_csr_ngo), 0).label(
                    "sanctioned_csr_ngo"
                ),
                func.coalesce(func.sum(D2DActivities.sanctioned_shg), 0).label(
                    "sanctioned_shg"
                ),
                func.coalesce(func.sum(D2DActivities.sanctioned_mixed_model), 0).label(
                    "sanctioned_mixed_model"
                ),
                func.coalesce(func.sum(D2DActivities.total_expenditure), 0).label(
                    "total_expenditure"
                ),
                func.coalesce(func.sum(D2DActivities.vehicles_deployed), 0).label(
                    "vehicles_deployed"
                ),
                func.coalesce(func.sum(D2DActivities.persons_deployed), 0).label(
                    "persons_deployed"
                ),
                func.coalesce(func.sum(D2DActivities.households_covered), 0).label(
                    "households_covered"
                ),
                func.coalesce(func.sum(D2DActivities.status_start), 0).label(
                    "status_start"
                ),
                func.coalesce(func.sum(D2DActivities.status_running), 0).label(
                    "status_running"
                ),
                func.coalesce(func.sum(D2DActivities.status_completed), 0).label(
                    "status_completed"
                ),
            )
            .select_from(AnnualSurvey)
            .outerjoin(D2DActivities, AnnualSurvey.id == D2DActivities.id)
        )

        if needs_gp_join:
            d2d_query = d2d_query.join(
                GramPanchayat, AnnualSurvey.gp_id == GramPanchayat.id
            )

        if has_filters:
            d2d_query = d2d_query.where(and_(*filters))

        # 8. Bartan Bank
        bartan_query = select(
            func.coalesce(func.sum(BartanBank.established_banks), 0).label(
                "established_banks"
            )
        )
        bartan_query = apply_filters(bartan_query, BartanBank)

        # 9. Vehicle Assets
        vehicle_query = select(
            func.coalesce(func.sum(VehicleAssets.owned_tricycles), 0).label(
                "owned_tricycles"
            ),
            func.coalesce(func.sum(VehicleAssets.owned_e_rickshaws), 0).label(
                "owned_e_rickshaws"
            ),
            func.coalesce(func.sum(VehicleAssets.owned_motorized_vehicles), 0).label(
                "owned_motorized_vehicles"
            ),
            func.coalesce(func.sum(VehicleAssets.contractor_tricycles), 0).label(
                "contractor_tricycles"
            ),
            func.coalesce(func.sum(VehicleAssets.contractor_e_rickshaws), 0).label(
                "contractor_e_rickshaws"
            ),
            func.coalesce(func.sum(VehicleAssets.contractor_motorized_vehicles), 0).label(
                "contractor_motorized_vehicles"
            ),
        )
        vehicle_query = apply_filters(vehicle_query, VehicleAssets)

        # Execute all queries
        odf_res = (await self.db.execute(odf_query)).one()
        swm_res = (await self.db.execute(swm_query)).one()
        lwm_res = (await self.db.execute(lwm_query)).one()
        pwmu_res = (await self.db.execute(pwmu_query)).one()
        fsm_res = (await self.db.execute(fsm_query)).one()
        gob_res = (await self.db.execute(gobardhan_query)).one()
        d2d_res = (await self.db.execute(d2d_query)).one()
        bartan_res = (await self.db.execute(bartan_query)).one()
        vehicle_res = (await self.db.execute(vehicle_query)).one()

        # Calculate contracts ending next month
        today = date.today()
        if today.month == 12:
            next_month = 1
            next_year = today.year + 1
        else:
            next_month = today.month + 1
            next_year = today.year

        start_date = datetime(next_year, next_month, 1, 0, 0, 0)
        last_day = calendar.monthrange(next_year, next_month)[1]
        end_date = datetime(next_year, next_month, last_day, 23, 59, 59)

        contractor_filters = [
            Contractor.contract_end_date >= start_date,
            Contractor.contract_end_date <= end_date
        ]

        if gp_id:
            contractor_filters.append(Contractor.gp_id == gp_id)

        contractor_query = select(func.count(Contractor.id))

        if district_id or block_id:
            contractor_query = contractor_query.join(GramPanchayat, Contractor.gp_id == GramPanchayat.id)
            if district_id:
                contractor_filters.append(GramPanchayat.district_id == district_id)
            if block_id:
                contractor_filters.append(GramPanchayat.block_id == block_id)

        contractor_query = contractor_query.where(and_(*contractor_filters))
        contracts_ending_next_month = (await self.db.execute(contractor_query)).scalar_one() or 0

        return AssetsDashboardResponse(
            odf_sustainability=ODFSustainabilityStats(
                ihhl=odf_res.ihhl,
                retrofitting=odf_res.retrofitting,
                csc=odf_res.csc,
                csc_shala_darpan=odf_res.csc_shala_darpan,
            ),
            swm_assets=SWMAssetsStats(
                bins_hh_level=swm_res.bins_hh_level,
                bins_public_places=swm_res.bins_public_places,
                community_compost_pits=swm_res.community_compost_pits,
                hh_compost_pit=swm_res.hh_compost_pit,
                segregation_sheds=swm_res.segregation_sheds,
                tricycles_manual=swm_res.tricycles_manual,
                e_rickshaws=swm_res.e_rickshaws,
                motorized_vehicles=swm_res.motorized_vehicles,
            ),
            lwm_assets=LWMAssetsStats(
                pits_hh_level=lwm_res.pits_hh_level,
                community_pits=lwm_res.community_pits,
                wsp=lwm_res.wsp,
                dewats=lwm_res.dewats,
                wetlands=lwm_res.wetlands,
                other_treatments=lwm_res.other_treatments,
                drainage_channels=lwm_res.drainage_channels,
            ),
            pwmu=PWMUStats(
                established_pwmu=pwmu_res.established_pwmu,
                blocks_covered_pwmu=pwmu_res.blocks_covered_pwmu,
                urban_mrfs=pwmu_res.urban_mrfs,
                blocks_covered_urban_mrf=pwmu_res.blocks_covered_urban_mrf,
            ),
            fsm=FSMStats(
                twin_pit_toilets=fsm_res.twin_pit_toilets,
                single_pit_toilets=fsm_res.single_pit_toilets,
                septic_tank_toilets=fsm_res.septic_tank_toilets,
                retrofitted_toilets=fsm_res.retrofitted_toilets,
                mechanized_desludging=fsm_res.mechanized_desludging,
                fstps_rural=fsm_res.fstps_rural,
                fstps_urban=fsm_res.fstps_urban,
            ),
            gobardhan=GobardhanStats(
                total_sanctioned=gob_res.total_sanctioned,
                total_functional=gob_res.total_functional,
                gas_production=float(gob_res.gas_production),
            ),
            d2d_activities=D2DActivitiesStats(
                total_gps=d2d_res.total_gps,
                gps_with_d2d_active=d2d_res.gps_with_d2d_active or 0,
                not_started_gps=d2d_res.not_started_gps or 0,
                running_started_gps=d2d_res.running_started_gps or 0,
                sanctioned_tender=d2d_res.sanctioned_tender,
                sanctioned_self_gp=d2d_res.sanctioned_self_gp,
                sanctioned_csr_ngo=d2d_res.sanctioned_csr_ngo,
                sanctioned_shg=d2d_res.sanctioned_shg,
                sanctioned_mixed_model=d2d_res.sanctioned_mixed_model,
                total_expenditure=float(d2d_res.total_expenditure),
                vehicles_deployed=d2d_res.vehicles_deployed,
                persons_deployed=d2d_res.persons_deployed,
                households_covered=d2d_res.households_covered,
                status_start=d2d_res.status_start,
                status_running=d2d_res.status_running,
                status_completed=d2d_res.status_completed,
                work_frequency_count=WorkFrequencyCount(
                    daily=d2d_res.freq_daily or 0,
                    weekly=d2d_res.freq_weekly or 0,
                    fifteen_days=d2d_res.freq_fifteen_days or 0,
                    monthly=d2d_res.freq_monthly or 0,
                ),
            ),
            bartan_bank=BartanBankStats(
                established_banks=bartan_res.established_banks,
            ),
            vehicle_assets=VehicleStats(
                owned_tricycles=vehicle_res.owned_tricycles,
                owned_e_rickshaws=vehicle_res.owned_e_rickshaws,
                owned_motorized_vehicles=vehicle_res.owned_motorized_vehicles,
                contractor_tricycles=vehicle_res.contractor_tricycles,
                contractor_e_rickshaws=vehicle_res.contractor_e_rickshaws,
                contractor_motorized_vehicles=vehicle_res.contractor_motorized_vehicles,
            ),
            contracts_ending_next_month=contracts_ending_next_month,
        )

    async def get_assets_drill_down(
        self,
        fy_id: Optional[int] = None,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
    ) -> HierarchicalAssetsResponse:
        """Get hierarchical asset analytics breakdown (District -> Block -> GP)."""

        # Determine the level of breakdown and the grouping entity
        if block_id:
            # Level: GP
            geography_type = "gp"
            group_by_entity = GramPanchayat
            filters = [GramPanchayat.block_id == block_id]
        elif district_id:
            # Level: Block
            geography_type = "block"
            group_by_entity = Block
            filters = [Block.district_id == district_id]
        else:
            # Level: District
            geography_type = "district"
            group_by_entity = District
            filters = []

        # Fetch all geography items for the target level
        geo_query = select(group_by_entity.id, group_by_entity.name)
        if filters:
            geo_query = geo_query.where(and_(*filters))
        
        geo_result = await self.db.execute(geo_query)
        geo_items = geo_result.all()

        results = []
        for geo in geo_items:
            # Call the existing optimized total method for each geography item
            if geography_type == "district":
                assets = await self.get_assets_dashboard_totals(fy_id=fy_id, district_id=geo.id)
            elif geography_type == "block":
                assets = await self.get_assets_dashboard_totals(fy_id=fy_id, block_id=geo.id)
            else:  # gp
                assets = await self.get_assets_dashboard_totals(fy_id=fy_id, gp_id=geo.id)
            
            results.append(
                GeographyAssetBreakdown(
                    geography_id=geo.id,
                    geography_name=geo.name,
                    assets=assets
                )
            )

        return HierarchicalAssetsResponse(
            geography_type=geography_type,
            items=results
        )

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
