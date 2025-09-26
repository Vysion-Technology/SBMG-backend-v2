from typing import Optional, List
from pydantic import BaseModel


class DistrictBase(BaseModel):
    """Base district model."""

    name: str
    description: Optional[str] = None


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


class BlockBase(BaseModel):
    """Base block model."""

    name: str
    description: Optional[str] = None
    district_id: int


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


class VillageBase(BaseModel):
    """Base village model."""

    name: str
    description: Optional[str] = None
    block_id: int
    district_id: int


class VillageResponse(BaseModel):
    """Village response model."""

    id: int
    name: str
    description: Optional[str] = None
    block_id: int
    district_id: int


class VillageDetailResponse(BaseModel):
    """Detailed village response with counts."""

    id: int
    name: str
    description: Optional[str] = None
    block_id: int
    district_id: int
    block_name: Optional[str] = None
    district_name: Optional[str] = None
    complaints_count: int


# Request models
class CreateDistrictRequest(DistrictBase):
    """Request model for creating a district."""

    pass


class UpdateDistrictRequest(DistrictBase):
    """Request model for updating a district."""

    pass


class CreateBlockRequest(BlockBase):
    """Request model for creating a block."""

    pass


class UpdateBlockRequest(BlockBase):
    """Request model for updating a block."""

    pass


class CreateVillageRequest(VillageBase):
    """Request model for creating a village."""

    pass


class UpdateVillageRequest(VillageBase):
    """Request model for updating a village."""

    pass


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


class VillageListResponse(BaseModel):
    """Village list response."""

    items: List[VillageResponse]
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


class BlockWithVillagesResponse(BaseModel):
    """Block with its villages."""

    id: int
    name: str
    description: Optional[str] = None
    district_id: int
    district_name: Optional[str] = None
    villages: List[VillageResponse]


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
