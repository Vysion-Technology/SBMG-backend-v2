import os
import logging
from typing import List, Dict, Optional

import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger(__name__)


class FCMService:
    """Service for sending Firebase Cloud Messaging notifications"""

    def __init__(self):
        self._initialized = False
        self._initialize()

    def _initialize(self):
        """Initialize Firebase Admin SDK"""
        if self._initialized:
            return

        # Check if already initialized
        if firebase_admin._apps:
            self._initialized = True
            logger.info("Firebase Admin SDK already initialized")
            return

        # Try to get credentials path from environment
        fcm_credential_path = os.environ.get("FCM_CREDENTIAL_PATH")

        if fcm_credential_path and os.path.exists(fcm_credential_path):
            try:
                cred = credentials.Certificate(fcm_credential_path)
                firebase_admin.initialize_app(cred)
                self._initialized = True
                logger.info(f"Firebase Admin SDK initialized from {fcm_credential_path}")
            except Exception as e:
                logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
        else:
            logger.warning(
                "FCM_CREDENTIAL_PATH not set or file doesn't exist. "
                "FCM notifications will be disabled."
            )

    def is_available(self) -> bool:
        """Check if FCM service is available"""
        return self._initialized

    async def send_notification(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
    ) -> Dict[str, int]:
        """
        Send notification to multiple devices

        Args:
            tokens: List of FCM device tokens
            title: Notification title
            body: Notification body
            data: Optional custom data payload

        Returns:
            Dictionary with success_count and failure_count
        """
        if not self.is_available():
            logger.warning("FCM service not available, skipping notification")
            return {"success_count": 0, "failure_count": 0}

        if not tokens:
            logger.info("No tokens provided, skipping notification")
            return {"success_count": 0, "failure_count": 0}

        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                tokens=tokens,
            )

            response = messaging.send_multicast(message)

            # Log invalid tokens
            if response.failure_count > 0:
                invalid_tokens = []
                for i, result in enumerate(response.responses):
                    if not result.success and result.exception:
                        if result.exception.code in ("UNREGISTERED", "NOT_FOUND"):
                            invalid_tokens.append(tokens[i])
                            logger.warning(f"Invalid token detected: {tokens[i][:20]}...")

                if invalid_tokens:
                    logger.info(f"Found {len(invalid_tokens)} invalid tokens for cleanup")

            logger.info(
                f"Sent FCM notification: {response.success_count} successful, "
                f"{response.failure_count} failed"
            )

            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "invalid_tokens": invalid_tokens if response.failure_count > 0 else [],
            }

        except Exception as e:
            logger.error(f"Error sending FCM notification: {e}")
            return {"success_count": 0, "failure_count": len(tokens), "invalid_tokens": []}

    async def send_to_user(
        self,
        user_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
    ) -> Dict[str, int]:
        """
        Convenience method to send notification to a user's devices

        Args:
            user_tokens: List of user's FCM tokens
            title: Notification title
            body: Notification body
            data: Optional custom data payload

        Returns:
            Dictionary with success_count and failure_count
        """
        return await self.send_notification(user_tokens, title, body, data)


# Global FCM service instance
fcm_service = FCMService()
