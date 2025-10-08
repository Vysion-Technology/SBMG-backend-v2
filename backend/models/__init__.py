"""
Models package initialization.
Import all models here to ensure they are registered with SQLAlchemy.
"""

# Import all database models to register them with SQLAlchemy Base
from models.database.auth import Role, User, PositionHolder, PublicUser, PublicUserToken
from models.database.geography import District, Block, Village
from models.database.complaint import (
    ComplaintType,
    ComplaintTypeGeographicalEligibility,
    ComplaintStatus,
    Complaint,
    ComplaintAssignment,
    ComplaintMedia,
    ComplaintComment,
)
from models.database.fcm_device import UserDeviceToken, PublicUserDeviceToken

__all__ = [
    # Auth models
    "Role",
    "User",
    "PositionHolder",
    "PublicUser",
    "PublicUserToken",
    # Geography models
    "District",
    "Block",
    "Village",
    # Complaint models
    "ComplaintType",
    "ComplaintTypeGeographicalEligibility",
    "ComplaintStatus",
    "Complaint",
    "ComplaintAssignment",
    "ComplaintMedia",
    "ComplaintComment",
    # FCM device models
    "UserDeviceToken",
    "PublicUserDeviceToken",
]
