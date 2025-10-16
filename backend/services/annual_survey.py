"""
Annual Survey Service
Handles business logic for annual survey management
"""

from typing import Any, List, Optional, Tuple, Dict
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.orm import selectinload

from models.database.survey_master import (
    AnnualSurvey,
    WorkOrderDetails,
    FundSanctioned,
    DoorToDoorCollectionDetails,
    RoadSweepingDetails,
    DrainCleaningDetails,
    CSCDetails,
    SWMAssets,
    SBMGYearTargets,
    VillageData,
    VillageSBMGAssets,
    VillageGWMAssets,
)
from models.database.auth import User, PositionHolder
from models.database.geography import Block, District, GramPanchayat
from models.requests.survey import (
    CreateAnnualSurveyRequest,
    UpdateAnnualSurveyRequest,
)
from auth_utils import UserRole


class AnnualSurveyService:
    """Service for managing annual surveys."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_active_position(self, user: User) -> Optional[PositionHolder]:
        """Get the active position of the user."""
        # Get the first active position
        for position in user.positions:
            return position
        return None

    async def can_survey_gp(self, user: User, gp_id: int) -> bool:
        """Check if user can survey a GP based on their jurisdiction."""
        # Get GP details
        result = await self.db.execute(
            select(GramPanchayat)
            .options(
                selectinload(GramPanchayat.block), selectinload(GramPanchayat.district)
            )
            .where(GramPanchayat.id == gp_id)
        )
        gp = result.scalar_one_or_none()

        if not gp:
            return False

        # Check user's jurisdiction
        for position in user.positions:
            role_name = position.role.name

            # Admin and SuperAdmin can survey anywhere
            if role_name in [UserRole.ADMIN, UserRole.SUPERADMIN]:
                return True

            # CEO can survey in their district
            if role_name == UserRole.CEO and position.district_id == gp.district_id:
                return True

            # BDO can survey in their block
            if role_name == UserRole.BDO and position.block_id == gp.block_id:
                return True

            # VDO can survey in their village/GP
            if role_name == UserRole.VDO and position.village_id == gp_id:
                return True

            # Worker can survey in their assigned area
            if role_name == UserRole.WORKER:
                if position.village_id == gp_id:
                    return True
                if position.block_id == gp.block_id:
                    return True
                if position.district_id == gp.district_id:
                    return True

        return False

    async def create_survey(
        self, user: User, request: CreateAnnualSurveyRequest
    ) -> AnnualSurvey:
        """Create a new annual survey."""
        # Get active position
        position = await self.get_user_active_position(user)
        if not position:
            raise ValueError("User does not have an active position")

        # Check if user can survey this GP
        if not await self.can_survey_gp(user, request.gp_id):
            raise ValueError("User does not have jurisdiction to survey this GP")

        # Get GP details to validate
        result = await self.db.execute(
            select(GramPanchayat).where(GramPanchayat.id == request.gp_id)
        )
        gp = result.scalar_one_or_none()
        if not gp:
            raise ValueError("Gram Panchayat not found")

        # Create annual survey
        survey = AnnualSurvey(
            gp_id=request.gp_id,
            survey_date=request.survey_date or date.today(),
            surveyed_by_id=position.id,
            vdo_name=request.vdo_name,
            vdo_contact=request.vdo_contact,
            sarpanch_name=request.sarpanch_name,
            sarpanch_contact=request.sarpanch_contact,
            num_ward_panchs=request.num_ward_panchs,
            bidder_name=request.bidder_name,
        )

        self.db.add(survey)
        await self.db.flush()  # Get the survey ID

        # Create work order details if provided
        if request.work_order:
            work_order = WorkOrderDetails(
                id=survey.id,
                work_order_no=request.work_order.work_order_no,
                work_order_date=request.work_order.work_order_date,
                work_order_amount=request.work_order.work_order_amount,
            )
            self.db.add(work_order)

        # Create fund sanctioned if provided
        if request.fund_sanctioned:
            fund = FundSanctioned(
                id=survey.id,
                amount=request.fund_sanctioned.amount,
                head=request.fund_sanctioned.head,
            )
            self.db.add(fund)

        # Create door to door collection details if provided
        if request.door_to_door_collection:
            dtd = DoorToDoorCollectionDetails(
                id=survey.id,
                num_households=request.door_to_door_collection.num_households,
                num_shops=request.door_to_door_collection.num_shops,
                collection_frequency=request.door_to_door_collection.collection_frequency,
            )
            self.db.add(dtd)

        # Create road sweeping details if provided
        if request.road_sweeping:
            road = RoadSweepingDetails(
                id=survey.id,
                width=request.road_sweeping.width,
                length=request.road_sweeping.length,
                cleaning_frequency=request.road_sweeping.cleaning_frequency,
            )
            self.db.add(road)

        # Create drain cleaning details if provided
        if request.drain_cleaning:
            drain = DrainCleaningDetails(
                id=survey.id,
                length=request.drain_cleaning.length,
                cleaning_frequency=request.drain_cleaning.cleaning_frequency,
            )
            self.db.add(drain)

        # Create CSC details if provided
        if request.csc_details:
            csc = CSCDetails(
                id=survey.id,
                numbers=request.csc_details.numbers,
                cleaning_frequency=request.csc_details.cleaning_frequency,
            )
            self.db.add(csc)

        # Create SWM assets if provided
        if request.swm_assets:
            swm = SWMAssets(
                id=survey.id,
                rrc=request.swm_assets.rrc,
                pwmu=request.swm_assets.pwmu,
                compost_pit=request.swm_assets.compost_pit,
                collection_vehicle=request.swm_assets.collection_vehicle,
            )
            self.db.add(swm)

        # Create SBMG targets if provided
        if request.sbmg_targets:
            targets = SBMGYearTargets(
                id=survey.id,
                ihhl=request.sbmg_targets.ihhl,
                csc=request.sbmg_targets.csc,
                rrc=request.sbmg_targets.rrc,
                pwmu=request.sbmg_targets.pwmu,
                soak_pit=request.sbmg_targets.soak_pit,
                magic_pit=request.sbmg_targets.magic_pit,
                leach_pit=request.sbmg_targets.leach_pit,
                wsp=request.sbmg_targets.wsp,
                dewats=request.sbmg_targets.dewats,
            )
            self.db.add(targets)

        # Create village data if provided
        if request.village_data:
            for village_req in request.village_data:
                village = VillageData(
                    survey_id=survey.id,
                    village_name=village_req.village_name,
                    population=village_req.population,
                    num_households=village_req.num_households,
                )
                self.db.add(village)
                await self.db.flush()  # Get village data ID

                # Create village SBMG assets if provided
                if village_req.sbmg_assets:
                    sbmg_assets = VillageSBMGAssets(
                        id=village.id,
                        ihhl=village_req.sbmg_assets.ihhl,
                        csc=village_req.sbmg_assets.csc,
                    )
                    self.db.add(sbmg_assets)

                # Create village GWM assets if provided
                if village_req.gwm_assets:
                    gwm_assets = VillageGWMAssets(
                        id=village.id,
                        soak_pit=village_req.gwm_assets.soak_pit,
                        magic_pit=village_req.gwm_assets.magic_pit,
                        leach_pit=village_req.gwm_assets.leach_pit,
                        wsp=village_req.gwm_assets.wsp,
                        dewats=village_req.gwm_assets.dewats,
                    )
                    self.db.add(gwm_assets)

        await self.db.commit()
        await self.db.refresh(survey)

        return survey

    async def get_survey_by_id(self, survey_id: int) -> Optional[AnnualSurvey]:
        """Get annual survey by ID with all related data."""
        result = await self.db.execute(
            select(AnnualSurvey)
            .options(
                selectinload(AnnualSurvey.gp).selectinload(GramPanchayat.block),
                selectinload(AnnualSurvey.gp).selectinload(GramPanchayat.district),
                selectinload(AnnualSurvey.work_order),
                selectinload(AnnualSurvey.fund_sanctioned),
                selectinload(AnnualSurvey.door_to_door_collection),
                selectinload(AnnualSurvey.road_sweeping),
                selectinload(AnnualSurvey.drain_cleaning),
                selectinload(AnnualSurvey.csc_details),
                selectinload(AnnualSurvey.swm_assets),
                selectinload(AnnualSurvey.sbmg_targets),
                selectinload(AnnualSurvey.village_data).selectinload(
                    VillageData.sbmg_assets
                ),
                selectinload(AnnualSurvey.village_data).selectinload(
                    VillageData.gwm_assets
                ),
            )
            .where(AnnualSurvey.id == survey_id)
        )
        return result.scalar_one_or_none()

    async def get_surveys_list(
        self,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        gp_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> Tuple[List[AnnualSurvey], int]:
        """Get paginated list of surveys with filters."""
        # Build base query
        query = (
            select(AnnualSurvey)
            .join(GramPanchayat, AnnualSurvey.gp_id == GramPanchayat.id)
            .join(Block, GramPanchayat.block_id == Block.id)
            .join(District, Block.district_id == District.id)
            .options(
                selectinload(AnnualSurvey.gp).selectinload(GramPanchayat.block),
                selectinload(AnnualSurvey.gp).selectinload(GramPanchayat.district),
                selectinload(AnnualSurvey.village_data),
            )
        )

        if gp_id:
            query = query.where(AnnualSurvey.gp_id == gp_id)
        elif block_id:
            query = query.where(Block.id == block_id)
        elif district_id:
            query = query.where(District.id == district_id)

        if start_date:
            query = query.where(AnnualSurvey.survey_date >= start_date)
        if end_date:
            query = query.where(AnnualSurvey.survey_date <= end_date)

        # Get total count
        count_query = select(func.count()).select_from(AnnualSurvey)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        query = query.order_by(AnnualSurvey.survey_date.desc())
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        surveys = result.scalars().all()

        return list(surveys), total

    async def update_survey(
        self, survey_id: int, user: User, request: UpdateAnnualSurveyRequest
    ) -> AnnualSurvey:
        """Update an existing annual survey."""
        # Get existing survey
        survey = await self.get_survey_by_id(survey_id)
        if not survey:
            raise ValueError("Survey not found")

        # Check if user can survey this GP
        if not await self.can_survey_gp(user, survey.gp_id):
            raise ValueError("User does not have jurisdiction to update this survey")

        # Update basic fields
        if request.survey_date is not None:
            survey.survey_date = request.survey_date
        if request.vdo_name is not None:
            survey.vdo_name = request.vdo_name
        if request.vdo_contact is not None:
            survey.vdo_contact = request.vdo_contact
        if request.sarpanch_name is not None:
            survey.sarpanch_name = request.sarpanch_name
        if request.sarpanch_contact is not None:
            survey.sarpanch_contact = request.sarpanch_contact
        if request.num_ward_panchs is not None:
            survey.num_ward_panchs = request.num_ward_panchs
        if request.bidder_name is not None:
            survey.bidder_name = request.bidder_name

        # Update or create work order details
        if request.work_order is not None:
            if survey.work_order:
                survey.work_order.work_order_no = request.work_order.work_order_no
                survey.work_order.work_order_date = request.work_order.work_order_date
                survey.work_order.work_order_amount = (
                    request.work_order.work_order_amount
                )
            else:
                work_order = WorkOrderDetails(
                    id=survey.id,
                    work_order_no=request.work_order.work_order_no,
                    work_order_date=request.work_order.work_order_date,
                    work_order_amount=request.work_order.work_order_amount,
                )
                self.db.add(work_order)

        # Update or create fund sanctioned
        if request.fund_sanctioned is not None:
            if survey.fund_sanctioned:
                survey.fund_sanctioned.amount = request.fund_sanctioned.amount
                survey.fund_sanctioned.head = request.fund_sanctioned.head
            else:
                fund = FundSanctioned(
                    id=survey.id,
                    amount=request.fund_sanctioned.amount,
                    head=request.fund_sanctioned.head,
                )
                self.db.add(fund)

        # Similar updates for other sub-sections...
        if request.door_to_door_collection is not None:
            if survey.door_to_door_collection:
                survey.door_to_door_collection.num_households = (
                    request.door_to_door_collection.num_households
                )
                survey.door_to_door_collection.num_shops = (
                    request.door_to_door_collection.num_shops
                )
                survey.door_to_door_collection.collection_frequency = (
                    request.door_to_door_collection.collection_frequency
                )
            else:
                dtd = DoorToDoorCollectionDetails(
                    id=survey.id,
                    num_households=request.door_to_door_collection.num_households,
                    num_shops=request.door_to_door_collection.num_shops,
                    collection_frequency=request.door_to_door_collection.collection_frequency,
                )
                self.db.add(dtd)

        if request.road_sweeping is not None:
            if survey.road_sweeping:
                survey.road_sweeping.width = request.road_sweeping.width
                survey.road_sweeping.length = request.road_sweeping.length
                survey.road_sweeping.cleaning_frequency = (
                    request.road_sweeping.cleaning_frequency
                )
            else:
                road = RoadSweepingDetails(
                    id=survey.id,
                    width=request.road_sweeping.width,
                    length=request.road_sweeping.length,
                    cleaning_frequency=request.road_sweeping.cleaning_frequency,
                )
                self.db.add(road)

        if request.drain_cleaning is not None:
            if survey.drain_cleaning:
                survey.drain_cleaning.length = request.drain_cleaning.length
                survey.drain_cleaning.cleaning_frequency = (
                    request.drain_cleaning.cleaning_frequency
                )
            else:
                drain = DrainCleaningDetails(
                    id=survey.id,
                    length=request.drain_cleaning.length,
                    cleaning_frequency=request.drain_cleaning.cleaning_frequency,
                )
                self.db.add(drain)

        if request.csc_details is not None:
            if survey.csc_details:
                survey.csc_details.numbers = request.csc_details.numbers
                survey.csc_details.cleaning_frequency = (
                    request.csc_details.cleaning_frequency
                )
            else:
                csc = CSCDetails(
                    id=survey.id,
                    numbers=request.csc_details.numbers,
                    cleaning_frequency=request.csc_details.cleaning_frequency,
                )
                self.db.add(csc)

        if request.swm_assets is not None:
            if survey.swm_assets:
                survey.swm_assets.rrc = request.swm_assets.rrc
                survey.swm_assets.pwmu = request.swm_assets.pwmu
                survey.swm_assets.compost_pit = request.swm_assets.compost_pit
                survey.swm_assets.collection_vehicle = (
                    request.swm_assets.collection_vehicle
                )
            else:
                swm = SWMAssets(
                    id=survey.id,
                    rrc=request.swm_assets.rrc,
                    pwmu=request.swm_assets.pwmu,
                    compost_pit=request.swm_assets.compost_pit,
                    collection_vehicle=request.swm_assets.collection_vehicle,
                )
                self.db.add(swm)

        if request.sbmg_targets is not None:
            if survey.sbmg_targets:
                survey.sbmg_targets.ihhl = request.sbmg_targets.ihhl
                survey.sbmg_targets.csc = request.sbmg_targets.csc
                survey.sbmg_targets.rrc = request.sbmg_targets.rrc
                survey.sbmg_targets.pwmu = request.sbmg_targets.pwmu
                survey.sbmg_targets.soak_pit = request.sbmg_targets.soak_pit
                survey.sbmg_targets.magic_pit = request.sbmg_targets.magic_pit
                survey.sbmg_targets.leach_pit = request.sbmg_targets.leach_pit
                survey.sbmg_targets.wsp = request.sbmg_targets.wsp
                survey.sbmg_targets.dewats = request.sbmg_targets.dewats
            else:
                targets = SBMGYearTargets(
                    id=survey.id,
                    ihhl=request.sbmg_targets.ihhl,
                    csc=request.sbmg_targets.csc,
                    rrc=request.sbmg_targets.rrc,
                    pwmu=request.sbmg_targets.pwmu,
                    soak_pit=request.sbmg_targets.soak_pit,
                    magic_pit=request.sbmg_targets.magic_pit,
                    leach_pit=request.sbmg_targets.leach_pit,
                    wsp=request.sbmg_targets.wsp,
                    dewats=request.sbmg_targets.dewats,
                )
                self.db.add(targets)

        # Update village data - delete existing and recreate
        if request.village_data is not None:
            # Delete existing village data
            await self.db.execute(
                delete(VillageData).where(VillageData.survey_id == survey.id)
            )
            await self.db.flush()

            # Create new village data
            for village_req in request.village_data:
                village = VillageData(
                    survey_id=survey.id,
                    village_name=village_req.village_name,
                    population=village_req.population,
                    num_households=village_req.num_households,
                )
                self.db.add(village)
                await self.db.flush()

                if village_req.sbmg_assets:
                    sbmg_assets = VillageSBMGAssets(
                        id=village.id,
                        ihhl=village_req.sbmg_assets.ihhl,
                        csc=village_req.sbmg_assets.csc,
                    )
                    self.db.add(sbmg_assets)

                if village_req.gwm_assets:
                    gwm_assets = VillageGWMAssets(
                        id=village.id,
                        soak_pit=village_req.gwm_assets.soak_pit,
                        magic_pit=village_req.gwm_assets.magic_pit,
                        leach_pit=village_req.gwm_assets.leach_pit,
                        wsp=village_req.gwm_assets.wsp,
                        dewats=village_req.gwm_assets.dewats,
                    )
                    self.db.add(gwm_assets)

        survey.updated_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(survey)

        return survey

    async def delete_survey(self, survey_id: int, user: User) -> bool:
        """Delete an annual survey."""
        survey = await self.get_survey_by_id(survey_id)
        if not survey:
            raise ValueError("Survey not found")

        # Check if user can survey this GP
        if not await self.can_survey_gp(user, survey.gp_id):
            raise ValueError("User does not have jurisdiction to delete this survey")

        await self.db.delete(survey)
        await self.db.commit()
        return True

    async def get_survey_statistics(
        self,
        user: User,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        gp_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Get survey statistics."""
        # Build base query
        query = select(AnnualSurvey).options(
            selectinload(AnnualSurvey.village_data).selectinload(
                VillageData.sbmg_assets
            ),
            selectinload(AnnualSurvey.village_data).selectinload(
                VillageData.gwm_assets
            ),
            selectinload(AnnualSurvey.sbmg_targets),
        )

        # Apply jurisdiction filter

        # Apply additional filters
        filters = []

        if gp_id:
            filters.append(AnnualSurvey.gp_id == gp_id)
        elif block_id:
            filters.append(
                AnnualSurvey.gp_id.in_(
                    select(GramPanchayat.id).where(GramPanchayat.block_id == block_id)
                )
            )
        elif district_id:
            filters.append(
                AnnualSurvey.gp_id.in_(
                    select(GramPanchayat.id).where(
                        GramPanchayat.district_id == district_id
                    )
                )
            )

        if start_date:
            filters.append(AnnualSurvey.survey_date >= start_date)
        if end_date:
            filters.append(AnnualSurvey.survey_date <= end_date)

        if filters:
            query = query.where(and_(*filters))

        # Execute query
        result = await self.db.execute(query)
        surveys = result.scalars().all()

        # Calculate statistics
        total_surveys = len(surveys)
        gp_ids = set()
        total_villages = 0
        total_population = 0
        total_households = 0

        # Asset totals
        total_ihhl = 0
        total_csc = 0
        total_rrc = 0
        total_pwmu = 0
        total_soak_pit = 0
        total_magic_pit = 0
        total_leach_pit = 0
        total_wsp = 0
        total_dewats = 0

        for survey in surveys:
            gp_ids.add(survey.gp_id)

            if survey.village_data:
                total_villages += len(survey.village_data)
                for village in survey.village_data:
                    if village.population:
                        total_population += village.population
                    if village.num_households:
                        total_households += village.num_households

                    if village.sbmg_assets:
                        if village.sbmg_assets.ihhl:
                            total_ihhl += village.sbmg_assets.ihhl
                        if village.sbmg_assets.csc:
                            total_csc += village.sbmg_assets.csc

                    if village.gwm_assets:
                        if village.gwm_assets.soak_pit:
                            total_soak_pit += village.gwm_assets.soak_pit
                        if village.gwm_assets.magic_pit:
                            total_magic_pit += village.gwm_assets.magic_pit
                        if village.gwm_assets.leach_pit:
                            total_leach_pit += village.gwm_assets.leach_pit
                        if village.gwm_assets.wsp:
                            total_wsp += village.gwm_assets.wsp
                        if village.gwm_assets.dewats:
                            total_dewats += village.gwm_assets.dewats

        return {
            "total_surveys": total_surveys,
            "total_gps_surveyed": len(gp_ids),
            "total_villages_covered": total_villages,
            "total_population_covered": total_population,
            "total_households_covered": total_households,
            "total_ihhl": total_ihhl,
            "total_csc": total_csc,
            "total_rrc": total_rrc,
            "total_pwmu": total_pwmu,
            "total_soak_pit": total_soak_pit,
            "total_magic_pit": total_magic_pit,
            "total_leach_pit": total_leach_pit,
            "total_wsp": total_wsp,
            "total_dewats": total_dewats,
        }
