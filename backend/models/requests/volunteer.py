from datetime import date
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class VolunteerRegistrationRequest(BaseModel):
    """
    Request model for volunteer registration.
    """
    full_name: str
    date_of_birth: date
    gender: str
    aadhar_number: str
    alternate_mobile: Optional[str] = None
    email: Optional[EmailStr] = None
    
    # Address Details
    district_id: int
    block_id: int
    gp_id: int
    village_name: str
    ward_number: Optional[str] = None
    full_address: str
    pin_code: str

    # Educational & Occupational Background
    highest_qualification: str
    current_occupation: str
    organization_name: Optional[str] = None

    # Volunteer Service Details
    service_types: List[str]
    preferred_days: List[str]
    hours_per_week: int
    commitment_duration: str

    # Skills & Physical Capability
    fitness_level: str
    relevant_skills: Optional[str] = None
    willing_to_work_other_villages: bool = False
    can_bring_more_volunteers: bool = False
    additional_volunteers_count: int = 0

    # Identity & Declaration
    category: str
    declaration_accepted: bool = Field(..., description="Must agree to contribute without financial expectation")
