import logging
from typing import List, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from models.database.auth import User, PublicUser
from models.database.fcm_device import UserDeviceToken, PublicUserDeviceToken
from models.database.complaint import Complaint
from models.database.geography import GramPanchayat
from services.fcm_service import fcm_service

logger = logging.getLogger(__name__)


async def notify_workers_on_new_complaint(
    db: AsyncSession,
    complaint: Complaint,
) -> None:
    """
    Send notification to all workers in the village where the complaint was created

    Args:
        db: Database session
        complaint: The newly created complaint
    """
    try:
        # Get all users who are workers in this village
        # We need to find users with WORKER role assigned to this village
        from models.database.auth import PositionHolder, Role

        result = await db.execute(
            select(User, UserDeviceToken.fcm_token)
            .join(PositionHolder, User.id == PositionHolder.user_id)
            .join(Role, PositionHolder.role_id == Role.id)
            .join(UserDeviceToken, User.id == UserDeviceToken.user_id)
            .where(
                and_(
                    Role.name == "WORKER",
                    PositionHolder.village_id == complaint.gp_id,
                    User.is_active.is_(True),
                )
            )
            .distinct()
        )

        workers = result.all()

        if not workers:
            logger.info("No workers found for village %d", complaint.gp_id)
            return

        # Collect all FCM tokens
        tokens = [worker[1] for worker in workers]

        # Get village name for better notification
        village_result = await db.execute(
            select(GramPanchayat).where(GramPanchayat.id == complaint.gp_id)
        )
        village = village_result.scalar_one_or_none()
        village_name = village.name if village else "your village"

        # Send notification
        result = await fcm_service.send_notification(
            tokens=tokens,
            title="New Complaint Assigned",
            body=f"A new complaint has been registered in {village_name}. Please review and take action.",
            data={
                "type": "new_complaint",
                "complaint_id": str(complaint.id),
                "village_id": str(complaint.gp_id),
                "village_name": village_name,
            },
        )

        # Clean up invalid tokens
        if result.invalid_tokens:
            await _cleanup_invalid_tokens(db, result.invalid_tokens, UserDeviceToken)

        logger.info(
            f"Sent new complaint notification to {result.success_count} workers "
            f"for complaint {complaint.id}"
        )

    except Exception as e:
        logger.error(f"Error sending notification to workers: {e}")


async def notify_user_on_complaint_status_update(
    db: AsyncSession,
    complaint: Complaint,
    new_status_name: str,
) -> None:
    """
    Send notification to the user who created the complaint when status is updated

    Args:
        db: Database session
        complaint: The complaint that was updated
        new_status_name: The new status name
    """
    try:
        # Check if complaint was created by a public user (has mobile_number)
        if not complaint.mobile_number:
            logger.info(
                f"Complaint {complaint.id} has no mobile number, skipping notification"
            )
            return

        # Get public user and their device tokens
        result = await db.execute(
            select(PublicUser, PublicUserDeviceToken.fcm_token)
            .join(
                PublicUserDeviceToken,
                PublicUser.id == PublicUserDeviceToken.public_user_id,
            )
            .where(PublicUser.mobile_number == complaint.mobile_number)
            .distinct()
        )

        public_users = result.all()

        if not public_users:
            logger.info(
                f"No public user devices found for mobile {complaint.mobile_number}"
            )
            return

        # Collect all FCM tokens
        tokens = [user[1] for user in public_users]

        # Send notification
        result = await fcm_service.send_notification(
            tokens=tokens,
            title="Complaint Status Updated",
            body=f"Your complaint #{complaint.id} status has been updated to: {new_status_name}",
            data={
                "type": "status_update",
                "complaint_id": str(complaint.id),
                "new_status": new_status_name,
            },
        )

        # Clean up invalid tokens
        if result.invalid_tokens:
            await _cleanup_invalid_tokens(
                db, result.invalid_tokens, PublicUserDeviceToken
            )

        logger.info(
            f"Sent status update notification to {result.success_count} devices "
            f"for complaint {complaint.id}"
        )

    except Exception as e:
        logger.error(f"Error sending notification to public user: {e}")


async def _cleanup_invalid_tokens(
    db: AsyncSession,
    invalid_tokens: List[str],
    model_class: type[Union[UserDeviceToken, PublicUserDeviceToken]],
) -> None:
    """
    Remove invalid FCM tokens from the database

    Args:
        db: Database session
        invalid_tokens: List of invalid FCM tokens
        model_class: Either UserDeviceToken or PublicUserDeviceToken
    """
    try:
        for token in invalid_tokens:
            result = await db.execute(
                select(model_class).where(model_class.fcm_token == token)
            )
            device = result.scalar_one_or_none()

            if device:
                await db.delete(device)
                logger.info(f"Deleted invalid FCM token: {token[:20]}...")

        await db.commit()

    except Exception as e:
        logger.error(f"Error cleaning up invalid tokens: {e}")
        await db.rollback()
