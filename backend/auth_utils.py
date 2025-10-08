from typing import List
from enum import Enum
from functools import wraps

from fastapi import HTTPException, status, Depends
from controllers.auth import get_current_active_user
from models.database.auth import User


class UserRole(str, Enum):
    """User roles in the system."""
    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    CEO = "CEO"  # District Collector
    BDO = "BDO"  # Block Development Officer
    VDO = "VDO"  # Village Development Officer
    WORKER = "WORKER"
    PUBLIC = "PUBLIC"


class PermissionChecker:
    """Check permissions based on user role and geographical location."""
    
    @staticmethod
    def user_has_role(user: User, required_roles: List[str]) -> bool:
        """Check if user has any of the required roles."""
        user_roles = [pos.role.name for pos in user.positions if pos.role]
        return any(role in user_roles for role in required_roles)
    
    @staticmethod
    def user_can_access_district(user: User, district_id: int) -> bool:
        """Check if user can access a specific district."""
        # SuperAdmin and Admin can access everything
        if PermissionChecker.user_has_role(user, [UserRole.SUPERADMIN, UserRole.ADMIN]):
            return True
        
        # CEO can access their district
        for position in user.positions:
            if position.role.name == UserRole.CEO and position.district_id == district_id:
                return True
            
            # BDO can access if their block is in the district
            if position.role.name == UserRole.BDO and position.district_id == district_id:
                return True
            
            # VDO can access if their village is in the district
            if position.role.name == UserRole.VDO and position.district_id == district_id:
                return True
            
            # Worker can access if assigned to work in the district
            if position.role.name == UserRole.WORKER and position.district_id == district_id:
                return True
        
        return False
    
    @staticmethod
    def user_can_access_block(user: User, block_id: int) -> bool:
        """Check if user can access a specific block."""
        # SuperAdmin and Admin can access everything
        if PermissionChecker.user_has_role(user, [UserRole.SUPERADMIN, UserRole.ADMIN]):
            return True
        
        for position in user.positions:
            # CEO can access all blocks in their district
            if position.role.name == UserRole.CEO and position.district_id:
                # Need to check if block belongs to their district
                return True
            
            # BDO can access their block
            if position.role.name == UserRole.BDO and position.block_id == block_id:
                return True
            
            # VDO can access if their village is in the block
            if position.role.name == UserRole.VDO and position.block_id == block_id:
                return True
            
            # Worker can access if assigned to work in the block
            if position.role.name == UserRole.WORKER and position.block_id == block_id:
                return True
        
        return False
    
    @staticmethod
    def user_can_access_village(user: User, village_id: int) -> bool:
        """Check if user can access a specific village."""
        # SuperAdmin and Admin can access everything
        if PermissionChecker.user_has_role(user, [UserRole.SUPERADMIN, UserRole.ADMIN]):
            return True
        
        for position in user.positions:
            # CEO can access all villages in their district
            if position.role.name == UserRole.CEO and position.district_id:
                # Need to check if village belongs to their district
                return True
            
            # BDO can access all villages in their block
            if position.role.name == UserRole.BDO and position.block_id:
                # Need to check if village belongs to their block
                return True
            
            # VDO can access their village
            if position.role.name == UserRole.VDO and position.village_id == village_id:
                return True
            
            # Worker can access if assigned to work in the village
            if position.role.name == UserRole.WORKER and position.village_id == village_id:
                return True
        
        return False


def require_roles(required_roles: List[str]):
    """Decorator to require specific roles for a route."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs (should be injected by dependency)
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not authenticated"
                )
            
            if not PermissionChecker.user_has_role(current_user, required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required roles: {required_roles}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Dependency functions for common role checks
async def require_superadmin(current_user: User = Depends(get_current_active_user)) -> User:
    """Require superadmin role."""
    if not PermissionChecker.user_has_role(current_user, [UserRole.SUPERADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SuperAdmin role required"
        )
    return current_user


async def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Require admin or superadmin role."""
    if not PermissionChecker.user_has_role(current_user, [UserRole.SUPERADMIN, UserRole.ADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return current_user


async def require_admin_or_ceo(current_user: User = Depends(get_current_active_user)) -> User:
    """Require admin, superadmin, or CEO role."""
    if not PermissionChecker.user_has_role(current_user, [UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.CEO]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or CEO role required"
        )
    return current_user


async def require_admin_or_ceo_or_bdo(current_user: User = Depends(get_current_active_user)) -> User:
    """Require admin, superadmin, CEO, or BDO role."""
    if not PermissionChecker.user_has_role(current_user, [UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.CEO, UserRole.BDO]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin, CEO, or BDO role required"
        )
    return current_user


async def require_staff_role(current_user: User = Depends(get_current_active_user)) -> User:
    """Require any staff role (not public)."""
    staff_roles = [UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.CEO, UserRole.BDO, UserRole.VDO, UserRole.WORKER]
    if not PermissionChecker.user_has_role(current_user, staff_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff role required"
        )
    return current_user

async def require_worker_role(current_user: User = Depends(get_current_active_user)) -> User:
    """Require worker role."""
    if not PermissionChecker.user_has_role(current_user, [UserRole.WORKER]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Worker role required"
        )
    return current_user