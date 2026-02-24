import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = "sqlite+aiosqlite:///./test.db"

    # JWT Settings
    jwt_secret_key: str = "your-secret-key-here-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 43200  # 30 days default
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15

    # S3/MinIO Settings
    s3_endpoint_url: Optional[str] = os.getenv("S3_ENDPOINT_URL")
    s3_access_key: Optional[str] = os.getenv("S3_ACCESS_KEY")
    s3_secret_key: Optional[str] = os.getenv("S3_SECRET_KEY")
    s3_bucket_name: str = os.getenv("S3_BUCKET_NAME") or "sbm-complaints"

    # FCM Settings
    fcm_credential_path: Optional[str] = (
        os.getenv("FCM_CREDENTIAL_PATH") or "firebase.json"
    )

    # Trackverse API Settings
    trackverse_api_url: str = (
        os.getenv("TRACKVERSE_API_URL")
        or "https://api.trackverse.in/api/public/tracking/v0/device"
    )
    trackverse_api_key: str = (
        os.getenv("TRACKVERSE_API_KEY") or "NT-20250001332338322F488A3E78AC07DD24BF"
    )
    trackverse_username: str = os.getenv("TRACKVERSE_USERNAME") or "deepakgupta"
    trackverse_password: str = os.getenv("TRACKVERSE_PASSWORD") or "123456"

    # Application
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Convert environment variable names to uppercase
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()
