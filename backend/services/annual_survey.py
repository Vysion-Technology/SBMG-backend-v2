"""
Annual Survey Service
Handles business logic for annual survey management
"""

from typing import List, Optional
from datetime import date
import random

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, delete
from sqlalchemy.orm import selectinload

from services.auth import AuthService

from models.response.auth import PositionHolderResponse
from models.response.annual_survey import AnnualSurveyFYResponse, AnnualSurveyResponse
from models.database.survey_master import (
    AnnualSurvey,
    AnnualSurveyFY,
    FundHead,
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
    CollectionFrequency,
    CleaningFrequency,
)
from models.database.auth import PositionHolder, User
from models.database.geography import Block, District, GramPanchayat
from models.requests.survey import (
    CreateAnnualSurveyRequest,
)


def get_response_model_from_survey(
    survey: AnnualSurvey,
) -> AnnualSurveyResponse:
    """Convert AnnualSurvey model to AnnualSurveyResponse."""
    return AnnualSurveyResponse(
        id=survey.id,
        fy_id=survey.fy_id,
        gp_id=survey.gp_id,
        survey_date=survey.survey_date,
        vdo_id=survey.vdo_id,
        gp_name=survey.gp.name,
        block_name=survey.gp.block.name,
        district_name=survey.gp.district.name,
        sarpanch_name=survey.sarpanch_name or "",
        sarpanch_contact=survey.sarpanch_contact or "",
        num_ward_panchs=survey.num_ward_panchs or 0,
        agency_id=survey.agency_id,
        vdo=PositionHolderResponse(
            id=survey.vdo.id,
            user_id=survey.vdo.user_id,
            first_name=survey.vdo.first_name,
            middle_name=survey.vdo.middle_name,
            last_name=survey.vdo.last_name,
            username=survey.vdo.user.username,
        ),
        created_at=survey.created_at,
        updated_at=survey.updated_at,
        work_order=survey.work_order,
        fund_sanctioned=survey.fund_sanctioned,
        door_to_door_collection=survey.door_to_door_collection,
        road_sweeping=survey.road_sweeping,
        drain_cleaning=survey.drain_cleaning,
        csc_details=survey.csc_details,
        swm_assets=survey.swm_assets,
        sbmg_targets=survey.sbmg_targets,
        village_data=survey.village_data,  # type: ignore
    )


class AnnualSurveyService:
    """Service for managing annual surveys."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def vdo_fills_the_survey(self, user: User, request: CreateAnnualSurveyRequest) -> AnnualSurveyResponse:
        """Create a new annual survey."""
        # Get active position
        position = await AuthService.get_user_active_position(user)
        if not position:
            raise ValueError("User does not have an active position")

        # Get GP details to validate
        result = await self.db.execute(
            select(GramPanchayat)
            .options(
                selectinload(GramPanchayat.block),
                selectinload(GramPanchayat.district),
            )
            .where(GramPanchayat.id == request.gp_id)
        )
        gp = result.scalar_one_or_none()
        if not gp:
            raise ValueError("Gram Panchayat not found")

        # Create annual survey

        survey = (
            await self.db.execute(
                insert(AnnualSurvey)
                .values(
                    fy_id=request.fy_id,
                    gp_id=request.gp_id,
                    survey_date=date.today(),
                    vdo_id=position.id,
                    sarpanch_name=request.sarpanch_name,
                    sarpanch_contact=request.sarpanch_contact,
                    num_ward_panchs=request.num_ward_panchs,
                    agency_id=1,
                )
                .returning(AnnualSurvey)
            )
        ).scalar_one()

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
                    village_id=village_req.village_id,
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

        return AnnualSurveyResponse(
            id=survey.id,
            fy_id=survey.fy_id,
            gp_id=survey.gp_id,
            survey_date=survey.survey_date,
            vdo_id=survey.vdo_id,
            gp_name=gp.name,
            block_name=gp.block.name,
            district_name=gp.district.name,
            sarpanch_name=survey.sarpanch_name or "",
            sarpanch_contact=survey.sarpanch_contact or "",
            num_ward_panchs=survey.num_ward_panchs or 0,
            agency_id=survey.agency_id,
            vdo=None,
            created_at=survey.created_at,
            updated_at=survey.updated_at,
        )

    async def get_survey_by_id(self, survey_id: int) -> Optional[AnnualSurveyResponse]:
        """Get annual survey by ID with all related data."""
        result = await self.db.execute(
            select(AnnualSurvey)
            .options(
                selectinload(AnnualSurvey.gp).selectinload(GramPanchayat.block),
                selectinload(AnnualSurvey.gp).selectinload(GramPanchayat.district),
                # eager-load both the linked User and Employee for the VDO/position holder
                selectinload(AnnualSurvey.vdo).selectinload(PositionHolder.user),
                selectinload(AnnualSurvey.vdo).selectinload(PositionHolder.employee),
                selectinload(AnnualSurvey.work_order),
                selectinload(AnnualSurvey.fund_sanctioned),
                selectinload(AnnualSurvey.door_to_door_collection),
                selectinload(AnnualSurvey.road_sweeping),
                selectinload(AnnualSurvey.drain_cleaning),
                selectinload(AnnualSurvey.csc_details),
                selectinload(AnnualSurvey.swm_assets),
                selectinload(AnnualSurvey.sbmg_targets),
                selectinload(AnnualSurvey.village_data).selectinload(VillageData.sbmg_assets),
                selectinload(AnnualSurvey.village_data).selectinload(VillageData.gwm_assets),
            )
            .where(AnnualSurvey.id == survey_id)
        )
        resp = get_response_model_from_survey(result.scalar_one_or_none())
        return resp

    async def get_surveys_list(
        self,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        gp_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> List[AnnualSurveyResponse]:
        """Get paginated list of surveys with filters."""
        # Build base query
        query = select(AnnualSurvey).options(
            selectinload(AnnualSurvey.gp).selectinload(GramPanchayat.block),
            selectinload(AnnualSurvey.gp).selectinload(GramPanchayat.district),
            # eager-load both the linked User and Employee for the VDO/position holder
            selectinload(AnnualSurvey.vdo).selectinload(PositionHolder.user),
            selectinload(AnnualSurvey.vdo).selectinload(PositionHolder.employee),
            selectinload(AnnualSurvey.work_order),
            selectinload(AnnualSurvey.fund_sanctioned),
            selectinload(AnnualSurvey.door_to_door_collection),
            selectinload(AnnualSurvey.road_sweeping),
            selectinload(AnnualSurvey.drain_cleaning),
            selectinload(AnnualSurvey.csc_details),
            selectinload(AnnualSurvey.swm_assets),
            selectinload(AnnualSurvey.sbmg_targets),
            selectinload(AnnualSurvey.village_data).selectinload(VillageData.sbmg_assets),
            selectinload(AnnualSurvey.village_data).selectinload(VillageData.gwm_assets),
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

        # Apply pagination
        query = query.order_by(AnnualSurvey.survey_date.desc())
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        surveys = result.scalars().all()

        return [get_response_model_from_survey(survey) for survey in surveys]

    async def delete_survey(self, survey_id: int) -> bool:
        """Delete an annual survey."""
        await self.db.execute(delete(AnnualSurvey).where(AnnualSurvey.id == survey_id))
        await self.db.commit()
        return True

    async def get_active_financial_years(self) -> List[AnnualSurveyFYResponse]:
        """Get list of active financial years from surveys."""
        result = await self.db.execute(select(AnnualSurveyFY).where(AnnualSurveyFY.active.is_(True)))
        fys = result.scalars().all()
        return [AnnualSurveyFYResponse.model_validate(fy) for fy in fys]

    async def get_latest_survey_by_gp(self, gp_id: int) -> Optional[AnnualSurveyResponse]:
        """Get the latest survey for a given Gram Panchayat."""
        result = await self.db.execute(
            select(AnnualSurvey)
            .options(
                selectinload(AnnualSurvey.gp).selectinload(GramPanchayat.block),
                selectinload(AnnualSurvey.gp).selectinload(GramPanchayat.district),
                # eager-load both the linked User and Employee for the VDO/position holder
                selectinload(AnnualSurvey.vdo).selectinload(PositionHolder.user),
                selectinload(AnnualSurvey.vdo).selectinload(PositionHolder.employee),
                selectinload(AnnualSurvey.work_order),
                selectinload(AnnualSurvey.fund_sanctioned),
                selectinload(AnnualSurvey.door_to_door_collection),
                selectinload(AnnualSurvey.road_sweeping),
                selectinload(AnnualSurvey.drain_cleaning),
                selectinload(AnnualSurvey.csc_details),
                selectinload(AnnualSurvey.swm_assets),
                selectinload(AnnualSurvey.sbmg_targets),
                selectinload(AnnualSurvey.village_data).selectinload(VillageData.sbmg_assets),
                selectinload(AnnualSurvey.village_data).selectinload(VillageData.gwm_assets),
            )
            .where(AnnualSurvey.gp_id == gp_id)
            .order_by(AnnualSurvey.survey_date.desc())
            .limit(1)
        )
        survey = result.scalar_one_or_none()
        if survey:
            return get_response_model_from_survey(survey)
        return None

    async def fill_annual_survey_bulk(
        self,
        fy_id: int,
        vdo_list: List[User],
        gp_villages_map: dict[int, List[int]],
    ) -> None:
        """Fill annual survey for all Gram Panchayats with random data in batches of 100."""
        gp_ids = sorted(list(gp_villages_map.keys()))
        vdo_list = sorted(vdo_list, key=lambda vdo: vdo.gp_id or 0)
        vdo_ids = [vdo.id for vdo in vdo_list]

        assert len(gp_ids) == len(vdo_ids), "Number of GPs and VDOs must be the same for bulk filling."

        batch_size = 100
        for i in range(0, len(gp_ids), batch_size):
            batch_gp_ids = gp_ids[i : i + batch_size]
            batch_vdo_ids = vdo_ids[i : i + batch_size]
            surveys = await self.db.execute(
                insert(AnnualSurvey)
                .returning(AnnualSurvey)
                .values([
                    {
                        "fy_id": fy_id,
                        "gp_id": gp_id,
                        "survey_date": date.today(),
                        "vdo_id": batch_vdo_ids[idx],
                        "sarpanch_name": f"Sarpanch {gp_id}",
                        "sarpanch_contact": f"90000000{gp_id % 10}",
                        "num_ward_panchs": random.randint(5, 15),
                        "agency_id": 1,
                    }
                    for idx, gp_id in enumerate(batch_gp_ids)
                ])
            )
            await self.db.commit()
            # Fill other related data as well for all related tables compulsorily
            surveys_list = surveys.scalars().all()
            # Process related survey data sequentially to avoid concurrent use of the same AsyncSession.
            # Concurrent operations on the same AsyncSession are not permitted and were causing
            # `InvalidRequestError: This session is provisioning a new connection; concurrent operations are not permitted`.
            for survey in surveys_list:
                await self._fill_related_survey_data(survey, gp_villages_map[survey.gp_id])
            # Ensure any remaining pending changes are committed
            await self.db.commit()

    async def _fill_related_survey_data(self, survey: AnnualSurvey, village_ids: List[int]) -> None:
        """Fill related data for a given survey."""
        work_order = WorkOrderDetails(
            id=survey.id,
            work_order_no=f"WO-{survey.gp_id}-{survey.id}",
            work_order_date=date.today(),
            work_order_amount=random.randint(100000, 500000),
        )
        self.db.add(work_order)

        fund = FundSanctioned(
            id=survey.id,
            amount=random.randint(50000, 200000),
            head=random.choice(list(FundHead)),
        )
        self.db.add(fund)

        dtd = DoorToDoorCollectionDetails(
            id=survey.id,
            num_households=random.randint(100, 500),
            num_shops=random.randint(10, 50),
            collection_frequency=random.choice(list(CollectionFrequency)),
        )
        self.db.add(dtd)

        road = RoadSweepingDetails(
            id=survey.id,
            width=random.uniform(2.0, 5.0),
            length=random.uniform(1000.0, 5000.0),
            cleaning_frequency=random.choice(list(CleaningFrequency)),
        )
        self.db.add(road)

        drain = DrainCleaningDetails(
            id=survey.id,
            length=random.uniform(500.0, 2000.0),
            cleaning_frequency=random.choice(list(CleaningFrequency)),
        )
        self.db.add(drain)

        csc = CSCDetails(
            id=survey.id,
            numbers=random.randint(1, 5),
            cleaning_frequency=random.choice(list(CleaningFrequency)),
        )
        self.db.add(csc)

        swm = SWMAssets(
            id=survey.id,
            rrc=random.randint(1, 3),
            pwmu=random.randint(1, 2),
            compost_pit=random.randint(1, 4),
            collection_vehicle=random.randint(1, 2),
        )
        self.db.add(swm)

        targets = SBMGYearTargets(
            id=survey.id,
            ihhl=random.randint(100, 300),
            csc=random.randint(1, 5),
            rrc=random.randint(1, 3),
            pwmu=random.randint(1, 2),
            soak_pit=random.randint(50, 150),
            magic_pit=random.randint(30, 100),
            leach_pit=random.randint(20, 80),
            wsp=random.randint(1, 3),
            dewats=random.randint(0, 2),
        )

        village_data_entries: List[VillageData] = []
        for village_id in village_ids:
            village_data = VillageData(
                survey_id=survey.id,
                village_id=village_id,
                village_name=f"Village {village_id}",
                population=random.randint(500, 2000),
                num_households=random.randint(100, 500),
            )
            village_data_entries.append(village_data)
            self.db.add(village_data)
            # flush to populate village_data.id without committing the transaction
            await self.db.flush()

            sbmg_assets = VillageSBMGAssets(
                id=village_data.id,
                ihhl=random.randint(50, 150),
                csc=random.randint(1, 5),
            )
            self.db.add(sbmg_assets)

            gwm_assets = VillageGWMAssets(
                id=village_data.id,
                soak_pit=random.randint(20, 80),
                magic_pit=random.randint(10, 50),
                leach_pit=random.randint(5, 30),
                wsp=random.randint(1, 3),
                dewats=random.randint(0, 2),
            )
            self.db.add(gwm_assets)

        # add targets and perform a single commit for the entire survey's related data
        self.db.add(targets)
        await self.db.commit()
