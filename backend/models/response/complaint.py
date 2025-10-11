from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class MediaResponse(BaseModel):
    id: int
    media_url: str
    uploaded_at: datetime


class ComplaintResponse(BaseModel):
    id: int
    description: str
    mobile_number: Optional[str] = None
    status_name: str
    village_name: str
    block_name: str
    district_name: str
    lat: float
    long: float
    created_at: datetime
    updated_at: Optional[datetime]
    media_urls: List[str] = []
    media: List[MediaResponse] = []


class VerifyComplaintStatusResponse(BaseModel):
    complaint_id: int
    current_status: str
    message: str


class ComplaintCommentResponse(BaseModel):
    id: int
    complaint_id: int
    comment: str
    commented_at: datetime
    user_name: str


class ResolveComplaintResponse(BaseModel):
    message: str
    complaint_id: int


class MediaUploadResponse(BaseModel):
    id: int
    complaint_id: int
    media_url: str
    uploaded_at: datetime


class ComplaintStatusResponse(BaseModel):
    id: int
    status_name: str
    updated_at: Optional[datetime]


class DetailedComplaintResponse(BaseModel):
    id: int
    description: str
    mobile_number: Optional[str] = None
    complaint_type_id: int
    created_at: datetime
    status_id: int
    complaint_type: Optional[str] = None
    status: Optional[str] = None
    village_name: Optional[str] = None
    block_name: Optional[str] = None
    district_name: Optional[str] = None
    updated_at: Optional[datetime]
    media_urls: List[str] = []
    media: List[MediaResponse] = []
    comments: List[ComplaintCommentResponse] = []
    assigned_worker: Optional[str] = None
    assignment_date: Optional[datetime] = None


class CitizenStatusUpdateResponse(BaseModel):
    message: str
    complaint_id: int
    new_status: str
    updated_at: datetime
