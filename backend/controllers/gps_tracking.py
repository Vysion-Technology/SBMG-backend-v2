"""GPS Tracking Controller."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.response.gps import GPSTrackingResponse, UniqueVehiclesResponse, VehicleResponse
from services.gps_tracking import GPSTrackingService

router = APIRouter()


@router.post("/vehicles", response_model=VehicleResponse)
async def add_vehicles(
    gp_id: int = Query(..., description="Gram Panchayat ID"),
    vehicle_no: str = Query(..., description="Vehicle number to add"),
    imei: str = Query(..., description="IMEI number of the vehicle GPS device"),
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
    vehicle = await GPSTrackingService(db).add_vehicle(gp_id=gp_id, vehicle_no=vehicle_no, imei=imei)
    return VehicleResponse(
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
            vehicle_no=vehicle.vehicle_no,
            imei=vehicle.imei,
            gp_id=vehicle.gp_id,
        )
        for vehicle in vehicles
    ]
