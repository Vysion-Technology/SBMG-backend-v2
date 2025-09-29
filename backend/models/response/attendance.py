from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel


class AttendanceResponse(BaseModel):
    """Response model for attendance record"""
    id: int
    contractor_id: int
    contractor_name: Optional[str]
    village_id: Optional[int]
    village_name: Optional[str]
    block_name: Optional[str]
    district_name: Optional[str]
    date: date
    start_time: Optional[datetime]
    start_lat: str
    start_long: str
    end_time: Optional[datetime]
    end_lat: Optional[str]
    end_long: Optional[str]
    remarks: Optional[str]
    
    class Config:
        from_attributes = True


class AttendanceListResponse(BaseModel):
    """Response model for attendance list"""
    attendances: List[AttendanceResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class AttendanceSummaryResponse(BaseModel):
    """Response model for attendance summary"""
    contractor_id: int
    contractor_name: Optional[str]
    total_days: int
    present_days: int
    attendance_percentage: float
    last_attendance: Optional[date]


class AttendanceStatsResponse(BaseModel):
    """Response model for attendance statistics"""
    total_workers: int
    present_today: int
    absent_today: int
    attendance_rate: float
    summaries: List[AttendanceSummaryResponse]