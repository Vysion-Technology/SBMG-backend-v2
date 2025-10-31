"""
Inspection Service
Handles business logic for inspection management
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import and_, func, select, text
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from models.internal import GeoTypeEnum
from models.response.inspection import (
    PerformanceReportLineItemResponse,
    PerformanceReportResponse,
    TopPerformerInspectionResponse,
    TopPerformerInspectorItemResponse,
)

if TYPE_CHECKING:
    from models.internal import GeoTypeEnum


from auth_utils import UserRole
from models.database.auth import PositionHolder, User
from models.database.geography import Block, GramPanchayat, District
from models.database.inspection import (
    CommunitySanitationInspectionItem,
    HouseHoldWasteCollectionAndDisposalInspectionItem,
    Inspection,
    OtherInspectionItem,
    RoadAndDrainCleaningInspectionItem,
)
from models.requests.inspection import CreateInspectionRequest


class InspectionService:
    """Service for managing inspections."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_active_position(self, user: User) -> Optional[PositionHolder]:
        """Get the active position of the user."""
        # Get the first active position (you might want to add logic for multiple positions)
        for position in user.positions:
            if position.role.name != UserRole.VDO:  # VDO cannot make inspections
                return position
        return None

    async def can_inspect_village(self, user: User, village_id: int) -> bool:
        """Check if user can inspect a village based on their jurisdiction."""
        # Get village details
        result = await self.db.execute(
            select(GramPanchayat)
            .options(selectinload(GramPanchayat.block), selectinload(GramPanchayat.district))
            .where(GramPanchayat.id == village_id)
        )
        village = result.scalar_one_or_none()

        if not village:
            return False

        # Check user's jurisdiction
        for position in user.positions:
            role_name = position.role.name

            # VDO cannot inspect
            if role_name == UserRole.VDO:
                if position.user.gp_id == village_id:
                    return True

            # Admin and SuperAdmin can inspect anywhere
            if role_name in [UserRole.ADMIN, UserRole.SUPERADMIN]:
                return True

            # CEO can inspect in their district
            if role_name == UserRole.CEO and position.user.district_id == village.district_id:
                return True

            # BDO can inspect in their block
            if role_name == UserRole.BDO and position.user.block_id == village.block_id:
                return True

            # Worker can inspect in their assigned area
            if role_name == UserRole.WORKER:
                if position.user.gp_id == village_id:
                    return False
                if position.user.block_id == village.block_id:
                    return False
                if position.user.district_id == village.district_id:
                    return False

        return False

    async def create_inspection(self, user: User, request: CreateInspectionRequest) -> Inspection:
        """Create a new inspection."""
        # Get active position
        positions = await self.db.execute(
            select(PositionHolder).where(PositionHolder.user_id == user.id, PositionHolder.end_date.is_(None))
        )
        positions = positions.scalars().all()
        if not positions:
            raise ValueError("User does not have an active position or is a VDO")
        if len(positions) > 1:
            raise ValueError("User has multiple active positions; cannot determine which to use")
        position = positions[0]

        # Check if user can inspect this village
        if not await self.can_inspect_village(user, request.gp_id):
            raise ValueError("User does not have jurisdiction to inspect this village")

        # Get village details to populate district and block
        result = await self.db.execute(select(GramPanchayat).where(GramPanchayat.id == request.gp_id))
        village = result.scalar_one_or_none()
        if not village:
            raise ValueError("Village not found")

        # Create inspection
        inspection = Inspection(
            remarks=request.remarks,
            position_holder_id=position.id,
            gp_id=request.gp_id,
            village_name=request.village_name,
            date=request.inspection_date or date.today(),
            start_time=request.start_time or datetime.now(),
            lat=request.lat,
            long=request.long,
            register_maintenance=request.register_maintenance,
        )

        self.db.add(inspection)
        await self.db.flush()  # Get the inspection ID

        # Create household waste inspection items if provided
        if request.household_waste:
            household_item = HouseHoldWasteCollectionAndDisposalInspectionItem(
                id=inspection.id,
                waste_collection_frequency=request.household_waste.waste_collection_frequency,
                dry_wet_vehicle_segregation=request.household_waste.dry_wet_vehicle_segregation,
                covered_collection_in_vehicles=request.household_waste.covered_collection_in_vehicles,
                waste_disposed_at_rrc=request.household_waste.waste_disposed_at_rrc,
                rrc_waste_collection_and_disposal_arrangement=request.household_waste.rrc_waste_collection_and_disposal_arrangement,
                waste_collection_vehicle_functional=request.household_waste.waste_collection_vehicle_functional,
            )
            self.db.add(household_item)

        # Create road and drain inspection items if provided
        if request.road_and_drain:
            road_item = RoadAndDrainCleaningInspectionItem(
                id=inspection.id,
                road_cleaning_frequency=request.road_and_drain.road_cleaning_frequency,
                drain_cleaning_frequency=request.road_and_drain.drain_cleaning_frequency,
                disposal_of_sludge_from_drains=request.road_and_drain.disposal_of_sludge_from_drains,
                drain_waste_colllected_on_roadside=request.road_and_drain.drain_waste_colllected_on_roadside,
            )
            self.db.add(road_item)

        # Create community sanitation inspection items if provided
        if request.community_sanitation:
            community_item = CommunitySanitationInspectionItem(
                id=inspection.id,
                csc_cleaning_frequency=request.community_sanitation.csc_cleaning_frequency,
                electricity_and_water=request.community_sanitation.electricity_and_water,
                csc_used_by_community=request.community_sanitation.csc_used_by_community,
                pink_toilets_cleaning=request.community_sanitation.pink_toilets_cleaning,
                pink_toilets_used=request.community_sanitation.pink_toilets_used,
            )
            self.db.add(community_item)

        # Create other inspection items if provided
        if request.other_items:
            other_item = OtherInspectionItem(
                id=inspection.id,
                firm_paid_regularly=request.other_items.firm_paid_regularly,
                cleaning_staff_paid_regularly=request.other_items.cleaning_staff_paid_regularly,
                firm_provided_safety_equipment=request.other_items.firm_provided_safety_equipment,
                regular_feedback_register_entry=request.other_items.regular_feedback_register_entry,
                chart_prepared_for_cleaning_work=request.other_items.chart_prepared_for_cleaning_work,
                village_visibly_clean=request.other_items.village_visibly_clean,
                rate_chart_displayed=request.other_items.rate_chart_displayed,
            )
            self.db.add(other_item)

        await self.db.commit()
        await self.db.refresh(inspection)

        return inspection

    async def get_inspections(
        self,
        page: int = 1,
        page_size: int = 20,
        village_id: Optional[int] = None,
        block_id: Optional[int] = None,
        district_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        inspected_by_user_id: Optional[int] = None,
    ) -> List[Inspection]:
        """Get paginated list of all inspections (admin only)."""
        # Base query
        query = select(Inspection).options(
            selectinload(Inspection.gp).selectinload(GramPanchayat.block),
            selectinload(Inspection.gp).selectinload(GramPanchayat.district),
            selectinload(Inspection.media),
            selectinload(Inspection.other_item),
        )

        # Apply additional filters
        filters: List[Any] = []
        if village_id:
            filters.append(Inspection.gp_id == village_id)
        if block_id:
            filters.append(Inspection.gp_id.in_(select(GramPanchayat.id).where(GramPanchayat.block_id == block_id)))
        if district_id:
            filters.append(
                Inspection.gp_id.in_(select(GramPanchayat.id).where(GramPanchayat.district_id == district_id))
            )
        if start_date:
            filters.append(Inspection.date >= start_date)
        if end_date:
            filters.append(Inspection.date <= end_date)
        if inspected_by_user_id:
            filters.append(
                Inspection.position_holder_id.in_(
                    select(PositionHolder.id).where(PositionHolder.user_id == inspected_by_user_id)
                )
            )

        if filters:
            query = query.where(and_(*filters))

        # Apply pagination
        query = query.order_by(Inspection.date.desc(), Inspection.start_time.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        inspections = list(result.scalars().all())

        return inspections

    async def get_total_count(
        self,
        village_id: Optional[int] = None,
        block_id: Optional[int] = None,
        district_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> int:
        """Get total count of all inspections (admin only)."""
        # Base count query
        count_query = select(func.count()).select_from(Inspection)

        # Apply additional filters
        filters: List[Any] = []
        if village_id:
            filters.append(Inspection.gp_id == village_id)
        if block_id:
            filters.append(Inspection.gp_id.in_(select(GramPanchayat.id).where(GramPanchayat.block_id == block_id)))
        if district_id:
            filters.append(
                Inspection.gp_id.in_(select(GramPanchayat.id).where(GramPanchayat.district_id == district_id))
            )
        if start_date:
            filters.append(Inspection.date >= start_date)
        if end_date:
            filters.append(Inspection.date <= end_date)

        if filters:
            count_query = count_query.where(and_(*filters))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        return total

    async def get_my_inspections(
        self,
        position_ids: List[int],
        page: int = 1,
        page_size: int = 20,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Inspection]:
        """Get paginated list of inspections done by the current user."""
        # Base query
        query = select(Inspection).options(
            selectinload(Inspection.gp).selectinload(GramPanchayat.block),
            selectinload(Inspection.gp).selectinload(GramPanchayat.district),
            selectinload(Inspection.media),
            selectinload(Inspection.other_item),
        )

        # Filter by position holder IDs
        filters: List[Any] = [Inspection.position_holder_id.in_(position_ids)]

        # Apply additional filters
        if start_date:
            filters.append(Inspection.date >= start_date)
        if end_date:
            filters.append(Inspection.date <= end_date)

        query = query.where(and_(*filters))

        # Apply pagination
        query = query.order_by(Inspection.date.desc(), Inspection.start_time.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        inspections = list(result.scalars().all())

        return inspections

    async def get_my_inspections_count(
        self,
        position_ids: List[int],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> int:
        """Get total count of inspections done by the current user."""
        # Base count query
        count_query = select(func.count()).select_from(Inspection)

        # Filter by position holder IDs
        filters: List[Any] = [Inspection.position_holder_id.in_(position_ids)]

        # Apply additional filters
        if start_date:
            filters.append(Inspection.date >= start_date)
        if end_date:
            filters.append(Inspection.date <= end_date)

        count_query = count_query.where(and_(*filters))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        return total

    async def get_district_inspection_analytics(
        self,
        district_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Get inspection analytics for a district."""
        from sqlalchemy import text

        query = text("""
            SELECT * FROM get_district_inspection_analytics(:district_id, :start_date, :end_date)
        """)

        result = await self.db.execute(
            query,
            {
                "district_id": district_id,
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        row = result.fetchone()

        if row:
            return {
                "district_id": row.district_id,
                "total_blocks": row.total_blocks,
                "inspected_blocks": row.inspected_blocks,
                "total_gps": row.total_gps,
                "inspected_gps": row.inspected_gps,
                "average_score": row.average_score,
                "coverage_percentage": row.coverage_percentage,
            }
        return {}

    async def get_state_inspection_analytics(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get inspection analytics for the state."""
        from sqlalchemy import text

        query = text("""
            SELECT * FROM get_state_inspection_analytics(:start_date, :end_date)
        """)

        result = await self.db.execute(
            query,
            {
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        row = result.fetchone()

        if row:
            return {
                "total_districts": row.total_districts,
                "inspected_districts": row.inspected_districts,
                "total_blocks": row.total_blocks,
                "inspected_blocks": row.inspected_blocks,
                "total_gps": row.total_gps,
                "inspected_gps": row.inspected_gps,
                "average_score": row.average_score,
                "coverage_percentage": row.coverage_percentage,
            }
        return {}

    async def get_villages_inspection_analytics_batch(
        self,
        village_ids: list[int],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[int, Dict[str, Any]]:
        """Get inspection analytics for multiple villages in one query."""
        from sqlalchemy import text

        if not village_ids:
            return {}

        query = text("""
            SELECT * FROM get_villages_inspection_analytics_batch(:village_ids, :start_date, :end_date)
        """)

        result = await self.db.execute(
            query,
            {
                "village_ids": village_ids,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        # Return as dict keyed by village_id for easy lookup
        analytics_dict = {}
        for row in result:
            analytics_dict[row.village_id] = {
                "village_id": row.village_id,
                "total_inspections": row.total_inspections,
                "average_score": row.average_score,
                "latest_score": row.latest_score,
                "coverage_percentage": row.coverage_percentage,
            }
        return analytics_dict

    async def get_blocks_inspection_analytics_batch(
        self,
        block_ids: list[int],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[int, Dict[str, Any]]:
        """Get inspection analytics for multiple blocks in one query."""
        from sqlalchemy import text

        if not block_ids:
            return {}

        query = text("""
            SELECT * FROM get_blocks_inspection_analytics_batch(:block_ids, :start_date, :end_date)
        """)

        result = await self.db.execute(
            query,
            {
                "block_ids": block_ids,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        # Return as dict keyed by block_id for easy lookup
        analytics_dict = {}
        for row in result:
            analytics_dict[row.block_id] = {
                "block_id": row.block_id,
                "total_gps": row.total_gps,
                "inspected_gps": row.inspected_gps,
                "average_score": row.average_score,
                "coverage_percentage": row.coverage_percentage,
            }
        return analytics_dict

    async def get_districts_inspection_analytics_batch(
        self,
        district_ids: list[int],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[int, Dict[str, Any]]:
        """Get inspection analytics for multiple districts in one query."""

        if not district_ids:
            return {}

        query = text("""
            SELECT * FROM get_districts_inspection_analytics_batch(:district_ids, :start_date, :end_date)
        """)

        result = await self.db.execute(
            query,
            {
                "district_ids": district_ids,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        # Return as dict keyed by district_id for easy lookup
        analytics_dict = {}
        for row in result:
            analytics_dict[row.district_id] = {
                "district_id": row.district_id,
                "total_blocks": row.total_blocks,
                "inspected_blocks": row.inspected_blocks,
                "total_gps": row.total_gps,
                "inspected_gps": row.inspected_gps,
                "average_score": row.average_score,
                "coverage_percentage": row.coverage_percentage,
            }
        return analytics_dict

    async def inspection_analytics(
        self,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        gp_id: Optional[int] = None,
        level: Optional["GeoTypeEnum"] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Get inspection analytics aggregated by geographic level."""

        # Default to current month if no dates provided
        if not start_date:
            start_date = date.today().replace(day=1)
        if not end_date:
            end_date = date.today()

        # Default to DISTRICT level if not provided
        if level is None:
            level = GeoTypeEnum.DISTRICT

        response_items: List[Dict[str, Any]] = []

        if level == GeoTypeEnum.DISTRICT:
            # Get analytics for all districts or specific district

            if district_id:
                analytics = await self.get_district_inspection_analytics(district_id, start_date, end_date)
                if analytics:
                    # Get district name
                    result = await self.db.execute(select(District.name).where(District.id == district_id))
                    name = result.scalar()

                    item = {
                        "geography_id": district_id,
                        "geography_name": name,
                        **analytics,
                    }

                    response_items.append(item)
            else:
                # Get all districts - use batch query

                districts_result = await self.db.execute(select(District.id, District.name))
                districts = districts_result.fetchall()

                # Get analytics for all districts in one batch query
                district_ids = [d.id for d in districts]
                analytics_batch = await self.get_districts_inspection_analytics_batch(
                    district_ids, start_date, end_date
                )

                for district in districts:
                    analytics = analytics_batch.get(district.id)
                    if analytics:
                        item = {
                            "geography_id": district.id,
                            "geography_name": district.name,
                            **analytics,
                        }
                        response_items.append(item)

        elif level == GeoTypeEnum.BLOCK:
            # Get analytics for blocks

            query = select(Block.id, Block.name)
            if district_id:
                query = query.where(Block.district_id == district_id)

            blocks_result = await self.db.execute(query)
            blocks = blocks_result.fetchall()

            # Get analytics for all blocks in one batch query
            block_ids = [b.id for b in blocks]
            analytics_batch = await self.get_blocks_inspection_analytics_batch(block_ids, start_date, end_date)

            for block_item in blocks:
                analytics = analytics_batch.get(block_item.id)
                if analytics:
                    item = {
                        "geography_id": block_item.id,
                        "geography_name": block_item.name,
                        **analytics,
                    }
                    response_items.append(item)

        else:  # VILLAGE level
            # Get analytics for villages (gram panchayats)

            query = select(GramPanchayat.id, GramPanchayat.name)
            if block_id:
                query = query.where(GramPanchayat.block_id == block_id)
            elif district_id:
                # If district_id is provided, filter by district
                query = query.where(GramPanchayat.district_id == district_id)

            gps_result = await self.db.execute(query)
            gps = gps_result.fetchall()

            # Get analytics for all villages in one batch query
            village_ids = [gp.id for gp in gps]
            analytics_batch = await self.get_villages_inspection_analytics_batch(village_ids, start_date, end_date)

            for gp_item in gps:
                analytics = analytics_batch.get(gp_item.id)
                if analytics:
                    item = {
                        "geography_id": gp_item.id,
                        "geography_name": gp_item.name,
                        **analytics,
                    }
                    response_items.append(item)

        for item in response_items:
            # Round float values to 2 decimal places
            for key in ["average_score", "coverage_percentage", "latest_score"]:
                if key in item and item[key] is not None:
                    item[key] = float(f"{item[key]:.2f}")
        return {
            "geo_type": level.value,
            "response": response_items,
        }

    async def top_performer_inspectors(
        self,
        level: GeoTypeEnum,
        top_n: int = 5,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        gp_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[TopPerformerInspectionResponse]:
        """Get the inspectors with the highest number of inspections conducted at the specified geographic level."""
        # TODO: Implement the logic to fetch top performer inspectors based on the level and filters

        return [
            TopPerformerInspectionResponse(
                level=level,
                inspectors=[
                    TopPerformerInspectorItemResponse(
                        geo_id=1,
                        geo_name="Sample Geo",
                        inspector_name="Inspector Name",
                        inspections_count=100,
                    ),
                    TopPerformerInspectorItemResponse(
                        geo_id=1,
                        geo_name="Sample Geo",
                        inspector_name="Inspector Name",
                        inspections_count=80,
                    ),
                    TopPerformerInspectorItemResponse(
                        geo_id=1,
                        geo_name="Sample Geo",
                        inspector_name="Inspector Name",
                        inspections_count=70,
                    ),
                ],
            )
        ]  # Implementation goes here

    async def get_performance_report(
        self,
        level: GeoTypeEnum,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        gp_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> PerformanceReportResponse:
        """Get performance report aggregated by geographic level."""

        # TODO: Implement the logic to fetch performance report based on the level and filters

        return PerformanceReportResponse(
            level=level,
            line_items=[
                PerformanceReportLineItemResponse(
                    geo_id=1,
                    geo_name="Sample Geo",
                    total_inspections=150,
                    average_score=85.5,
                    coverage_percentage=90.0,
                ),
                PerformanceReportLineItemResponse(
                    geo_id=2,
                    geo_name="Sample Geo 2",
                    total_inspections=120,
                    average_score=80.0,
                    coverage_percentage=85.0,
                ),
            ],
        )  # Implementation goes here
