from datetime import date
from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey, Date, Boolean, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class VolunteerRegistration(Base):
    """
    Model for volunteer registration details.
    """
    __tablename__ = "volunteer_registrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    public_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("public_users.id"), nullable=False, index=True)
    
    # Personal Information
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String, nullable=False)  # Male / Female / Other
    aadhar_number: Mapped[str] = mapped_column(String, nullable=False, index=True)
    mobile_number: Mapped[str] = mapped_column(String, nullable=False)
    alternate_mobile: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Address Details
    state: Mapped[str] = mapped_column(String, default="Rajasthan")
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey("districts.id"), nullable=False)
    block_id: Mapped[int] = mapped_column(Integer, ForeignKey("blocks.id"), nullable=False)
    gp_id: Mapped[int] = mapped_column(Integer, ForeignKey("gram_panchayats.id"), nullable=False)
    village_name: Mapped[str] = mapped_column(String, nullable=False)
    ward_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    full_address: Mapped[str] = mapped_column(Text, nullable=False)
    pin_code: Mapped[str] = mapped_column(String, nullable=False)

    # Educational & Occupational Background
    highest_qualification: Mapped[str] = mapped_column(String, nullable=False)
    current_occupation: Mapped[str] = mapped_column(String, nullable=False)  # Farmer / Student / Homemaker / Self-employed / Other
    organization_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Volunteer Service Details
    service_types: Mapped[List[str]] = mapped_column(JSON, nullable=False)  # List of selected service types
    preferred_days: Mapped[List[str]] = mapped_column(JSON, nullable=False)  # List of days (Mon-Sun)
    hours_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    commitment_duration: Mapped[str] = mapped_column(String, nullable=False)  # 1 month / 3 months / etc.

    # Skills & Physical Capability
    fitness_level: Mapped[str] = mapped_column(String, nullable=False)  # Fit / Moderate / Differently-abled
    relevant_skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    willing_to_work_other_villages: Mapped[bool] = mapped_column(Boolean, default=False)
    can_bring_more_volunteers: Mapped[bool] = mapped_column(Boolean, default=False)
    additional_volunteers_count: Mapped[int] = mapped_column(Integer, default=0)

    # Identity & Declaration
    category: Mapped[str] = mapped_column(String, nullable=False)  # General / SC / ST / OBC
    declaration_accepted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    public_user = relationship("PublicUser")
    district = relationship("District")
    block = relationship("Block")
    gp = relationship("GramPanchayat")
