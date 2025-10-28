"""Response model for deletion operations."""
from pydantic import BaseModel


class DeletionResponse(BaseModel):
    """Response model for deletion operations."""
    message: str
