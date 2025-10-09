"""
Inspection Service
Handles business logic for inspection management
"""

from typing import List, Optional, Tuple, Dict
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, extract
from sqlalchemy.orm import selectinload

from models.database.inspection import (
    Inspection,
    InspectionImage,
    HouseHoldWasteCollectionAndDisposalInspectionItem,
    RoadAndDrainCleaningInspectionItem,
    CommunitySanitationInspectionItem,
    OtherInspectionItem,
)
from models.database.auth import User, PositionHolder
from models.database.geography import GramPanchayat
from models.requests.inspection import (
    CreateInspectionRequest,
)
from auth_utils import UserRole


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
            .options(
                selectinload(GramPanchayat.block), selectinload(GramPanchayat.district)
            )
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
                continue

            # Admin and SuperAdmin can inspect anywhere
            if role_name in [UserRole.ADMIN, UserRole.SUPERADMIN]:
                return True

            # CEO can inspect in their district
            if (
                role_name == UserRole.CEO
                and position.district_id == village.district_id
            ):
                return True

            # BDO can inspect in their block
            if role_name == UserRole.BDO and position.block_id == village.block_id:
                return True

            # Worker can inspect in their assigned area
            if role_name == UserRole.WORKER:
                if position.village_id == village_id:
                    return True
                if position.block_id == village.block_id:
                    return True
                if position.district_id == village.district_id:
                    return True

        return False

    async def create_inspection(
        self, user: User, request: CreateInspectionRequest
    ) -> Inspection:
        """Create a new inspection."""
        # Get active position
        position = await self.get_user_active_position(user)
        if not position:
            raise ValueError("User does not have an active position or is a VDO")

        # Check if user can inspect this village
        if not await self.can_inspect_village(user, request.village_id):
            raise ValueError("User does not have jurisdiction to inspect this village")

        # Get village details to populate district and block
        result = await self.db.execute(
            select(GramPanchayat).where(GramPanchayat.id == request.village_id)
        )
        village = result.scalar_one_or_none()
        if not village:
            raise ValueError("Village not found")

        # Create inspection
        inspection = Inspection(
            remarks=request.remarks,
            position_holder_id=position.id,
            village_id=request.village_id,
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

        # Create images if provided
        if request.images:
            for img in request.images:
                image = InspectionImage(
                    inspection_id=inspection.id,
                    image_url=img.image_url,
                )
                self.db.add(image)

        await self.db.commit()
        await self.db.refresh(inspection)

        return inspection

    async def get_inspection_by_id(self, inspection_id: int) -> Optional[Inspection]:
        """Get inspection by ID with all related data."""
        result = await self.db.execute(
            select(Inspection)
            .options(
                selectinload(Inspection.village).selectinload(GramPanchayat.block),
                selectinload(Inspection.village).selectinload(GramPanchayat.district),
                selectinload(Inspection.media),
            )
            .where(Inspection.id == inspection_id)
        )
        return result.scalar_one_or_none()

    def get_user_jurisdiction_filter(self, user: User):
        """Get jurisdiction filter for inspections based on user role."""
        user_roles = [pos.role.name for pos in user.positions if pos.role]

        # Admin can see all inspections
        if UserRole.ADMIN in user_roles or UserRole.SUPERADMIN in user_roles:
            return None

        jurisdiction_filters = []

        for position in user.positions:
            # VDO can see inspections in their village
            if position.role.name == UserRole.VDO and position.village_id:
                jurisdiction_filters.append(
                    Inspection.village_id == position.village_id
                )

            # BDO can see inspections in their block
            elif position.role.name == UserRole.BDO and position.block_id:
                # Need to join with villages to filter by block
                jurisdiction_filters.append(
                    Inspection.village_id.in_(
                        select(GramPanchayat.id).where(
                            GramPanchayat.block_id == position.block_id
                        )
                    )
                )

            # CEO can see inspections in their district
            elif position.role.name == UserRole.CEO and position.district_id:
                # Need to join with villages to filter by district
                jurisdiction_filters.append(
                    Inspection.village_id.in_(
                        select(GramPanchayat.id).where(
                            GramPanchayat.district_id == position.district_id
                        )
                    )
                )

            # Worker can see inspections in their assigned area
            elif position.role.name == UserRole.WORKER:
                if position.village_id:
                    jurisdiction_filters.append(
                        Inspection.village_id == position.village_id
                    )
                elif position.block_id:
                    jurisdiction_filters.append(
                        Inspection.village_id.in_(
                            select(GramPanchayat.id).where(
                                GramPanchayat.block_id == position.block_id
                            )
                        )
                    )
                elif position.district_id:
                    jurisdiction_filters.append(
                        Inspection.village_id.in_(
                            select(GramPanchayat.id).where(
                                GramPanchayat.district_id == position.district_id
                            )
                        )
                    )

        return or_(*jurisdiction_filters) if jurisdiction_filters else None

    async def get_inspections_paginated(
        self,
        user: User,
        page: int = 1,
        page_size: int = 20,
        village_id: Optional[int] = None,
        block_id: Optional[int] = None,
        district_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Tuple[List[Inspection], int]:
        """Get paginated list of inspections within user's jurisdiction."""
        # Base query
        query = select(Inspection).options(
            selectinload(Inspection.village).selectinload(GramPanchayat.block),
            selectinload(Inspection.village).selectinload(GramPanchayat.district),
            selectinload(Inspection.media),
        )

        # Apply jurisdiction filter
        jurisdiction_filter = self.get_user_jurisdiction_filter(user)
        if jurisdiction_filter is not None:
            query = query.where(jurisdiction_filter)

        # Apply additional filters
        filters = []
        if village_id:
            filters.append(Inspection.village_id == village_id)
        if block_id:
            filters.append(
                Inspection.village_id.in_(
                    select(GramPanchayat.id).where(GramPanchayat.block_id == block_id)
                )
            )
        if district_id:
            filters.append(
                Inspection.village_id.in_(
                    select(GramPanchayat.id).where(
                        GramPanchayat.district_id == district_id
                    )
                )
            )
        if start_date:
            filters.append(Inspection.date >= start_date)
        if end_date:
            filters.append(Inspection.date <= end_date)

        if filters:
            query = query.where(and_(*filters))

        # Get total count
        count_query = select(func.count()).select_from(Inspection)
        if jurisdiction_filter is not None:
            count_query = count_query.where(jurisdiction_filter)
        if filters:
            count_query = count_query.where(and_(*filters))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.order_by(Inspection.date.desc(), Inspection.start_time.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        inspections = list(result.scalars().all())

        return inspections, total

    async def get_inspection_statistics(self, user: User) -> Dict[str, int]:
        """Get inspection statistics for user's jurisdiction."""
        jurisdiction_filter = self.get_user_jurisdiction_filter(user)

        # Total inspections
        total_query = select(func.count()).select_from(Inspection)
        if jurisdiction_filter is not None:
            total_query = total_query.where(jurisdiction_filter)
        total_result = await self.db.execute(total_query)
        total = total_result.scalar() or 0

        # This month
        month_query = (
            select(func.count())
            .select_from(Inspection)
            .where(
                and_(
                    extract("month", Inspection.date) == datetime.now().month,
                    extract("year", Inspection.date) == datetime.now().year,
                )
            )
        )
        if jurisdiction_filter is not None:
            month_query = month_query.where(jurisdiction_filter)
        month_result = await self.db.execute(month_query)
        this_month = month_result.scalar() or 0

        # Today
        today_query = (
            select(func.count())
            .select_from(Inspection)
            .where(Inspection.date == date.today())
        )
        if jurisdiction_filter is not None:
            today_query = today_query.where(jurisdiction_filter)
        today_result = await self.db.execute(today_query)
        today = today_result.scalar() or 0

        # Unique villages inspected
        villages_query = select(
            func.count(func.distinct(Inspection.village_id))
        ).select_from(Inspection)
        if jurisdiction_filter is not None:
            villages_query = villages_query.where(jurisdiction_filter)
        villages_result = await self.db.execute(villages_query)
        villages = villages_result.scalar() or 0

        return {
            "total_inspections": total,
            "inspections_this_month": this_month,
            "inspections_today": today,
            "villages_inspected": villages,
        }
