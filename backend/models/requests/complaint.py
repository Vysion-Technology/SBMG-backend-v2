from pydantic import BaseModel
from typing import Optional

class CreateComplaintRequest(BaseModel):
    complaint_type_id: int
    village_id: int
    block_id: int
    district_id: int
    description: str
    mobile_number: Optional[str] = None


class UpdateComplaintStatusRequest(BaseModel):
    status_name: str


class AddCommentRequest(BaseModel):
    comment: str


class VerifyComplaintStatusRequest(BaseModel):
    complaint_id: int
    mobile_number: str


class ResolveComplaintRequest(BaseModel):
    resolution_comment: Optional[str] = None


class CitizenStatusUpdateRequest(BaseModel):
    complaint_id: int
    mobile_number: str
    new_status: str  # Should be "VERIFIED" or "RESOLVED"

