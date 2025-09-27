from typing import Any, List, Optional
from auth_utils import UserRole
from models.database.auth import User
from models.database.complaint import Complaint, ComplaintAssignment
from sqlalchemy import select, or_


def get_user_jurisdiction_filter(user: User) -> Optional[Any]:
        """Get jurisdiction filter based on user's roles and positions."""
        user_roles = [pos.role.name for pos in user.positions if pos.role]
        
        if UserRole.ADMIN in user_roles:
            return None  # Admin can see everything
        
        jurisdiction_filters: List[Any] = []
        
        for position in user.positions:
            if position.role.name == UserRole.CEO and position.district_id:
                jurisdiction_filters.append(Complaint.district_id == position.district_id)
            elif position.role.name == UserRole.BDO and position.block_id:
                jurisdiction_filters.append(Complaint.block_id == position.block_id)
            elif position.role.name == UserRole.VDO and position.village_id:
                jurisdiction_filters.append(Complaint.village_id == position.village_id)
            elif position.role.name == UserRole.WORKER:
                # Workers can only see assigned complaints
                jurisdiction_filters.append(
                    Complaint.id.in_(
                        select(ComplaintAssignment.complaint_id).where(
                            ComplaintAssignment.user_id == user.id
                        )
                    )
                )
        
        return or_(*jurisdiction_filters) if jurisdiction_filters else None