"""GPS Tracking Service."""

import logging
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any

import requests
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct, func

from models.database.gps import GPSTracking

logger = logging.getLogger(__name__)


class GPSTrackingService:
    """Service for GPS tracking operations."""

    TRACKVERSE_API_URL = "https://api.trackverse.in/api/public/tracking/v0/device"
    TRACKVERSE_API_KEY = "NT-20257E2B94DB44C90F755C45D61E0CA55895"
    TRACKVERSE_USERNAME = "clacademy"
    TRACKVERSE_PASSWORD = "123456"
    FETCH_INTERVAL_SECONDS = 10  # Fetch GPS data every 10 seconds

    _background_task = None
    _should_stop = False

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

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

                    gps_record = GPSTracking(
                        vehicle_no=device.get("vehicleNo"),
                        imei=device.get("imei"),
                        latitude=device.get("latitude"),
                        longitude=device.get("longitude"),
                        speed=device.get("speed"),
                        ignition=device.get("ignition"),
                        total_gps_odometer=device.get("totalGpsOdometer"),
                        timestamp=timestamp,
                    )

                    self.db.add(gps_record)
                    records_saved += 1
                except Exception as e:  # pylint: disable=broad-except
                    logger.error("Error saving GPS record for vehicle %s: %s", device.get('vehicleNo'), e)
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
        except Exception as e: # pylint: disable=broad-except
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

    def stop_periodic_fetch():
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
        self,
        vehicle_nos: Optional[List[str]] = None, limit: int = 1000
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
