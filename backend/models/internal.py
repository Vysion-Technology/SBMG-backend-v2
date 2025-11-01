"""Enum for geographical types."""
from enum import Enum


class GeoTypeEnum(str, Enum):
    """Enumeration for geographical types."""
    STATE = "STATE"
    DISTRICT = "DISTRICT"
    BLOCK = "BLOCK"
    GP = "VILLAGE"

class FeedbackFromEnum(str, Enum):
    """Enumeration for feedback source types."""
    AUTH_USER = "AUTH_USER"
    PUBLIC_USER = "PUBLIC_USER"
