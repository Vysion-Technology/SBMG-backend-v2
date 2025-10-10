"""Response models for analytics across different modules."""

from datetime import datetime, date
from enum import Enum
from typing import List
from pydantic import BaseModel

from models.internal import GeoTypeEnum


class ComplaintStatusEnum(str, Enum):
    """Enum for complaint status types."""

    OPEN = "OPEN"
    VERIFIED = "VERIFIED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    COMPLETED = "COMPLETED"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    REJECTED = "REJECTED"


class GeographyComplaintCountByStatusResponse(BaseModel):
    """Response model for complaint count by status at a geographical level."""

    geography_id: int
    geography_name: str
    status_id: int
    status: ComplaintStatusEnum
    count: int


class ComplaintAnalyticsResponse(BaseModel):
    """Response model for complaint analytics aggregated by geography type."""

    geo_type: GeoTypeEnum
    response: List[GeographyComplaintCountByStatusResponse]


class AttendanceStatusEnum(str, Enum):
    """Enum for attendance status types."""

    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    ON_LEAVE = "ON_LEAVE"
    HALF_DAY = "HALF_DAY"


class GeographyAttendanceCountResponse(BaseModel):
    """Response model for attendance count at a geographical level."""

    geography_id: int
    geography_name: str
    total_contractors: int
    present_count: int
    absent_count: int
    attendance_rate: float


class AttendanceAnalyticsResponse(BaseModel):
    """Response model for attendance analytics aggregated by geography type."""

    geo_type: GeoTypeEnum
    date: date
    response: List[GeographyAttendanceCountResponse]


class DaySummaryAttendanceResponse(BaseModel):
    """Response model for a single day's attendance summary."""

    contractor_id: int
    contractor_name: str
    village_id: int
    village_name: str
    block_id: int
    block_name: str
    district_id: int
    district_name: str
    date: date
    start_time: datetime | None
    end_time: datetime | None
    status: AttendanceStatusEnum
    duration_hours: float | None
    remarks: str | None


class DayAttendanceSummaryResponse(BaseModel):
    """Response model for day attendance summary."""

    date: date
    geo_type: GeoTypeEnum
    total_contractors: int
    present_count: int
    absent_count: int
    attendance_rate: float
    attendances: List[DaySummaryAttendanceResponse]
