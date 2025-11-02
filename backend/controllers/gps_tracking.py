"""GPS Tracking Controller."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.internal import GeoTypeEnum
from models.requests.gps import AddVehicleRequest
from models.response.gps import (
    LocationLineItem,
    RunningVehicleSummaryResponse,
    RunningVehiclesListResponse,
    VehicleResponse,
)
from services.geography import GeographyService
from services.gps_tracking import GPSTrackingService

router = APIRouter()


@router.post("/vehicles", response_model=VehicleResponse)
async def add_vehicles(
    add_vehicle_request: AddVehicleRequest,
    db: AsyncSession = Depends(get_db),
) -> VehicleResponse:
    """
    Add a new vehicle for a Gram Panchayat.

    Args:
        gp_id: Gram Panchayat ID
        vehicle_no: Vehicle number
        imei: IMEI number of the GPS device
        db: Database session

    Returns:
        VehicleResponse: The added vehicle information
    """
    vehicle = await GPSTrackingService(db).add_vehicle(
        gp_id=add_vehicle_request.gp_id,
        vehicle_no=add_vehicle_request.vehicle_no,
        imei=add_vehicle_request.imei,
    )
    return VehicleResponse(
        id=vehicle.id,
        vehicle_no=vehicle.vehicle_no,
        imei=vehicle.imei,
        gp_id=vehicle.gp_id,
    )


@router.get("/vehicles", response_model=List[VehicleResponse])
async def get_vehicles(
    district_id: Optional[int] = Query(None, description="District ID"),
    block_id: Optional[int] = Query(None, description="Block ID"),
    gp_id: Optional[int] = Query(None, description="Gram Panchayat ID"),
    db: AsyncSession = Depends(get_db),
) -> List[VehicleResponse]:
    """
    Get all vehicles for a specific location.

    Args:
        district_id: District ID
        block_id: Block ID
        gp_id: Gram Panchayat ID
        db: Database session

    Returns:
        List[VehicleResponse]: List of vehicles for the specified Gram Panchayat
    """
    vehicles = await GPSTrackingService(db).get_vehicles(district_id=district_id, block_id=block_id, gp_id=gp_id)
    return [
        VehicleResponse(
            id=vehicle.id,
            vehicle_no=vehicle.vehicle_no,
            imei=vehicle.imei,
            gp_id=vehicle.gp_id,
        )
        for vehicle in vehicles
    ]


@router.get("/vehicles/", response_model=RunningVehiclesListResponse)
async def get_vehicle(
    district_id: Optional[int] = Query(None, description="District ID"),
    block_id: Optional[int] = Query(None, description="Block ID"),
    gp_id: Optional[int] = Query(None, description="Gram Panchayat ID"),
    start_time: Optional[datetime] = Query(None, description="Start time for filtering GPS records"),
    end_time: Optional[datetime] = Query(None, description="End time for filtering GPS records"),
    db: AsyncSession = Depends(get_db),
) -> RunningVehiclesListResponse:
    """
    Get vehicle details by vehicle ID.

    Args:
        vehicle_id: Vehicle ID
        db: Database session

    Returns:
        VehicleResponse: The vehicle information
    """
    if start_time and end_time and end_time < start_time:
        raise HTTPException(status_code=400, detail="end_time must be greater than or equal to start_time")

    now = datetime.now(tz=timezone.utc)
    start_time = start_time or now - timedelta(minutes=30)
    end_time = end_time or now
    if start_time.date() != end_time.date():
        raise HTTPException(status_code=400, detail="start_time and end_time must be on the same date")
    vehicles = await GPSTrackingService(db).get_vehicle_details(
        district_id=district_id,
        block_id=block_id,
        gp_id=gp_id,
        start_time=start_time,
        end_time=end_time,
    )
    if not vehicles:
        raise HTTPException(status_code=404, detail="No vehicles found for the specified location(s).")

    geo_service = GeographyService(db)

    return RunningVehiclesListResponse(
        date_=start_time.date(),
        location=LocationLineItem(
            type=GeoTypeEnum.GP if gp_id else GeoTypeEnum.BLOCK if block_id else GeoTypeEnum.DISTRICT,
            district=(await geo_service.get_district(district_id)).name if district_id else "",
            block=(await geo_service.get_block(block_id)).name if block_id else "",
            gp=(await geo_service.get_village(gp_id)).name if gp_id else "",
        ),
        summary=RunningVehicleSummaryResponse(
            total=0,
            running=0,
            stopped=0,
            active=0,
            inactive=0,
        ),
        vehicles=vehicles,
    )
