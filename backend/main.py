"""SBMG Rajasthan Backend Main Application."""

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from controllers import contractor
from controllers import citizen, event, scheme
from controllers import auth, complaints, admin, public
from controllers import geography, attendance
from controllers import fcm_device, inspection, notice, annual_survey
from controllers import position_holder


app = FastAPI(
    title="SBM Gramin Rajasthan API",
    description="Swachh Bharat Mission (Gramin) - Rajasthan Complaint Management System",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():
    """Root endpoint."""
    return {"message": "SBM Gramin Rajasthan API", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker."""
    return {"status": "healthy"}


# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(citizen.router, prefix="/api/v1/citizen", tags=["Citizen"])
app.include_router(geography.router, prefix="/api/v1/geography", tags=["Geography"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(position_holder.router, prefix="/api/v1/position-holders", tags=["Position Holders"])
app.include_router(complaints.router, prefix="/api/v1/complaints", tags=["Complaints"])
app.include_router(event.router, prefix="/api/v1/events", tags=["Events"])
app.include_router(public.router, prefix="/api/v1/public", tags=["Public"])
app.include_router(attendance.router, prefix="/api/v1/attendance", tags=["DailyAttendance"])
app.include_router(scheme.router, prefix="/api/v1/schemes", tags=["Schemes"])
app.include_router(fcm_device.router, prefix="/api/v1/notifications", tags=["FCM Notifications"])
app.include_router(inspection.router, prefix="/api/v1/inspections", tags=["Inspections"])
app.include_router(annual_survey.router, prefix="/api/v1/annual-surveys", tags=["Annual Surveys"])
app.include_router(notice.router, prefix="/api/v1/notices", tags=["Notices"])
app.include_router(
    contractor.router,
    prefix="/api/v1/contractors",
    tags=["Agency and Contractor Management"],
)
# app.include_router(survey.router, prefix="/api/v1/surveys", tags=["Surveys"])


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):  # pylint: disable=unused-argument
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail, "status_code": exc.status_code},
    )


@app.exception_handler(Exception)
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
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )
