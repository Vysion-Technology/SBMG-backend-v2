"""Utility functions for role-based access control (RBAC) in FastAPI."""

from typing import List

from fastapi import HTTPException, status, Depends
from controllers.auth import get_current_active_user, UserRole
from models.database.auth import User


class PermissionChecker:
    """Check permissions based on user role and geographical location."""

    @staticmethod
    def user_has_role(user: User, required_roles: List[UserRole]) -> bool:
        """Check if user has any of the required roles."""
        # If user has no village, block, or district, they are considered ADMIN
        if not user.gp_id and not user.block_id and not user.district_id:
            return True  # Admin access
        if not user.gp_id and not user.block_id and user.district_id:
            if UserRole.CEO in required_roles:
                return True  # CEO access
        if not user.gp_id and user.block_id and user.district_id:
            if UserRole.BDO in required_roles:
                return True  # BDO access
        if user.gp_id and user.block_id and user.district_id and "contractor" not in required_roles:
            if UserRole.VDO in required_roles:
                return True  # VDO access
        if user.gp_id and user.block_id and user.district_id:
            if UserRole.WORKER in required_roles:
                return True  # Worker access
        user_roles = [pos.role.name for pos in user.positions if pos.role]
        return any(role in user_roles for role in required_roles)


async def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Require admin or superadmin role."""
    if not PermissionChecker.user_has_role(current_user, [UserRole.SUPERADMIN, UserRole.ADMIN]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return current_user


async def require_staff_role(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Require any staff role (not public)."""
    staff_roles = [
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
        UserRole.CEO,
        UserRole.BDO,
        UserRole.VDO,
        UserRole.WORKER,
    ]
    if not PermissionChecker.user_has_role(current_user, staff_roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff role required")
    return current_user


async def require_worker_role(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Require worker role."""
    if not PermissionChecker.user_has_role(current_user, [UserRole.WORKER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Worker role required")
    return current_user
