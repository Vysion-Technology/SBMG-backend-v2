"""Request models for notices."""

from typing import Optional, List

from pydantic import BaseModel, Field


class CreateNoticeTypeRequest(BaseModel):
    """Request model for creating a notice type."""

    name: str = Field(..., min_length=1, max_length=100, description="Name of the notice type")
    description: Optional[str] = Field(None, description="Description of the notice type")


class CreateNoticeRequest(BaseModel):
    """Request model for creating a notice."""

    notice_type_id: int = Field(..., description="Notice type ID (required)")
    district_id: Optional[int] = Field(None, description="District ID (optional)")
    block_id: Optional[int] = Field(None, description="Block ID (optional - to target specific block)")
    gp_id: Optional[int] = Field(None, description="Village ID (optional - to target specific village)")
    title: str = Field(..., min_length=1, max_length=500, description="Notice title")
    text: Optional[str] = Field(None, description="Notice text content")
    media_urls: Optional[List[str]] = Field(None, description="List of media URLs attached to the notice")


class CreateNoticeReplyRequest(BaseModel):
    """Request model for creating a notice reply."""

    reply_text: str = Field(..., min_length=1, description="Reply text content")
