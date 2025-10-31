"""Database-related exceptions."""

class SBMGRDatabaseException(Exception):
    """Base exception for SBMGR database errors."""

class TooMuchDataAskedException(SBMGRDatabaseException):
    """Exception raised when too much data is requested from the database."""


class DataRequestedForCreationAlreadyExistsException(SBMGRDatabaseException):
    """Exception raised when data requested for creation already exists in the database."""
