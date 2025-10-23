from typing import Optional, List
from pydantic import BaseModel

from models.base import BlockBase, GPBase


class DistrictResponse(BaseModel):
    """District response model."""

    id: int
    name: str
    description: Optional[str] = None


class DistrictDetailResponse(BaseModel):
    """Detailed district response with counts."""

    id: int
    name: str
    description: Optional[str] = None
    blocks_count: int
    villages_count: int
    complaints_count: int


class BlockResponse(BaseModel):
    """Block response model."""

    id: int
    name: str
    description: Optional[str] = None
    district_id: int


class BlockDetailResponse(BaseModel):
    """Detailed block response with counts."""

    id: int
    name: str
    description: Optional[str] = None
    district_id: int
    district_name: Optional[str] = None
    villages_count: int
    complaints_count: int


class GPResponse(BaseModel):
    """Gram Panchayat response model."""

    id: int
    name: str
    description: Optional[str] = None
    block_id: int
    district_id: int


class VillageResponse(BaseModel):
    """Village response model."""

    id: int
    name: str
    description: Optional[str] = None
    gp_id: int


class GPDetailResponse(BaseModel):
    """Detailed gram panchayat response with counts."""

    id: int
    name: str
    description: Optional[str] = None
    block_id: int
    district_id: int
    block_name: Optional[str] = None
    district_name: Optional[str] = None
    complaints_count: int


class CreateBlockRequest(BlockBase):
    """Request model for creating a block."""



class UpdateBlockRequest(BlockBase):
    """Request model for updating a block."""



class CreateGPRequest(GPBase):
    """Request model for creating a gram panchayat."""



class UpdateGPRequest(GPBase):
    """Request model for updating a Gram Panchayat."""



# Pagination and listing models
class GeographyListResponse(BaseModel):
    """Generic list response for geography entities."""

    items: List[BaseModel]
    total: int
    page: int
    size: int
    pages: int


class DistrictListResponse(BaseModel):
    """District list response."""

    items: List[DistrictResponse]
    total: int
    page: int
    size: int
    pages: int


class BlockListResponse(BaseModel):
    """Block list response."""

    items: List[BlockResponse]
    total: int
    page: int
    size: int
    pages: int


class GPListResponse(BaseModel):
    """Gram Panchayat list response."""

    items: List[GPResponse]
    total: int
    page: int
    size: int
    pages: int


# Error response models
class ErrorResponse(BaseModel):
    """Standard error response."""

    message: str
    status_code: int
    detail: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response."""

    message: str
    status_code: int
    errors: List[dict[str, str]]


# Hierarchical response models
class DistrictWithBlocksResponse(BaseModel):
    """District with its blocks."""

    id: int
    name: str
    description: Optional[str] = None
    blocks: List[BlockResponse]


class BlockWithGPResponse(BaseModel):
    """Block with its villages."""

    id: int
    name: str
    description: Optional[str] = None
    district_id: int
    district_name: Optional[str] = None
    gps: List[GPResponse]


class GeographyHierarchyResponse(BaseModel):
    """Complete geography hierarchy."""

    districts: List[DistrictWithBlocksResponse]


# Bulk operation models
class BulkDeleteRequest(BaseModel):
    """Request for bulk delete operations."""

    ids: List[int]


class BulkDeleteResponse(BaseModel):
    """Response for bulk delete operations."""

    deleted_count: int
    failed_ids: List[int]
    errors: List[str]
