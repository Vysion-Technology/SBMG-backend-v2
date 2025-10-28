"""Request models for contractor-related operations"""
from typing import Optional
from datetime import datetime

from pydantic import BaseModel


class CreateAgencyRequest(BaseModel):
    """Request model for creating an agency"""
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


class CreateContractorRequest(BaseModel):
    """Request model for creating a contractor"""
    agency_id: int
    person_name: Optional[str] = None
    person_phone: Optional[str] = None
    gp_id: int
    contract_start_date: Optional[datetime] = None
    contract_end_date: Optional[datetime] = None


class UpdateContractorRequest(BaseModel):
    """Request model for updating a contractor"""
    agency_id: Optional[int] = None
    person_name: Optional[str] = None
    person_phone: Optional[str] = None
    gp_id: Optional[int] = None
    contract_start_date: Optional[datetime] = None
    contract_end_date: Optional[datetime] = None
