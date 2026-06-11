"""
Annual Survey Service
Handles business logic for annual survey management
"""

from fastapi.exceptions import HTTPException
from fastapi import status
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
    ODFSustainability,
    SWMAssetsCategory,
    LWMAssets,
    PWMUDetails,
    FSMDetails,
    GobardhanProject,
    D2DActivities,
    BartanBank,
    VehicleAssets,
    SBMGYearTargets,
    VillageData,
    VillageSBMGAssets,
    VillageGWMAssets,
    CollectionFrequency,
    CleaningFrequency,
)
from models.database.auth import PositionHolder, User
from models.database.geography import Block, District, GramPanchayat, Village
from models.requests.survey import (
    CreateAnnualSurveyRequest,
    UpdateAnnualSurveyRequest,
)
from models.database.contractor import Agency


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
        vdo_name=survey.vdo_name,
        vdo_contact_number=survey.vdo_contact_number,
        gp_name=survey.gp.name,
        block_name=survey.gp.block.name,
        district_name=survey.gp.district.name,
        sarpanch_name=survey.sarpanch_name or "",
        sarpanch_contact=survey.sarpanch_contact or "",
        num_ward_panchs=survey.num_ward_panchs or 0,
        agency_id=survey.agency_id,
        agency_name=survey.agency.name if getattr(survey, "agency", None) else "",
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
        # Categorized assets
        odf_sustainability=survey.odf_sustainability,
        swm_assets=survey.swm_assets,
        lwm_assets=survey.lwm_assets,
        pwmu_details=survey.pwmu_details,
        fsm_details=survey.fsm_details,
        gobardhan_projects=survey.gobardhan_projects,
        d2d_activities=survey.d2d_activities,
        bartan_bank=survey.bartan_bank,
        vehicle_assets=survey.vehicle_assets,
        
        sbmg_targets=survey.sbmg_targets,
        village_data=survey.village_data,  # type: ignore
    )


class AnnualSurveyService:
    """Service for managing annual surveys."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def vdo_fills_the_survey(
        self, user: User, request: CreateAnnualSurveyRequest
    ) -> AnnualSurveyResponse:
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
                    vdo_name=request.vdo_name,
                    vdo_contact_number=request.vdo_contact_number,
                    sarpanch_name=request.sarpanch_name,
                    sarpanch_contact=request.sarpanch_contact,
                    num_ward_panchs=request.num_ward_panchs,
                    agency_id=request.agency_id,
                )
                .returning(AnnualSurvey)
            )
        ).scalar_one()

        # Create section details if provided
        if request.work_order:
            self.db.add(WorkOrderDetails(
                id=survey.id,
                work_order_no=request.work_order.work_order_no,
                work_order_date=request.work_order.work_order_date,
                work_order_amount=request.work_order.work_order_amount,
            ))

        if request.fund_sanctioned:
            self.db.add(FundSanctioned(
                id=survey.id,
                amount=request.fund_sanctioned.amount,
                head=request.fund_sanctioned.head,
            ))

        if request.door_to_door_collection:
            self.db.add(DoorToDoorCollectionDetails(
                id=survey.id,
                num_households=request.door_to_door_collection.num_households,
                num_shops=request.door_to_door_collection.num_shops,
                collection_frequency=request.door_to_door_collection.collection_frequency,
            ))

        if request.road_sweeping:
            self.db.add(RoadSweepingDetails(
                id=survey.id,
                width=request.road_sweeping.width,
                length=request.road_sweeping.length,
                cleaning_frequency=request.road_sweeping.cleaning_frequency,
            ))

        if request.drain_cleaning:
            self.db.add(DrainCleaningDetails(
                id=survey.id,
                length=request.drain_cleaning.length,
                cleaning_frequency=request.drain_cleaning.cleaning_frequency,
            ))

        if request.csc_details:
            self.db.add(CSCDetails(
                id=survey.id,
                numbers=request.csc_details.numbers,
                cleaning_frequency=request.csc_details.cleaning_frequency,
            ))

        # --- Categorized Assets Creation ---
        
        if request.odf_sustainability:
            self.db.add(ODFSustainability(
                id=survey.id,
                ihhl=request.odf_sustainability.ihhl,
                retrofitting=request.odf_sustainability.retrofitting,
                csc=request.odf_sustainability.csc,
                csc_shala_darpan=request.odf_sustainability.csc_shala_darpan,
            ))

        if request.swm_assets:
            self.db.add(SWMAssetsCategory(
                id=survey.id,
                bins_hh_level=request.swm_assets.bins_hh_level,
                bins_public_places=request.swm_assets.bins_public_places,
                community_compost_pits=request.swm_assets.community_compost_pits,
                hh_compost_pit=request.swm_assets.hh_compost_pit,
                segregation_sheds=request.swm_assets.segregation_sheds,
                tricycles_manual=request.swm_assets.tricycles_manual,
                e_rickshaws=request.swm_assets.e_rickshaws,
                motorized_vehicles=request.swm_assets.motorized_vehicles,
            ))

        if request.lwm_assets:
            self.db.add(LWMAssets(
                id=survey.id,
                pits_hh_level=request.lwm_assets.pits_hh_level,
                community_pits=request.lwm_assets.community_pits,
                wsp=request.lwm_assets.wsp,
                dewats=request.lwm_assets.dewats,
                wetlands=request.lwm_assets.wetlands,
                other_treatments=request.lwm_assets.other_treatments,
                drainage_channels=request.lwm_assets.drainage_channels,
            ))

        if request.pwmu_details:
            self.db.add(PWMUDetails(
                id=survey.id,
                established_pwmu=request.pwmu_details.established_pwmu,
                blocks_covered_pwmu=request.pwmu_details.blocks_covered_pwmu,
                urban_mrfs=request.pwmu_details.urban_mrfs,
                blocks_covered_urban_mrf=request.pwmu_details.blocks_covered_urban_mrf,
            ))

        if request.fsm_details:
            self.db.add(FSMDetails(
                id=survey.id,
                twin_pit_toilets=request.fsm_details.twin_pit_toilets,
                single_pit_toilets=request.fsm_details.single_pit_toilets,
                septic_tank_toilets=request.fsm_details.septic_tank_toilets,
                retrofitted_toilets=request.fsm_details.retrofitted_toilets,
                mechanized_desludging=request.fsm_details.mechanized_desludging,
                fstps_rural=request.fsm_details.fstps_rural,
                fstps_urban=request.fsm_details.fstps_urban,
            ))

        if request.gobardhan_projects:
            self.db.add(GobardhanProject(
                id=survey.id,
                total_sanctioned=request.gobardhan_projects.total_sanctioned,
                total_functional=request.gobardhan_projects.total_functional,
                gas_production=request.gobardhan_projects.gas_production,
            ))

        if request.d2d_activities:
            self.db.add(D2DActivities(
                id=survey.id,
                sanctioned_tender=request.d2d_activities.sanctioned_tender,
                sanctioned_self_gp=request.d2d_activities.sanctioned_self_gp,
                sanctioned_csr_ngo=request.d2d_activities.sanctioned_csr_ngo,
                sanctioned_shg=request.d2d_activities.sanctioned_shg,
                sanctioned_mixed_model=request.d2d_activities.sanctioned_mixed_model,
                total_expenditure=request.d2d_activities.total_expenditure,
                vehicles_deployed=request.d2d_activities.vehicles_deployed,
                persons_deployed=request.d2d_activities.persons_deployed,
                households_covered=request.d2d_activities.households_covered,
                status_start=request.d2d_activities.status_start,
                status_running=request.d2d_activities.status_running,
                status_completed=request.d2d_activities.status_completed,
            ))

        if request.bartan_bank:
            self.db.add(BartanBank(
                id=survey.id,
                established_banks=request.bartan_bank.established_banks,
            ))

        if request.vehicle_assets:
            self.db.add(VehicleAssets(
                id=survey.id,
                owned_tricycles=request.vehicle_assets.owned_tricycles,
                owned_e_rickshaws=request.vehicle_assets.owned_e_rickshaws,
                owned_motorized_vehicles=request.vehicle_assets.owned_motorized_vehicles,
                contractor_tricycles=request.vehicle_assets.contractor_tricycles,
                contractor_e_rickshaws=request.vehicle_assets.contractor_e_rickshaws,
                contractor_motorized_vehicles=request.vehicle_assets.contractor_motorized_vehicles,
            ))

        if request.sbmg_targets:
            self.db.add(SBMGYearTargets(
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
            ))

        # Create village data if provided
        if request.village_data:
            for village_req in request.village_data:
                v_data = VillageData(
                    survey_id=survey.id,
                    village_id=village_req.village_id,
                    village_name=village_req.village_name,
                    population=village_req.population,
                    num_households=village_req.num_households,
                )
                self.db.add(v_data)
                await self.db.flush()  # Get village data ID

                if village_req.sbmg_assets:
                    self.db.add(VillageSBMGAssets(
                        id=v_data.id,
                        ihhl=village_req.sbmg_assets.ihhl,
                        csc=village_req.sbmg_assets.csc,
                    ))

                if village_req.gwm_assets:
                    self.db.add(VillageGWMAssets(
                        id=v_data.id,
                        soak_pit=village_req.gwm_assets.soak_pit,
                        magic_pit=village_req.gwm_assets.magic_pit,
                        leach_pit=village_req.gwm_assets.leach_pit,
                        wsp=village_req.gwm_assets.wsp,
                        dewats=village_req.gwm_assets.dewats,
                    ))

        await self.db.commit()
        return await self.get_survey_by_id(survey.id)

    async def update_survey(
        self, survey_id: int, request: UpdateAnnualSurveyRequest
    ) -> AnnualSurveyResponse:
        """Update an existing annual survey."""
        # Get the existing survey
        result = await self.db.execute(
            select(AnnualSurvey)
            .options(
                selectinload(AnnualSurvey.gp).selectinload(GramPanchayat.block),
                selectinload(AnnualSurvey.gp).selectinload(GramPanchayat.district),
                selectinload(AnnualSurvey.vdo).options(
                    selectinload(PositionHolder.user),
                    selectinload(PositionHolder.role),
                    selectinload(PositionHolder.gp),
                    selectinload(PositionHolder.block),
                    selectinload(PositionHolder.district),
                    selectinload(PositionHolder.employee),
                ),
                selectinload(AnnualSurvey.agency),
                selectinload(AnnualSurvey.work_order),
                selectinload(AnnualSurvey.fund_sanctioned),
                selectinload(AnnualSurvey.door_to_door_collection),
                selectinload(AnnualSurvey.road_sweeping),
                selectinload(AnnualSurvey.drain_cleaning),
                selectinload(AnnualSurvey.csc_details),
                selectinload(AnnualSurvey.odf_sustainability),
                selectinload(AnnualSurvey.swm_assets),
                selectinload(AnnualSurvey.lwm_assets),
                selectinload(AnnualSurvey.pwmu_details),
                selectinload(AnnualSurvey.fsm_details),
                selectinload(AnnualSurvey.gobardhan_projects),
                selectinload(AnnualSurvey.d2d_activities),
                selectinload(AnnualSurvey.bartan_bank),
                selectinload(AnnualSurvey.vehicle_assets),
                selectinload(AnnualSurvey.sbmg_targets),
            )
            .where(AnnualSurvey.id == survey_id)
        )
        survey = result.scalar_one_or_none()
        if not survey:
            raise ValueError("Survey not found")

        # Update main survey fields
        if request.vdo_name is not None:
            survey.vdo_name = request.vdo_name
        if request.vdo_contact_number is not None:
            survey.vdo_contact_number = request.vdo_contact_number
        if request.sarpanch_name is not None:
            survey.sarpanch_name = request.sarpanch_name
        if request.sarpanch_contact is not None:
            survey.sarpanch_contact = request.sarpanch_contact
        if request.num_ward_panchs is not None:
            survey.num_ward_panchs = request.num_ward_panchs
        if request.agency_id is not None:
            survey.agency_id = request.agency_id

        # --- Helper for standard sections ---
        async def upsert_section(model_class, request_data, existing_obj=None):
            if request_data is None:
                return existing_obj
            
            obj = existing_obj
            if not obj:
                # Check if it exists in DB first
                res = await self.db.execute(select(model_class).where(model_class.id == survey_id))
                obj = res.scalar_one_or_none()
            
            if not obj:
                obj = model_class(id=survey_id)
                self.db.add(obj)
            
            for key, value in request_data.model_dump(exclude_unset=True).items():
                setattr(obj, key, value)
            return obj

        # Update core sections
        await upsert_section(WorkOrderDetails, request.work_order, survey.work_order)
        await upsert_section(FundSanctioned, request.fund_sanctioned, survey.fund_sanctioned)
        await upsert_section(DoorToDoorCollectionDetails, request.door_to_door_collection, survey.door_to_door_collection)
        await upsert_section(RoadSweepingDetails, request.road_sweeping, survey.road_sweeping)
        await upsert_section(DrainCleaningDetails, request.drain_cleaning, survey.drain_cleaning)
        await upsert_section(CSCDetails, request.csc_details, survey.csc_details)

        # Update categorized assets
        await upsert_section(ODFSustainability, request.odf_sustainability, survey.odf_sustainability)
        await upsert_section(SWMAssetsCategory, request.swm_assets, survey.swm_assets)
        await upsert_section(LWMAssets, request.lwm_assets, survey.lwm_assets)
        await upsert_section(PWMUDetails, request.pwmu_details, survey.pwmu_details)
        await upsert_section(FSMDetails, request.fsm_details, survey.fsm_details)
        await upsert_section(GobardhanProject, request.gobardhan_projects, survey.gobardhan_projects)
        await upsert_section(D2DActivities, request.d2d_activities, survey.d2d_activities)
        await upsert_section(BartanBank, request.bartan_bank, survey.bartan_bank)
        await upsert_section(VehicleAssets, request.vehicle_assets, survey.vehicle_assets)
        
        await upsert_section(SBMGYearTargets, request.sbmg_targets, survey.sbmg_targets)

        # Final amount validation
        if survey.work_order and survey.fund_sanctioned:
            if (survey.work_order.work_order_amount or 0) > (survey.fund_sanctioned.amount or 0):
                raise ValueError("Work order amount cannot be greater than the fund sanctioned amount")

        # Update village data if provided
        if request.village_data is not None:
            # Validate that all village_ids exist
            requested_village_ids = [v.village_id for v in request.village_data]
            existing_result = await self.db.execute(
                select(Village.id).where(Village.id.in_(requested_village_ids))
            )
            existing_ids = set(existing_result.scalars().all())
            missing_ids = set(requested_village_ids) - existing_ids
            if missing_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid village_id(s): {sorted(missing_ids)}. These do not exist in the villages table.",
                )

            # Delete existing village data and recreate
            village_ids_subquery = select(VillageData.id).where(VillageData.survey_id == survey_id)
            await self.db.execute(delete(VillageGWMAssets).where(VillageGWMAssets.id.in_(village_ids_subquery)))
            await self.db.execute(delete(VillageSBMGAssets).where(VillageSBMGAssets.id.in_(village_ids_subquery)))
            await self.db.execute(delete(VillageData).where(VillageData.survey_id == survey_id))

            for village_req in request.village_data:
                v_data = VillageData(
                    survey_id=survey.id,
                    village_id=village_req.village_id,
                    village_name=village_req.village_name,
                    population=village_req.population,
                    num_households=village_req.num_households,
                )
                self.db.add(v_data)
                await self.db.flush()

                if village_req.sbmg_assets:
                    self.db.add(VillageSBMGAssets(id=v_data.id, **village_req.sbmg_assets.model_dump()))
                if village_req.gwm_assets:
                    self.db.add(VillageGWMAssets(id=v_data.id, **village_req.gwm_assets.model_dump()))

        await self.db.commit()
        return await self.get_survey_by_id(survey.id)

    async def get_survey_by_id(self, survey_id: int) -> Optional[AnnualSurveyResponse]:
        """Get annual survey by ID with all related data."""
        result = await self.db.execute(
            select(AnnualSurvey)
            .options(
                selectinload(AnnualSurvey.gp).selectinload(GramPanchayat.block),
                selectinload(AnnualSurvey.gp).selectinload(GramPanchayat.district),
                selectinload(AnnualSurvey.vdo).options(
                    selectinload(PositionHolder.user),
                    selectinload(PositionHolder.role),
                    selectinload(PositionHolder.gp),
                    selectinload(PositionHolder.block),
                    selectinload(PositionHolder.district),
                    selectinload(PositionHolder.employee),
                ),
                selectinload(AnnualSurvey.agency),
                selectinload(AnnualSurvey.work_order),
                selectinload(AnnualSurvey.fund_sanctioned),
                selectinload(AnnualSurvey.door_to_door_collection),
                selectinload(AnnualSurvey.road_sweeping),
                selectinload(AnnualSurvey.drain_cleaning),
                selectinload(AnnualSurvey.csc_details),
                # New assets
                selectinload(AnnualSurvey.odf_sustainability),
                selectinload(AnnualSurvey.swm_assets),
                selectinload(AnnualSurvey.lwm_assets),
                selectinload(AnnualSurvey.pwmu_details),
                selectinload(AnnualSurvey.fsm_details),
                selectinload(AnnualSurvey.gobardhan_projects),
                selectinload(AnnualSurvey.d2d_activities),
                selectinload(AnnualSurvey.bartan_bank),
                selectinload(AnnualSurvey.vehicle_assets),
                selectinload(AnnualSurvey.sbmg_targets),
                selectinload(AnnualSurvey.village_data).selectinload(VillageData.sbmg_assets),
                selectinload(AnnualSurvey.village_data).selectinload(VillageData.gwm_assets),
            )
            .where(AnnualSurvey.id == survey_id)
        )
        survey = result.scalar_one_or_none()
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Annual Survey has not been filled for this GP yet.",
            )
        return get_response_model_from_survey(survey)

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
        query = select(AnnualSurvey).options(
            selectinload(AnnualSurvey.gp).selectinload(GramPanchayat.block),
            selectinload(AnnualSurvey.gp).selectinload(GramPanchayat.district),
            selectinload(AnnualSurvey.vdo).options(
                selectinload(PositionHolder.user),
                selectinload(PositionHolder.role),
                selectinload(PositionHolder.gp),
                selectinload(PositionHolder.block),
                selectinload(PositionHolder.district),
                selectinload(PositionHolder.employee),
            ),
            selectinload(AnnualSurvey.agency),
            selectinload(AnnualSurvey.work_order),
            selectinload(AnnualSurvey.fund_sanctioned),
            selectinload(AnnualSurvey.door_to_door_collection),
            selectinload(AnnualSurvey.road_sweeping),
            selectinload(AnnualSurvey.drain_cleaning),
            selectinload(AnnualSurvey.csc_details),
            # New assets
            selectinload(AnnualSurvey.odf_sustainability),
            selectinload(AnnualSurvey.swm_assets),
            selectinload(AnnualSurvey.lwm_assets),
            selectinload(AnnualSurvey.pwmu_details),
            selectinload(AnnualSurvey.fsm_details),
            selectinload(AnnualSurvey.gobardhan_projects),
            selectinload(AnnualSurvey.d2d_activities),
            selectinload(AnnualSurvey.bartan_bank),
            selectinload(AnnualSurvey.vehicle_assets),
            selectinload(AnnualSurvey.sbmg_targets),
            selectinload(AnnualSurvey.village_data).selectinload(VillageData.sbmg_assets),
            selectinload(AnnualSurvey.village_data).selectinload(VillageData.gwm_assets),
        )

        if gp_id:
            query = query.where(AnnualSurvey.gp_id == gp_id)
        elif block_id:
            query = query.join(GramPanchayat, AnnualSurvey.gp_id == GramPanchayat.id).where(GramPanchayat.block_id == block_id)
        elif district_id:
            query = query.join(GramPanchayat, AnnualSurvey.gp_id == GramPanchayat.id).where(GramPanchayat.district_id == district_id)

        if start_date:
            query = query.where(AnnualSurvey.survey_date >= start_date)
        if end_date:
            query = query.where(AnnualSurvey.survey_date <= end_date)

        query = query.order_by(AnnualSurvey.survey_date.desc())
        query = query.offset(skip).limit(limit)

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
        result = await self.db.execute(
            select(AnnualSurveyFY).where(AnnualSurveyFY.active.is_(True))
        )
        fys = result.scalars().all()
        return [AnnualSurveyFYResponse.model_validate(fy) for fy in fys]

    async def get_latest_survey_by_gp(
        self, gp_id: int
    ) -> Optional[AnnualSurveyResponse]:
        """Get the latest survey for a given Gram Panchayat."""
        result = await self.db.execute(
            select(AnnualSurvey)
            .options(
                selectinload(AnnualSurvey.gp).selectinload(GramPanchayat.block),
                selectinload(AnnualSurvey.gp).selectinload(GramPanchayat.district),
                selectinload(AnnualSurvey.vdo).options(
                    selectinload(PositionHolder.user),
                    selectinload(PositionHolder.role),
                    selectinload(PositionHolder.gp),
                    selectinload(PositionHolder.block),
                    selectinload(PositionHolder.district),
                    selectinload(PositionHolder.employee),
                ),
                selectinload(AnnualSurvey.agency),
                selectinload(AnnualSurvey.work_order),
                selectinload(AnnualSurvey.fund_sanctioned),
                selectinload(AnnualSurvey.door_to_door_collection),
                selectinload(AnnualSurvey.road_sweeping),
                selectinload(AnnualSurvey.drain_cleaning),
                selectinload(AnnualSurvey.csc_details),
                # New assets
                selectinload(AnnualSurvey.odf_sustainability),
                selectinload(AnnualSurvey.swm_assets),
                selectinload(AnnualSurvey.lwm_assets),
                selectinload(AnnualSurvey.pwmu_details),
                selectinload(AnnualSurvey.fsm_details),
                selectinload(AnnualSurvey.gobardhan_projects),
                selectinload(AnnualSurvey.d2d_activities),
                selectinload(AnnualSurvey.bartan_bank),
                selectinload(AnnualSurvey.vehicle_assets),
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

        assert len(gp_ids) == len(vdo_ids), (
            "Number of GPs and VDOs must be the same for bulk filling."
        )

        batch_size = 100
        for i in range(0, len(gp_ids), batch_size):
            batch_gp_ids = gp_ids[i : i + batch_size]
            batch_vdo_ids = vdo_ids[i : i + batch_size]
            surveys = await self.db.execute(
                insert(AnnualSurvey)
                .returning(AnnualSurvey)
                .values(
                    [
                        {
                            "fy_id": fy_id,
                            "gp_id": gp_id,
                            "survey_date": date.today(),
                            "vdo_id": batch_vdo_ids[idx],
                            "vdo_name": f"VDO {batch_vdo_ids[idx]}",
                            "sarpanch_name": f"Sarpanch {gp_id}",
                            "sarpanch_contact": f"90000000{gp_id % 10}",
                            "num_ward_panchs": random.randint(5, 15),
                            "agency_id": 1,
                        }
                        for idx, gp_id in enumerate(batch_gp_ids)
                    ]
                )
            )
            await self.db.commit()
            surveys_list = surveys.scalars().all()
            for survey in surveys_list:
                await self._fill_related_survey_data(
                    survey, gp_villages_map[survey.gp_id]
                )
            await self.db.commit()

    async def _fill_related_survey_data(
        self, survey: AnnualSurvey, village_ids: List[int]
    ) -> None:
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

        # Fill categorized assets with random data
        self.db.add(ODFSustainability(
            id=survey.id,
            ihhl=random.randint(500, 1500),
            retrofitting=random.randint(100, 500),
            csc=random.randint(5, 20),
            csc_shala_darpan=random.randint(2, 10),
        ))

        self.db.add(SWMAssetsCategory(
            id=survey.id,
            bins_hh_level=random.randint(1000, 5000),
            bins_public_places=random.randint(50, 200),
            community_compost_pits=random.randint(5, 15),
            hh_compost_pit=random.randint(100, 500),
            segregation_sheds=random.randint(1, 3),
            tricycles_manual=random.randint(2, 8),
            e_rickshaws=random.randint(1, 4),
            motorized_vehicles=random.randint(1, 2),
        ))

        self.db.add(LWMAssets(
            id=survey.id,
            pits_hh_level=random.randint(500, 2000),
            community_pits=random.randint(10, 50),
            wsp=random.randint(1, 5),
            dewats=random.randint(1, 3),
            wetlands=random.randint(0, 2),
            other_treatments=random.randint(0, 5),
            drainage_channels=random.randint(1000, 5000),
        ))

        self.db.add(PWMUDetails(
            id=survey.id,
            established_pwmu=random.randint(0, 1),
            blocks_covered_pwmu=random.randint(0, 5),
            urban_mrfs=random.randint(0, 2),
            blocks_covered_urban_mrf=random.randint(0, 3),
        ))

        self.db.add(FSMDetails(
            id=survey.id,
            twin_pit_toilets=random.randint(100, 500),
            single_pit_toilets=random.randint(50, 200),
            septic_tank_toilets=random.randint(200, 800),
            retrofitted_toilets=random.randint(10, 50),
            mechanized_desludging=random.randint(1, 5),
            fstps_rural=random.randint(0, 1),
            fstps_urban=random.randint(0, 1),
        ))

        self.db.add(GobardhanProject(
            id=survey.id,
            total_sanctioned=random.randint(1, 5),
            total_functional=random.randint(0, 3),
            gas_production=float(random.randint(10, 100)),
        ))

        self.db.add(D2DActivities(
            id=survey.id,
            is_active=random.choice([True, False]),
            sanctioned_tender=random.randint(0, 5),
            sanctioned_self_gp=random.randint(0, 5),
            sanctioned_csr_ngo=random.randint(0, 2),
            sanctioned_shg=random.randint(0, 3),
            sanctioned_mixed_model=random.randint(0, 2),
            total_expenditure=float(random.randint(50000, 200000)),
            vehicles_deployed=random.randint(1, 5),
            persons_deployed=random.randint(2, 10),
            households_covered=random.randint(500, 2000),
            status_start=random.randint(1, 5),
            status_running=random.randint(1, 5),
            status_completed=random.randint(1, 5),
        ))

        self.db.add(BartanBank(
            id=survey.id,
            established_banks=random.randint(0, 5),
        ))

        self.db.add(VehicleAssets(
            id=survey.id,
            owned_tricycles=random.randint(0, 5),
            owned_e_rickshaws=random.randint(0, 3),
            owned_motorized_vehicles=random.randint(0, 2),
            contractor_tricycles=random.randint(0, 5),
            contractor_e_rickshaws=random.randint(0, 3),
            contractor_motorized_vehicles=random.randint(0, 2),
        ))

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

        for village_id in village_ids:
            v_data = VillageData(
                survey_id=survey.id,
                village_id=village_id,
                village_name=f"Village {village_id}",
                population=random.randint(500, 2000),
                num_households=random.randint(100, 500),
            )
            self.db.add(v_data)
            await self.db.flush()

            self.db.add(VillageSBMGAssets(
                id=v_data.id,
                ihhl=random.randint(50, 150),
                csc=random.randint(1, 5),
            ))

            self.db.add(VillageGWMAssets(
                id=v_data.id,
                soak_pit=random.randint(20, 80),
                magic_pit=random.randint(10, 50),
                leach_pit=random.randint(5, 30),
                wsp=random.randint(1, 3),
                dewats=random.randint(0, 2),
            ))

        self.db.add(targets)
        await self.db.commit()
