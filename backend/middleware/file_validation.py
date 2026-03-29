import magic
import os
import logging
from typing import Optional
from fastapi import HTTPException, UploadFile

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/jpg", "application/pdf"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

async def validate_secure_file(file: Optional[UploadFile]) -> Optional[UploadFile]:
    """
    Validates an uploaded file for security:
    1. Checks true MIME type using magic bytes.
    2. Prevents null byte injection and double extensions.
    3. Enforces file size limits.
    """
    if not file or not file.filename:
        return None

    # 1. Read the first 2048 bytes to determine the TRUE file type via Magic Bytes
    try:
        file_header = await file.read(2048)
        # Reset the file cursor back to the beginning so it can be saved properly later
        await file.seek(0)
        
        # Inspect the magic bytes
        true_mime_type = magic.from_buffer(file_header, mime=True)
    except Exception as e:
        logger.error(f"Magic byte inspection failed: {e}")
        raise HTTPException(status_code=400, detail="Could not verify file type.")
    
    if true_mime_type not in ALLOWED_MIME_TYPES:
        logger.warning(f"File spoofing detected: {file.filename} has true type {true_mime_type}")
        raise HTTPException(
            status_code=400, 
            detail=f"Security Alert: File spoofing detected. True file type is {true_mime_type}, which is not allowed."
        )

    # 2. Check Double Extensions and Null Bytes in the filename
    filename = file.filename
    if "%00" in filename or "\x00" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename: Null byte detected.")
    
    # Check for double extensions (e.g., malicious.php.jpg)
    if len(filename.split(".")) > 2:
        raise HTTPException(status_code=400, detail="Double extensions are not allowed.")

    # 3. Check File Size securely
    try:
        # Seek to end to get size
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        # Reset to beginning
        await file.seek(0)
    except Exception as e:
        logger.error(f"File size check failed: {e}")
        raise HTTPException(status_code=400, detail="Could not verify file size.")
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File size exceeds the {MAX_FILE_SIZE // (1024*1024)}MB limit.")
        
    return file
