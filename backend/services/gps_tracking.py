"""GPS Tracking Service."""

import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any

from fastapi import HTTPException
import requests
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, distinct, func
from sqlalchemy.orm import selectinload

from models.database.geography import Block, District, GramPanchayat
from models.database.gps import GPSRecord, GPSTracking, Vehicle
from models.response.gps import CoordinatesResponse, RunningVehiclesResponse

logger = logging.getLogger(__name__)


class GPSTrackingService:
    """Service for GPS tracking operations."""

    TRACKVERSE_API_URL = "https://api.trackverse.in/api/public/tracking/v0/device"
    TRACKVERSE_API_KEY = "NT-20257E2B94DB44C90F755C45D61E0CA55895"
    TRACKVERSE_USERNAME = "clacademy"
    TRACKVERSE_PASSWORD = "123456"
    FETCH_INTERVAL_SECONDS = 100  # Fetch GPS data every 10 seconds

    _background_task = None
    _should_stop = False

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_vehicle_by_number(self, vehicle_no: str) -> Optional[Vehicle]:
        """
        Get vehicle by its registration number.

        Args:
            vehicle_no: Vehicle registration number

        Returns:
            Vehicle or None if not found
        """
        result = await self.db.execute(select(Vehicle).where(Vehicle.vehicle_no == vehicle_no))
        return result.scalar_one_or_none()

    async def fetch_and_save_gps_data(self) -> Dict[str, Any]:
        """
        Fetch GPS data from Trackverse API and save to database.

        Returns:
            dict: Status of the operation
        """
        try:
            # Fetch data from Trackverse API
            headers = {
                "accept": "application/json",
                "api-key": GPSTrackingService.TRACKVERSE_API_KEY,
                "username": GPSTrackingService.TRACKVERSE_USERNAME,
                "pass": GPSTrackingService.TRACKVERSE_PASSWORD,
            }

            response = requests.get(GPSTrackingService.TRACKVERSE_API_URL, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()

            if not data.get("status") or data.get("statusCode") != 200:
                logger.error("API returned error: %s, %s", data.get("message"), data.get("statusCode"))
                return {"success": False, "message": data.get("message", "Unknown error"), "records_saved": 0}

            devices_data = data.get("data", [])

            if not devices_data:
                logger.warning("No GPS data received from API")
                return {"success": True, "message": "No data to save", "records_saved": 0}

            # Save to database
            records_saved = 0
            for device in devices_data:
                try:
                    # Parse timestamp from "30-10-2025 14:57:35" format
                    timestamp_str = device.get("timestamp")
                    timestamp = datetime.strptime(timestamp_str, "%d-%m-%Y %H:%M:%S")
                    vehicle = await self.get_vehicle_by_number(device.get("vehicleNo"))
                    if not vehicle:
                        logger.warning("Vehicle with number %s not found, skipping record", device.get("vehicleNo"))
                        continue
                    assert vehicle, "Vehicle should not be None here"
                    gps_record = GPSRecord(
                        vehicle_id=vehicle.id,
                        latitude=float(device.get("latitude")),
                        longitude=float(device.get("longitude")),
                        speed=float(device.get("speed")),
                        ignition=bool(device.get("ignition")),
                        total_gps_odometer=float(device.get("totalGpsOdometer")),
                        timestamp=timestamp,
                    )
                    self.db.add(gps_record)
                    records_saved += 1
                except Exception as e:  # pylint: disable=broad-except
                    logger.error("Error saving GPS record for vehicle %s: %s", device.get("vehicleNo"), e)
                    continue

            await self.db.commit()

            logger.info("Successfully saved %d GPS records", records_saved)
            return {
                "success": True,
                "message": f"Successfully saved {records_saved} GPS records",
                "records_saved": records_saved,
            }

        except requests.RequestException as e:
            logger.error("Error fetching GPS data from API: %s", e)
            return {"success": False, "message": f"Failed to fetch data from API: {str(e)}", "records_saved": 0}
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Unexpected error in fetch_and_save_gps_data: %s", e)
            return {"success": False, "message": f"Unexpected error: {str(e)}", "records_saved": 0}

    async def start_periodic_fetch(self):
        """
        Start periodic GPS data fetching in the background.
        This runs every FETCH_INTERVAL_SECONDS.
        """
        GPSTrackingService._should_stop = False
        logger.info("Starting periodic GPS data fetch (every %d seconds)", GPSTrackingService.FETCH_INTERVAL_SECONDS)

        while not GPSTrackingService._should_stop:
            try:
                result = await self.fetch_and_save_gps_data()
                logger.info("Periodic GPS fetch result: %s", result.get("message"))
            except Exception as e:  # pylint: disable=broad-except
                logger.error("Error in periodic GPS fetch: %s", e)

            # Wait for the specified interval before next fetch
            await asyncio.sleep(GPSTrackingService.FETCH_INTERVAL_SECONDS)

    def stop_periodic_fetch(self):
        """Stop the periodic GPS data fetching."""
        logger.info("Stopping periodic GPS data fetch")
        GPSTrackingService._should_stop = True

    async def get_unique_vehicles(self) -> List[str]:
        """
        Get list of unique vehicle numbers from GPS tracking data.

        Args:
            db: Database session

        Returns:
            List of unique vehicle numbers
        """
        result = await self.db.execute(select(distinct(GPSTracking.vehicle_no)).order_by(GPSTracking.vehicle_no))
        vehicles = result.scalars().all()
        return [str(v) for v in vehicles]

    @staticmethod
    async def get_vehicle_tracking(db: AsyncSession, vehicle_nos: List[str], limit: int = 100) -> List[GPSTracking]:
        """
        Get tracking data for specified vehicles.

        Args:
            db: Database session
            vehicle_nos: List of vehicle numbers to fetch
            limit: Maximum number of records per vehicle

        Returns:
            List of GPS tracking records
        """
        # Get latest records for each vehicle
        query = (
            select(GPSTracking)
            .where(GPSTracking.vehicle_no.in_(vehicle_nos))
            .order_by(GPSTracking.vehicle_no, GPSTracking.timestamp.desc())
            .limit(limit)
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_latest_vehicle_positions(
        self, vehicle_nos: Optional[List[str]] = None, limit: int = 1000
    ) -> List[GPSTracking]:
        """
        Get the latest position for each vehicle.

        Args:
            db: Database session
            vehicle_nos: Optional list of vehicle numbers to filter

        Returns:
            List of latest GPS tracking records for each vehicle
        """
        # This is a simplified version - for better performance, you might want to use
        # a window function or subquery to get the latest record per vehicle

        # Subquery to get the latest timestamp for each vehicle
        subquery = select(GPSTracking.vehicle_no, func.max(GPSTracking.timestamp).label("max_timestamp")).group_by(
            GPSTracking.vehicle_no
        )
        subquery = subquery.limit(limit)

        if vehicle_nos:
            subquery = subquery.where(GPSTracking.vehicle_no.in_(vehicle_nos))

        subquery = subquery.subquery()

        # Main query to get full records
        query = (
            select(GPSTracking)
            .join(
                subquery,
                (GPSTracking.vehicle_no == subquery.c.vehicle_no) & (GPSTracking.timestamp == subquery.c.max_timestamp),
            )
            .order_by(GPSTracking.vehicle_no)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add_vehicle(self, vehicle_no: str, imei: str, gp_id: int) -> Vehicle:
        """
        Add a new vehicle to the tracking system.

        Args:
            vehicle_no: Vehicle registration number
            imei: Device IMEI number
            gp_id: Gram Panchayat ID

        Returns:
            The created GPSTracking record
        """
        # Check if a vehicle with the same vehicle_no and gp_id already exists
        existing_vehicle = await self.get_vehicles(vehicle_no=vehicle_no)
        if existing_vehicle:
            raise HTTPException(status_code=400, detail=f"Vehicle with number {vehicle_no} already exists.")
        new_vehicle = (
            await self.db.execute(
                insert(Vehicle)
                .values(  # type: ignore
                    vehicle_no=vehicle_no,
                    imei=imei,
                    gp_id=gp_id,
                )
                .returning(Vehicle)
            )
        ).scalar_one()
        await self.db.commit()
        return new_vehicle

    async def get_vehicles(
        self,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        gp_id: Optional[int] = None,
        vehicle_no: Optional[str] = None,
    ) -> List[Vehicle]:
        """
        Get all vehicles for a specific Gram Panchayat.

        Args:
            gp_id: Gram Panchayat ID
            db: Database session

        Returns:
            List[Vehicle]: List of vehicles for the specified Gram Panchayat
        """
        query = (
            select(Vehicle)
            .options(selectinload(Vehicle.gp).selectinload(GramPanchayat.block).selectinload(Block.district))
            .join(GramPanchayat, Vehicle.gp_id == GramPanchayat.id)
            .join(Block, GramPanchayat.block_id == Block.id)
            .join(District, Block.district_id == District.id)
        )

        if district_id:
            query = query.where(District.id == district_id)
        if block_id:
            query = query.where(Block.id == block_id)
        if gp_id:
            query = query.where(GramPanchayat.id == gp_id)
        if vehicle_no:
            query = query.where(Vehicle.vehicle_no == vehicle_no)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_vehicle_details(
        self,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        gp_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[RunningVehiclesResponse]:
        """
        Get vehicle details by vehicle ID.

        Args:
            vehicle_id: Vehicle ID

        Returns:
            Vehicle or None if not found
        """
        now = datetime.now(tz=timezone.utc)
        if not start_time:
            start_time = now - timedelta(minutes=30)
        end_time = end_time or now
        print(f"Start time: {start_time}, End time: {end_time}")

        vehicles_query = select(GPSRecord).join(Vehicle, GPSRecord.vehicle_id == Vehicle.id)
        if district_id:
            vehicles_query = vehicles_query.where(District.id == district_id)
        if block_id:
            vehicles_query = vehicles_query.where(Block.id == block_id)
        if gp_id:
            vehicles_query = vehicles_query.where(GramPanchayat.id == gp_id)
        vehicles_query = vehicles_query.where(GPSRecord.timestamp >= start_time)
        if end_time:
            vehicles_query = vehicles_query.where(GPSRecord.timestamp <= end_time)
        vehicles_query = vehicles_query.order_by(Vehicle.id, GPSRecord.timestamp.asc())
        vehicles = await self.db.execute(vehicles_query)
        vehicles = vehicles.scalars().all()
        print(vehicles)
        if len(vehicles) > 10000:
            raise HTTPException(status_code=400, detail="Too many vehicles found, please narrow down your query.")
        vehicle_details: List[RunningVehiclesResponse] = []
        vehicle_id_to_index_map: Dict[int, int] = {}
        for _, record in enumerate(vehicles):
            if record.vehicle.id in vehicle_id_to_index_map:
                vehicle_index = vehicle_id_to_index_map[record.vehicle.id]
                vehicle_details[vehicle_index].route.append(
                    CoordinatesResponse(lat=record.latitude, long=record.longitude)
                )
            else:
                vehicle_id_to_index_map[record.vehicle.id] = len(vehicle_details)
                vehicle_details.append(
                    RunningVehiclesResponse(
                        vehicle_id=record.vehicle.id,
                        name=f"Vehicle {record.vehicle.vehicle_no}",
                        vehicle_no=record.vehicle.vehicle_no,
                        status="Running" if record.speed > 0 else "Stopped",
                        speed=record.speed,
                        last_updated=record.timestamp,
                        coordinates=CoordinatesResponse(lat=record.latitude, long=record.longitude),
                        route=[
                            CoordinatesResponse(lat=record.latitude, long=record.longitude)
                        ],
                    )
                )

        return vehicle_details
