import logging

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.database.auth import User, PublicUser, PublicUserToken
from models.database.fcm_device import UserDeviceToken, PublicUserDeviceToken
from models.requests.fcm_device import DeviceRegistrationRequest, DeviceRegistrationResponse
from auth_utils import get_current_active_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/staff/register-device", response_model=DeviceRegistrationResponse)
async def register_staff_device(
    request: DeviceRegistrationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Register or update FCM device token for staff users (Workers, VDOs, BDOs, etc.)
    """
    try:
        # Check if device already exists for this user
        result = await db.execute(
            select(UserDeviceToken).where(
                UserDeviceToken.user_id == current_user.id,
                UserDeviceToken.device_id == request.device_id,
            )
        )
        existing_device = result.scalar_one_or_none()

        if existing_device:
            # Update existing token
            existing_device.fcm_token = request.fcm_token
            existing_device.device_name = request.device_name
            existing_device.platform = request.platform
            logger.info(f"Updated FCM token for user {current_user.id}, device {request.device_id}")
        else:
            # Create new device token
            new_device = UserDeviceToken(
                user_id=current_user.id,
                device_id=request.device_id,
                fcm_token=request.fcm_token,
                device_name=request.device_name,
                platform=request.platform,
            )
            db.add(new_device)
            logger.info(f"Registered new FCM token for user {current_user.id}, device {request.device_id}")

        await db.commit()

        return DeviceRegistrationResponse(
            message="Device token registered successfully",
            device_id=request.device_id,
        )

    except Exception as e:
        logger.error(f"Error registering device token: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register device token",
        )


@router.post("/public/register-device", response_model=DeviceRegistrationResponse)
async def register_public_device(
    request: DeviceRegistrationRequest,
    token: str = Header(..., description="Public user token"),
    db: AsyncSession = Depends(get_db),
):
    """
    Register or update FCM device token for public users (citizens)
    """
    try:
        # Get public user from token
        result = await db.execute(
            select(PublicUserToken).where(PublicUserToken.token == token)
        )
        public_user_token = result.scalar_one_or_none()
        
        if not public_user_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing user token",
            )

        result = await db.execute(
            select(PublicUser).where(PublicUser.id == public_user_token.public_user_id)
        )
        public_user = result.scalar_one_or_none()
        
        if not public_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Public user not found",
            )

        # Check if device already exists for this public user
        result = await db.execute(
            select(PublicUserDeviceToken).where(
                PublicUserDeviceToken.public_user_id == public_user.id,
                PublicUserDeviceToken.device_id == request.device_id,
            )
        )
        existing_device = result.scalar_one_or_none()

        if existing_device:
            # Update existing token
            existing_device.fcm_token = request.fcm_token
            existing_device.device_name = request.device_name
            existing_device.platform = request.platform
            logger.info(f"Updated FCM token for public user {public_user.id}, device {request.device_id}")
        else:
            # Create new device token
            new_device = PublicUserDeviceToken(
                public_user_id=public_user.id,
                device_id=request.device_id,
                fcm_token=request.fcm_token,
                device_name=request.device_name,
                platform=request.platform,
            )
            db.add(new_device)
            logger.info(f"Registered new FCM token for public user {public_user.id}, device {request.device_id}")

        await db.commit()

        return DeviceRegistrationResponse(
            message="Device token registered successfully",
            device_id=request.device_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering public device token: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register device token",
        )


@router.delete("/staff/remove-device/{device_id}")
async def remove_staff_device(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Remove FCM device token for staff user
    """
    try:
        result = await db.execute(
            select(UserDeviceToken).where(
                UserDeviceToken.user_id == current_user.id,
                UserDeviceToken.device_id == device_id,
            )
        )
        device = result.scalar_one_or_none()

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found",
            )

        await db.delete(device)
        await db.commit()

        logger.info(f"Removed FCM token for user {current_user.id}, device {device_id}")

        return {"message": "Device token removed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing device token: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove device token",
        )
