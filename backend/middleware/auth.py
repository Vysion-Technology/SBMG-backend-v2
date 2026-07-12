from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi import Request, Response

from config import settings

class JWTSlidingWindowMiddleware(BaseHTTPMiddleware):
    """
    Middleware that implements a sliding window for JWT access tokens.
    If a token is valid but near expiration (e.g., < 5 minutes), 
    it issues a new token in the response headers.
    """
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        # Get Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return response

        token = auth_header.replace("Bearer ", "")
        
        try:
            # Decode token without verification first to check expiration
            # We assume the token was already verified by the security dependency
            # but we verify here again to be safe and get the payload
            payload = jwt.decode(
                token, 
                settings.jwt_secret_key, 
                algorithms=[settings.jwt_algorithm]
            )
            
            exp = payload.get("exp")
            if not exp:
                return response
                
            # Convert exp to datetime
            exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            
            # If token expires in less than 5 minutes, refresh it
            refresh_threshold = timedelta(minutes=5)
            if exp_datetime - now < refresh_threshold:
                # Create new payload with fresh expiration
                new_payload = payload.copy()
                new_exp = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)
                new_payload.update({"exp": new_exp})
                
                new_token = jwt.encode(
                    new_payload, 
                    settings.jwt_secret_key, 
                    algorithm=settings.jwt_algorithm
                )
                
                # Add new token to response headers
                response.headers["X-Refresh-Token"] = new_token
                # Ensure the header is exposed to the frontend (CORS)
                # Note: We'll also need to update CORS middleware to expose this header
                
        except (JWTError, Exception):
            # If token is invalid or expired, do nothing (let the normal auth handle it)
            pass
            
        return response
