import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from controllers import citizen, event
from controllers import auth, complaints, admin, public, user_management
from controllers import login_management, person_management
from controllers import geography, consolidated_reporting, attendance


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events."""
    # Startup
    yield
    # Shutdown (if needed)


app = FastAPI(
    title="SBM Gramin Rajasthan API",
    description="Swachh Bharat Mission (Gramin) - Rajasthan Complaint Management System",
    version="1.0.0",
    lifespan=lifespan,
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
app.include_router(login_management.router, prefix="/api/v1/login-management", tags=["Login User Management"])
app.include_router(person_management.router, prefix="/api/v1/person-management", tags=["Person Management"])
app.include_router(user_management.router, prefix="/api/v1/user-management", tags=["User Management (Legacy)"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(complaints.router, prefix="/api/v1/complaints", tags=["Complaints"])
app.include_router(event.router, prefix="/api/v1/events", tags=["Events"])
app.include_router(public.router, prefix="/api/v1/public", tags=["Public"])
app.include_router(attendance.router, prefix="/api/v1/attendance", tags=["Attendance"])
# app.include_router(reporting.router, prefix="/api/v1/reports", tags=["Reporting (Legacy)"])

# New consolidated reporting router with perfect RBAC and optimized queries
app.include_router(consolidated_reporting.router, prefix="/api/v1/reports", tags=["Advanced Reporting"])


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail, "status_code": exc.status_code})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    return JSONResponse(status_code=500, content={"message": "Internal server error", "status_code": 500})


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    uvicorn.run("main:app", host=host, port=port, reload=os.getenv("DEBUG", "false").lower() == "true")
