from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi import Request, Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Default strict CSP
        csp = "default-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self';"

        # Less strict CSP for documentation routes (Swagger/ReDoc)
        if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "object-src 'none'; "
                "frame-ancestors 'none';"
            )

        response.headers["Content-Security-Policy"] = csp
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Remove revealing headers
        revealing_headers = ["Server", "X-Powered-By", "X-Runtime", "X-Version"]
        for header in revealing_headers:
            if header in response.headers:
                del response.headers[header]
            # Also check case-insensitive just in case
            lower_headers = {k.lower(): k for k in response.headers.keys()}
            if header.lower() in lower_headers:
                del response.headers[lower_headers[header.lower()]]

        return response
