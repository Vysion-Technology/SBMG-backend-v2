from typing import Optional
from datetime import date
from pydantic import BaseModel


class AttendanceLogRequest(BaseModel):
    """Request model for logging attendance (start of work)"""
    date: date
    start_lat: str
    start_long: str
    village_id: Optional[int] = None
    remarks: Optional[str] = None


class AttendanceEndRequest(BaseModel):
    """Request model for ending attendance (end of work)"""
    attendance_id: int
    end_lat: str
    end_long: str
    remarks: Optional[str] = None


class AttendanceFilterRequest(BaseModel):
    """Request model for filtering attendance records"""
    contractor_id: Optional[int] = None
    village_id: Optional[int] = None
    block_id: Optional[int] = None
    district_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    page: int = 1
    limit: int = 10