"""Custom exceptions for attendance service errors."""


class AttendanceServiceError(Exception):
    """Custom exception for attendance service errors."""


class AttemptingToLogAttendanceForAnotherUserError(AttendanceServiceError):
    """Custom exception for attempting to log attendance for another user."""


class NoContractorForVillageError(AttendanceServiceError):
    """Custom exception for no contractor found for the village."""
