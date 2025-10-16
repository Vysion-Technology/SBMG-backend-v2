from typing import Optional
from pydantic import BaseModel


class AttendanceLogRequest(BaseModel):
    """Request model for logging attendance (start of work)"""

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
