import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = os.getenv("DATABASE_URL") or "sqlite+aiosqlite:///./test.db"
    
    # JWT Settings
    secret_key: str = os.getenv("JWT_SECRET_KEY") or "your-secret-key-here-change-in-production"
    algorithm: str = os.getenv("JWT_ALGORITHM") or "HS256"
    access_token_expire_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    
    # S3/MinIO Settings
    s3_endpoint_url: Optional[str] = os.getenv("S3_ENDPOINT_URL")
    s3_access_key: Optional[str] = os.getenv("S3_ACCESS_KEY")
    s3_secret_key: Optional[str] = os.getenv("S3_SECRET_KEY")
    s3_bucket_name: str = os.getenv("S3_BUCKET_NAME") or "sbm-complaints"
    
    # FCM Settings
    fcm_credential_path: Optional[str] = os.getenv("FCM_CREDENTIAL_PATH") or "firebase.json"
    
    # Application
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Convert environment variable names to uppercase
        case_sensitive = False


# Global settings instance
settings = Settings()