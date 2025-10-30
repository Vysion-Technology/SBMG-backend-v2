"""SBMG Rajasthan Backend Main Application."""

import os
import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from controllers import contractor
from controllers import citizen, event, scheme
from controllers import auth, complaints, admin, public
from controllers import geography, attendance
from controllers import fcm_device, inspection, notice, annual_survey
from controllers import position_holder
from controllers import gps_tracking
from database import AsyncSessionLocal, get_db
from services.gps_tracking import GPSTrackingService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Actions to perform on application startup and shutdown."""
    # Startup: Start periodic GPS data fetching
    logger.info("Application starting up...")
    logger.info("Starting GPS data periodic fetch task...")
    
    # Create background task for periodic GPS fetching
    async for db in get_db():
        gps_task = asyncio.create_task(GPSTrackingService(db).start_periodic_fetch())
        
        yield
        
        # Shutdown: Stop GPS fetching task
        logger.info("Application shutting down...")
        logger.info("Stopping GPS data periodic fetch task...")
        GPSTrackingService(db).stop_periodic_fetch()
    
    # Wait for the task to complete (with timeout)
    try:
        await asyncio.wait_for(gps_task, timeout=5.0)
    except asyncio.TimeoutError:
        logger.warning("GPS fetch task did not stop within timeout, cancelling...")
        gps_task.cancel()
        try:
            await gps_task
        except asyncio.CancelledError:
            pass


fastapi_app = FastAPI(
    title="SBM Gramin Rajasthan API",
    description="Swachh Bharat Mission (Gramin) - Rajasthan Complaint Management System",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@fastapi_app.get("/")
async def read_root():
    """Root endpoint."""
    return {"message": "SBM Gramin Rajasthan API", "status": "running"}


@fastapi_app.get("/health")
async def health_check():
    """Health check endpoint for Docker."""
    return {"status": "healthy"}


# Include routers
fastapi_app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
fastapi_app.include_router(citizen.router, prefix="/api/v1/citizen", tags=["Citizen"])
fastapi_app.include_router(geography.router, prefix="/api/v1/geography", tags=["Geography"])
fastapi_app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
fastapi_app.include_router(position_holder.router, prefix="/api/v1/position-holders", tags=["Position Holders"])
fastapi_app.include_router(complaints.router, prefix="/api/v1/complaints", tags=["Complaints"])
fastapi_app.include_router(event.router, prefix="/api/v1/events", tags=["Events"])
fastapi_app.include_router(public.router, prefix="/api/v1/public", tags=["Public"])
fastapi_app.include_router(attendance.router, prefix="/api/v1/attendance", tags=["DailyAttendance"])
fastapi_app.include_router(scheme.router, prefix="/api/v1/schemes", tags=["Schemes"])
fastapi_app.include_router(fcm_device.router, prefix="/api/v1/notifications", tags=["FCM Notifications"])
fastapi_app.include_router(inspection.router, prefix="/api/v1/inspections", tags=["Inspections"])
fastapi_app.include_router(annual_survey.router, prefix="/api/v1/annual-surveys", tags=["Annual Surveys"])
fastapi_app.include_router(notice.router, prefix="/api/v1/notices", tags=["Notices"])
fastapi_app.include_router(
    contractor.router,
    prefix="/api/v1/contractors",
    tags=["Agency and Contractor Management"],
)
fastapi_app.include_router(
    gps_tracking.router,
    prefix="/api/v1/gps",
    tags=["GPS Tracking"],
)
# app.include_router(survey.router, prefix="/api/v1/surveys", tags=["Surveys"])


@fastapi_app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):  # pylint: disable=unused-argument
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail, "status_code": exc.status_code},
    )


@fastapi_app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):  # pylint: disable=unused-argument
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "status_code": 500},
    )


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(  # type: ignore
        "main:fastapi_app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )
