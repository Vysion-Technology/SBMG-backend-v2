from typing import Optional, Any
from pydantic import BaseModel


class AgencyResponse(BaseModel):
    """Response model for agency"""
    id: int
    name: str
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    
    class Config:
        from_attributes = True


class ContractorResponse(BaseModel):
    """Response model for contractor"""
    id: int
    agency: Optional[AgencyResponse]
    person_name: Optional[str]
    person_phone: Optional[str]
    village_id: Optional[int]
    village_name: Optional[str]
    block_name: Optional[str]
    district_name: Optional[str]
    contract_start_date: Optional[Any] = None
    contract_end_date: Optional[Any] = None
    
    class Config:
        from_attributes = True
