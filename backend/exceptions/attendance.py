class AttendanceServiceError(Exception):
    """Custom exception for attendance service errors."""

    pass


class AttemptingToLogAttendanceForAnotherUserError(AttendanceServiceError):
    """Custom exception for attempting to log attendance for another user."""

    pass


class NoContractorForVillageError(AttendanceServiceError):
    """Custom exception for no contractor found for the village."""

    pass
