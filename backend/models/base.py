"""Base models for geography entities."""
from typing import Optional
from pydantic import BaseModel


class DistrictBase(BaseModel):
    """Base district model."""

    name: str
    description: Optional[str] = None

class BlockBase(BaseModel):
    """Base block model."""

    name: str
    description: Optional[str] = None
    district_id: int

class GPBase(BaseModel):
    """Base village model."""

    name: str
    description: Optional[str] = None
    block_id: int
    district_id: int


class VillageBase(BaseModel):
    """Base village model (for villages table)."""

    name: str
    gp_id: int
    description: Optional[str] = None
