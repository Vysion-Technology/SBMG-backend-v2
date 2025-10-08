from pydantic import BaseModel, Field
from typing import Optional


class DeviceRegistrationRequest(BaseModel):
    """Request model for registering a device token"""
    device_id: str = Field(..., description="Unique device identifier")
    fcm_token: str = Field(..., description="FCM registration token from client SDK")
    device_name: Optional[str] = Field(None, description="Device name/model")
    platform: Optional[str] = Field(None, description="Platform: ios, android, or web")


class DeviceRegistrationResponse(BaseModel):
    """Response model for device registration"""
    message: str
    device_id: str
