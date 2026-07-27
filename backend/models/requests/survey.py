"""
Request Models for Annual Survey Management
"""

from typing import Optional, List, Any
from datetime import date
from pydantic import BaseModel, Field, model_validator
from models.database.survey_master import (
    FundHead,
    CollectionFrequency,
    CleaningFrequency,
    WorkFrequency,
)


class WorkOrderDetailsRequest(BaseModel):
    """Request model for work order details."""

    work_order_no: Optional[str] = None
    work_order_date: Optional[date] = None
    work_order_amount: Optional[float] = None


class FundSanctionedRequest(BaseModel):
    """Request model for fund sanctioned details."""

    amount: Optional[float] = None
    head: Optional[FundHead] = None


class DoorToDoorCollectionRequest(BaseModel):
    """Request model for door to door collection details."""

    num_households: Optional[int] = None
    num_shops: Optional[int] = None
    collection_frequency: Optional[CollectionFrequency] = None


class RoadSweepingDetailsRequest(BaseModel):
    """Request model for road sweeping details."""

    width: Optional[float] = None
    length: Optional[float] = None
    cleaning_frequency: Optional[CleaningFrequency] = None


class DrainCleaningDetailsRequest(BaseModel):
    """Request model for drain cleaning details."""

    length: Optional[float] = None
    cleaning_frequency: Optional[CleaningFrequency] = None


class CSCDetailsRequest(BaseModel):
    """Request model for CSC details."""

    numbers: Optional[int] = None
    cleaning_frequency: Optional[CleaningFrequency] = None


# --- New Asset Category Request Models ---

class ODFSustainabilityRequest(BaseModel):
    """Request model for ODF sustainability details."""
    ihhl: int = 0
    retrofitting: int = 0
    csc: int = 0
    csc_shala_darpan: int = 0


class SWMAssetsCategoryRequest(BaseModel):
    """Request model for SWM assets details."""
    bins_hh_level: int = 0
    bins_public_places: int = 0
    community_compost_pits: int = 0
    hh_compost_pit: int = 0
    segregation_sheds: int = 0
    tricycles_manual: int = 0
    e_rickshaws: int = 0
    motorized_vehicles: int = 0


class LWMAssetsRequest(BaseModel):
    """Request model for LWM assets details."""
    pits_hh_level: int = 0
    community_pits: int = 0
    wsp: int = 0
    dewats: int = 0
    wetlands: int = 0
    other_treatments: int = 0
    drainage_channels: int = 0


class PWMUDetailsRequest(BaseModel):
    """Request model for PWMU details."""
    established_pwmu: int = 0
    blocks_covered_pwmu: int = 0
    urban_mrfs: int = 0
    blocks_covered_urban_mrf: int = 0


class FSMDetailsRequest(BaseModel):
    """Request model for FSM details."""
    twin_pit_toilets: int = 0
    single_pit_toilets: int = 0
    septic_tank_toilets: int = 0
    retrofitted_toilets: int = 0
    mechanized_desludging: int = 0
    fstps_rural: int = 0
    fstps_urban: int = 0


class GobardhanProjectRequest(BaseModel):
    """Request model for Gobar-dhan project details."""
    total_sanctioned: int = 0
    total_functional: int = 0
    gas_production: float = 0.0


class D2DActivitiesRequest(BaseModel):
    """Request model for D2D activities details."""
    is_active: bool = False
    work_frequency: Optional[WorkFrequency] = None
    sanctioned_tender: int = 0
    sanctioned_self_gp: int = 0
    sanctioned_csr_ngo: int = 0
    sanctioned_shg: int = 0
    sanctioned_mixed_model: int = 0
    total_expenditure: float = 0.0
    vehicles_deployed: int = 0
    persons_deployed: int = 0
    households_covered: int = 0
    status_start: int = 0
    status_running: int = 0
    status_completed: int = 0

    @model_validator(mode="before")
    @classmethod
    def preprocess_work_frequency(cls, data: Any) -> Any:
        if isinstance(data, dict):
            work_freq = data.get("work_frequency")
            if isinstance(work_freq, str) and work_freq.strip().lower() in ("none", "", "null", "undefined"):
                data["work_frequency"] = None
        return data

    @model_validator(mode="after")
    def validate_work_frequency(self):
        if not self.is_active:
            self.work_frequency = None
        elif self.is_active and self.work_frequency is None:
            self.work_frequency = WorkFrequency.DAILY
        return self


class BartanBankRequest(BaseModel):
    """Request model for Bartan Bank details."""
    established_banks: int = 0
    revenue: float = 0.0


class VehicleAssetsRequest(BaseModel):
    """Request model for categorized vehicle assets."""
    owned_tricycles: int = 0
    owned_e_rickshaws: int = 0
    owned_motorized_vehicles: int = 0
    contractor_tricycles: int = 0
    contractor_e_rickshaws: int = 0
    contractor_motorized_vehicles: int = 0

# --- End of New Asset Category Request Models ---


class SBMGYearTargetsRequest(BaseModel):
    """Request model for SBMG year targets."""

    ihhl: Optional[int] = None
    csc: Optional[int] = None
    rrc: Optional[int] = None
    pwmu: Optional[int] = None
    soak_pit: Optional[int] = None
    magic_pit: Optional[int] = None
    leach_pit: Optional[int] = None
    wsp: Optional[int] = None
    dewats: Optional[int] = None


class VillageSBMGAssetsRequest(BaseModel):
    """Request model for village SBMG assets."""

    ihhl: Optional[int] = None
    csc: Optional[int] = None


class VillageGWMAssetsRequest(BaseModel):
    """Request model for village GWM assets."""

    soak_pit: Optional[int] = None
    magic_pit: Optional[int] = None
    leach_pit: Optional[int] = None
    wsp: Optional[int] = None
    dewats: Optional[int] = None


class VillageDataRequest(BaseModel):
    """Request model for village data."""

    village_id: int = Field(..., description="ID of the village")
    village_name: Optional[str] = None
    population: Optional[int] = None
    num_households: Optional[int] = None
    sbmg_assets: Optional[VillageSBMGAssetsRequest] = None
    gwm_assets: Optional[VillageGWMAssetsRequest] = None


class CreateAnnualSurveyRequest(BaseModel):
    """Request model for creating a new annual survey."""

    fy_id: int = Field(..., description="Financial Year ID")
    gp_id: int = Field(..., description="ID of the Gram Panchayat")
    survey_date: Optional[date] = Field(
        None, description="Date of survey (defaults to today)"
    )

    # 1. VDO Details
    vdo_id: Optional[int] = Field(None, description="ID of the VDO")
    vdo_name: Optional[str] = Field(None, description="Name of the VDO")
    vdo_contact_number: Optional[str] = Field(None, description="Contact number of the VDO")

    # 2. Sarpanch Details
    sarpanch_name: str = Field(..., description="Name of the Sarpanch")
    sarpanch_contact: str = Field(..., description="Contact number of the Sarpanch")

    # 3. No. of Ward Panchs
    num_ward_panchs: int = Field(..., description="Number of Ward Panchs")

    # 4. Bidder Name (Sanitation activities)
    agency_id: int = Field(..., description="ID of the Agency")

    # 5. Work Order Details
    work_order: Optional[WorkOrderDetailsRequest] = Field(
        None, description="Work order details"
    )

    # 6. Fund Sanctioned
    fund_sanctioned: Optional[FundSanctionedRequest] = None

    # 7. Door to Door Collection
    door_to_door_collection: Optional[DoorToDoorCollectionRequest] = None

    # 8. Road Sweeping
    road_sweeping: Optional[RoadSweepingDetailsRequest] = None

    # 9. Drain Cleaning
    drain_cleaning: Optional[DrainCleaningDetailsRequest] = None

    # 10. CSC
    csc_details: Optional[CSCDetailsRequest] = None

    # New categorized assets
    odf_sustainability: Optional[ODFSustainabilityRequest] = None
    swm_assets: Optional[SWMAssetsCategoryRequest] = None
    lwm_assets: Optional[LWMAssetsRequest] = None
    pwmu_details: Optional[PWMUDetailsRequest] = None
    fsm_details: Optional[FSMDetailsRequest] = None
    gobardhan_projects: Optional[GobardhanProjectRequest] = None
    d2d_activities: Optional[D2DActivitiesRequest] = None
    bartan_bank: Optional[BartanBankRequest] = None
    vehicle_assets: Optional[VehicleAssetsRequest] = None

    # 12. SBMG Year Targets
    sbmg_targets: Optional[SBMGYearTargetsRequest] = None

    # 13. Village Data (multiple villages)
    village_data: Optional[List[VillageDataRequest]] = Field(
        None, description="List of village data"
    )

    @model_validator(mode="after")
    def validate_amounts(self):
        """Validate that work order amount is less than or equal to fund sanctioned amount."""
        if (
            self.work_order
            and self.work_order.work_order_amount is not None
            and self.fund_sanctioned
            and self.fund_sanctioned.amount is not None
        ):
            if self.work_order.work_order_amount > self.fund_sanctioned.amount:
                raise ValueError(
                    "Work order amount cannot be greater than the fund sanctioned amount"
                )
        return self


class UpdateAnnualSurveyRequest(BaseModel):
    """Request model for updating an annual survey."""

    # 1. VDO Details
    vdo_name: Optional[str] = None
    vdo_contact_number: Optional[str] = Field(
        None, description="Contact number of the VDO", pattern=r"^[6-9]\d{9}$"
    )

    # 2. Sarpanch Details
    sarpanch_name: Optional[str] = None
    sarpanch_contact: Optional[str] = Field(
        None, description="Contact number of the Sarpanch", pattern=r"^[6-9]\d{9}$"
    )

    # 3. No. of Ward Panchs
    num_ward_panchs: Optional[int] = None

    # 4. Bidder Name (Sanitation activities)
    agency_id: Optional[int] = None

    # 5. Work Order Details
    work_order: Optional[WorkOrderDetailsRequest] = None

    # 6. Fund Sanctioned
    fund_sanctioned: Optional[FundSanctionedRequest] = None

    # 7. Door to Door Collection
    door_to_door_collection: Optional[DoorToDoorCollectionRequest] = None

    # 8. Road Sweeping
    road_sweeping: Optional[RoadSweepingDetailsRequest] = None

    # 9. Drain Cleaning
    drain_cleaning: Optional[DrainCleaningDetailsRequest] = None

    # 10. CSC
    csc_details: Optional[CSCDetailsRequest] = None

    # New categorized assets
    odf_sustainability: Optional[ODFSustainabilityRequest] = None
    swm_assets: Optional[SWMAssetsCategoryRequest] = None
    lwm_assets: Optional[LWMAssetsRequest] = None
    pwmu_details: Optional[PWMUDetailsRequest] = None
    fsm_details: Optional[FSMDetailsRequest] = None
    gobardhan_projects: Optional[GobardhanProjectRequest] = None
    d2d_activities: Optional[D2DActivitiesRequest] = None
    bartan_bank: Optional[BartanBankRequest] = None
    vehicle_assets: Optional[VehicleAssetsRequest] = None

    # 12. SBMG Year Targets
    sbmg_targets: Optional[SBMGYearTargetsRequest] = None

    # 13. Village Data (multiple villages)
    village_data: Optional[List[VillageDataRequest]] = None

    @model_validator(mode="after")
    def validate_amounts(self):
        """Validate that work order amount is less than or equal to fund sanctioned amount."""
        if (
            self.work_order
            and self.work_order.work_order_amount is not None
            and self.fund_sanctioned
            and self.fund_sanctioned.amount is not None
        ):
            if self.work_order.work_order_amount > self.fund_sanctioned.amount:
                raise ValueError(
                    "Work order amount cannot be greater than the fund sanctioned amount"
                )
        return self
