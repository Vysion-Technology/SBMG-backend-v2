"""Exceptions for position holder service."""

class PositionHolderError(Exception):
    """Custom exception for position holder service errors."""

class ActivePositionHolderExistsError(PositionHolderError):
    """Custom exception for attempting to create a position holder when one already exists."""