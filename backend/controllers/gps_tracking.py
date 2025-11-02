"""GPS Tracking Controller."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.requests.gps import AddVehicleRequest
from models.response.gps import VehicleResponse
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
