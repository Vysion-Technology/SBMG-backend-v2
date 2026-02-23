from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = "sqlite+aiosqlite:///./test.db"

    # JWT Settings
    jwt_secret_key: str = "your-secret-key-here-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 43200

    # S3/MinIO Settings
    s3_endpoint_url: Optional[str] = None
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    s3_bucket_name: str = "sbm-complaints"

    # FCM Settings
    fcm_credential_path: Optional[str] = "firebase.json"

    # Trackverse API Settings
    trackverse_api_url: str = "https://api.trackverse.in/api/public/tracking/v0/device"
    trackverse_api_key: str = "NT-20250001332338322F488A3E78AC07DD24BF"
    trackverse_username: str = "deepakgupta"
    trackverse_password: str = "123456"

    # Application
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings = Settings()
