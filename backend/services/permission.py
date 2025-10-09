from sqlalchemy.ext.asyncio import AsyncSession

from models.database.auth import User


class PermissionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def is_smd(self, current_user: User) -> bool:
        """Check if the user is a State Mission Director (SMD)."""
        return (
            current_user.district_id is None
            and current_user.block_id is None
            and current_user.village_id is None
        )

    def is_ceo(self, current_user: User) -> bool:
        """Check if the user is a Chief Executive Officer (CEO)."""
        return (
            current_user.district_id is not None
            and current_user.block_id is None
            and current_user.village_id is None
        )

    def is_bdo(self, current_user: User) -> bool:
        """Check if the user is a Block Development Officer (BDO)."""
        return (
            current_user.district_id is not None
            and current_user.block_id is not None
            and current_user.village_id is None
        )

    def is_vdo(self, current_user: User) -> bool:
        """Check if the user is a Village Development Officer (VDO)."""
        return (
            current_user.district_id is not None
            and current_user.block_id is not None
            and current_user.village_id is not None
        )

    def valid_sender_receiver_pair(self, sender: User, receiver: User) -> bool:
        """Check if the sender and receiver form a valid pair based on their roles."""
        if self.is_smd(sender):
            return True  # SMD can send to anyone
        elif self.is_ceo(sender):
            return (
                receiver.district_id == sender.district_id
                and receiver.block_id is not None
            )
        elif self.is_bdo(sender):
            return (
                receiver.block_id == sender.block_id and receiver.village_id is not None
            )
        elif self.is_vdo(sender):
            return receiver.village_id == sender.village_id
        return False
