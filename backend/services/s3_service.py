"""S3/MinIO service for file uploads and downloads."""

import uuid
from typing import Optional
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile
import logging

from config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """Service for handling S3/MinIO operations."""

    def __init__(self):
        """Initialize S3 client."""
        self.client = None
        self.bucket_name = settings.s3_bucket_name

        if settings.s3_endpoint_url and settings.s3_access_key and settings.s3_secret_key:
            try:
                self.client = boto3.client(
                    "s3",
                    endpoint_url=settings.s3_endpoint_url,
                    aws_access_key_id=settings.s3_access_key,
                    aws_secret_access_key=settings.s3_secret_key,
                    region_name="us-east-1",  # MinIO doesn't care about region
                )
                logger.info(f"S3 client initialized with endpoint: {settings.s3_endpoint_url}")
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
                self.client = None
        else:
            logger.warning("S3 credentials not configured, file uploads will be disabled")

    def is_available(self) -> bool:
        """Check if S3 service is available."""
        return self.client is not None

    async def upload_file(self, file: UploadFile, folder: str = "uploads", filename: Optional[str] = None) -> str:
        """
        Upload a file to S3/MinIO.

        Args:
            file: The uploaded file
            folder: The folder/prefix in the bucket
            filename: Custom filename (if None, uses original or generates UUID)

        Returns:
            The S3 object key/path

        Raises:
            HTTPException: If upload fails
        """
        if not self.is_available():
            raise HTTPException(status_code=500, detail="File storage service is not available")

        try:
            # Generate filename if not provided
            if not filename:
                if file.filename:
                    # Use original filename
                    filename = file.filename
                else:
                    # Generate UUID-based filename
                    filename = f"{uuid.uuid4()}.bin"

            # Create S3 key (path)
            s3_key = f"{folder}/{uuid.uuid4()}-{filename}"

            # Read file content
            content = await file.read()

            # Upload to S3
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content,
                ContentType=file.content_type or "application/octet-stream",
            )

            logger.info(f"File uploaded successfully: {s3_key}")
            return s3_key

        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload file: {e}")
        except Exception as e:
            logger.error(f"Unexpected upload error: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload file")
        finally:
            # Reset file position for potential reuse
            await file.seek(0)

    def get_file_url(self, s3_key: str) -> str:
        """
        Get the public URL for a file in S3.

        Args:
            s3_key: The S3 object key

        Returns:
            The public URL
        """
        if not self.is_available() or not settings.s3_endpoint_url:
            return f"/media/{s3_key}"  # Fallback to local path

        # For MinIO with public bucket, construct direct URL
        base_url = settings.s3_endpoint_url.rstrip("/")
        return f"{base_url}/{self.bucket_name}/{s3_key}"

    def download_file(self, s3_key: str) -> bytes:
        """
        Download a file from S3/MinIO.

        Args:
            s3_key: The S3 object key

        Returns:
            File content as bytes

        Raises:
            HTTPException: If download fails
        """
        if not self.is_available():
            raise HTTPException(status_code=500, detail="File storage service is not available")

        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise HTTPException(status_code=404, detail="File not found")
            logger.error(f"S3 download error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to download file: {e}")
        except Exception as e:
            logger.error(f"Unexpected download error: {e}")
            raise HTTPException(status_code=500, detail="Failed to download file")

    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3/MinIO.

        Args:
            s3_key: The S3 object key

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False

        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"File deleted successfully: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"S3 delete error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected delete error: {e}")
            return False


# Global S3 service instance
s3_service = S3Service()
