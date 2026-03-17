"""SBMG Rajasthan Backend Main Application."""

import os
import logging
import asyncio
import uuid
from contextlib import asynccontextmanager

import traceback
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from controllers import contractor
from controllers import citizen, event, scheme
from controllers import auth, complaints, admin, public
from controllers import geography, attendance
from controllers import fcm_device, inspection, notice, annual_survey
from controllers import position_holder
from controllers import gps_tracking
from controllers import feedback
from controllers import formulae
from controllers import contractor_analytics
from database import get_db
from middleware.security import SecurityHeadersMiddleware
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

# Add Security Headers Middleware
fastapi_app.add_middleware(SecurityHeadersMiddleware)

# Add CORS middleware
# Primary production origins
default_origins = [
    "http://10.70.232.147",
    "http://139.59.34.99",
    "https://sbmg.rajasthan.gov.in",  # Placeholder for actual production domain if applicable
]

# Only include development origins if DEBUG is enabled
if os.getenv("DEBUG", "false").lower() == "true":
    default_origins.extend(
        [
            "http://localhost",
            "http://127.0.0.1",
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8000",
        ]
    )

# Read allowed origins from environment variable and merge with defaults
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "")
env_origins = [
    origin.strip().rstrip("/")
    for origin in allowed_origins_str.split(",")
    if origin.strip() and origin.strip() != "*"
]
allowed_origins = list(set(default_origins + env_origins))

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    # Explicitly list methods to satisfy security audits
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    # Explicitly list common headers to satisfy security audits
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
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
fastapi_app.include_router(
    geography.router, prefix="/api/v1/geography", tags=["Geography"]
)
fastapi_app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
fastapi_app.include_router(
    position_holder.router, prefix="/api/v1/position-holders", tags=["Position Holders"]
)
fastapi_app.include_router(
    complaints.router, prefix="/api/v1/complaints", tags=["Complaints"]
)
fastapi_app.include_router(event.router, prefix="/api/v1/events", tags=["Events"])
fastapi_app.include_router(public.router, prefix="/api/v1/public", tags=["Public"])
fastapi_app.include_router(
    attendance.router, prefix="/api/v1/attendance", tags=["DailyAttendance"]
)
fastapi_app.include_router(scheme.router, prefix="/api/v1/schemes", tags=["Schemes"])
fastapi_app.include_router(
    fcm_device.router, prefix="/api/v1/notifications", tags=["FCM Notifications"]
)
fastapi_app.include_router(
    inspection.router, prefix="/api/v1/inspections", tags=["Inspections"]
)
fastapi_app.include_router(
    annual_survey.router, prefix="/api/v1/annual-surveys", tags=["Annual Surveys"]
)
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
fastapi_app.include_router(
    feedback.router,
    prefix="/api/v1/feedback",
    tags=["Feedback"],
)
fastapi_app.include_router(
    formulae.router,
    prefix="/api/v1/formulae",
    tags=["Formulae"],
)
fastapi_app.include_router(
    contractor_analytics.router,
    prefix="/api/v1/contractor-analytics",
    tags=["Contractor Analytics"],
)
# app.include_router(survey.router, prefix="/api/v1/surveys", tags=["Surveys"])


# Include routers
@fastapi_app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):  # pylint: disable=unused-argument
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail, "status_code": exc.status_code},
    )


@fastapi_app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):  # pylint: disable=unused-argument
    """Handle validation errors without exposing internal Pydantic details."""
    simplified_errors = []
    for error in exc.errors():
        # Get a clean path to the field (e.g., "query -> limit")
        field = " -> ".join([str(loc) for loc in error.get("loc", [])])
        message = error.get("msg", "Invalid value")
        simplified_errors.append({"field": field, "message": message})

    return JSONResponse(
        status_code=422,
        content={
            "message": "Validation error",
            "errors": simplified_errors,
            "status_code": 422,
        },
    )


@fastapi_app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):  # pylint: disable=unused-argument
    """Handle general exceptions, log to file, and return a UUID for tracking."""
    error_id = str(uuid.uuid4())
    error_type = type(exc).__name__
    error_msg = str(exc)

    # Extract filename and line number from traceback
    tb_list = traceback.extract_tb(exc.__traceback__)
    if tb_list:
        last_frame = tb_list[-1]
        filename = os.path.basename(last_frame.filename)
        line_number = last_frame.lineno
        location = f"{filename}:{line_number}"
    else:
        location = "unknown"

    # Save full traceback to a file
    try:
        os.makedirs("logs", exist_ok=True)
        log_file_path = os.path.join("logs", f"error-{error_id}.txt")
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(f"Error ID: {error_id}\n")
            f.write(f"Type: {error_type}\n")
            f.write(f"Message: {error_msg}\n")
            f.write(f"Location: {location}\n")
            f.write("-" * 20 + " TRACEBACK " + "-" * 20 + "\n")
            f.write(traceback.format_exc())
    except Exception as log_exc:
        logger.error(f"Failed to save error log to file: {str(log_exc)}")

    # Log the full error for debugging on the server
    logger.error(
        f"Unhandled exception [{error_id}]: {error_type}: {error_msg} at {location}",
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error occurred.",
            "error_id": error_id,
            "error_type": error_type,
            "error_trace": f"{error_msg} (at {location})",
            "status_code": 500,
        },
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
        server_header=False,
    )
