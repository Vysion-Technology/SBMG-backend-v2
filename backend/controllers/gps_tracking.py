"""GPS Tracking Controller."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.response.gps import GPSTrackingResponse, UniqueVehiclesResponse
from services.gps_tracking import GPSTrackingService

router = APIRouter()


@router.get("/vehicles", response_model=UniqueVehiclesResponse)
async def get_unique_vehicles(
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of unique vehicles from GPS tracking data.

    Returns:
        UniqueVehiclesResponse: List of unique vehicle numbers with count
    """
    vehicles = await GPSTrackingService(db).get_unique_vehicles()

    return UniqueVehiclesResponse(vehicles=vehicles, total_count=len(vehicles))


@router.get("/tracking", response_model=List[GPSTrackingResponse])
async def get_vehicle_tracking(
    vehicle_nos: str = Query(..., description="Comma-separated list of vehicle numbers (e.g., 'UP91T5013,UP91T4309')"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get GPS tracking data for specified vehicles.

    Args:
        vehicle_nos: Comma-separated list of vehicle numbers
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List[GPSTrackingResponse]: List of GPS tracking records
    """
    # Parse comma-separated vehicle numbers
    vehicle_list = [v.strip() for v in vehicle_nos.split(",") if v.strip()]

    if not vehicle_list:
        raise HTTPException(status_code=400, detail="At least one vehicle number must be provided")

    # Get tracking data
    tracking_records = await GPSTrackingService(db).get_latest_vehicle_positions(vehicle_nos=vehicle_list, limit=limit)

    if not tracking_records:
        raise HTTPException(status_code=404, detail=f"No tracking data found for vehicles: {', '.join(vehicle_list)}")

    return [
        GPSTrackingResponse(
            id=record.id,
            vehicle_no=record.vehicle_no,
            imei=record.imei,
            latitude=record.latitude,
            longitude=record.longitude,
            speed=record.speed,
            ignition=record.ignition,
            total_gps_odometer=record.total_gps_odometer,
            timestamp=record.timestamp,
        )
        for record in tracking_records
    ]


@router.get("/tracking/latest", response_model=List[GPSTrackingResponse])
async def get_latest_positions(
    db: AsyncSession = Depends(get_db),
):
    """
    Get the latest GPS position for all vehicles.

    Returns:
        List[GPSTrackingResponse]: Latest GPS tracking record for each vehicle
    """
    tracking_records = await GPSTrackingService(db).get_latest_vehicle_positions()

    return [
        GPSTrackingResponse(
            id=record.id,
            vehicle_no=record.vehicle_no,
            imei=record.imei,
            latitude=record.latitude,
            longitude=record.longitude,
            speed=record.speed,
            ignition=record.ignition,
            total_gps_odometer=record.total_gps_odometer,
            timestamp=record.timestamp,
        )
        for record in tracking_records
    ]
