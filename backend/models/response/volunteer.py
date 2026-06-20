from datetime import date
from typing import List, Optional
from pydantic import BaseModel, field_validator


class VolunteerResponse(BaseModel):
    """
    Response model for volunteer registration details.
    """
    id: int
    full_name: str
    date_of_birth: date
    gender: str
    mobile_number: str
    alternate_mobile: Optional[str] = None
    email: Optional[str] = None
    photo_url: Optional[str] = None
    
    # Address
    state: str
    district_name: str
    block_name: Optional[str] = None
    gp_name: Optional[str] = None
    village_name: Optional[str] = None
    ward_number: Optional[str] = None
    full_address: str
    pin_code: str

    # Background
    highest_qualification: str
    current_occupation: str
    organization_name: Optional[str] = None

    # Service
    service_types: List[str]
    preferred_days: List[str]
    hours_per_week: int
    commitment_duration: str

    # Skills
    fitness_level: str
    relevant_skills: Optional[str] = None
    willing_to_work_other_villages: bool
    can_bring_more_volunteers: bool
    additional_volunteers_count: int

    category: str

    @field_validator("photo_url")
    @classmethod
    def format_photo_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith("/") and not v.startswith("http"):
            return f"/{v}"
        return v
    
    class Config:
        from_attributes = True
