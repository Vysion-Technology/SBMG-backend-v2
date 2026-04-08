import re
import logging
from typing import Any, Callable, Dict, List, Union
from fastapi import Request, Response, HTTPException
from fastapi.routing import APIRoute
from starlette.datastructures import UploadFile

# Regex pattern to detect HTML tags: < followed by any characters except > and then >
HTML_TAG_PATTERN = re.compile(r"<[^>]*>")

logger = logging.getLogger(__name__)

def check_for_html(data: Any) -> None:
    """
    Recursively inspects data for HTML tags.
    Raises HTTPException if a string contains HTML tags.
    Safely ignores UploadFile objects and other non-iterable/non-string types.
    """
    if isinstance(data, str):
        if HTML_TAG_PATTERN.search(data):
            logger.warning(f"XSS Protection: HTML tag detected in string: {data}")
            raise HTTPException(
                status_code=400,
                detail="Security Alert: HTML tags and scripts are not allowed."
            )
    elif isinstance(data, dict):
        for value in data.values():
            check_for_html(value)
    elif isinstance(data, list):
        for item in data:
            check_for_html(item)
    # Explicitly ignore UploadFile and other types
    else:
        pass

class XSSProtectionRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            # 1. Check Query Parameters
            if request.query_params:
                check_for_html(dict(request.query_params))

            # 2. Check Body based on Content-Type
            content_type = request.headers.get("Content-Type", "")

            if "application/json" in content_type:
                try:
                    body = await request.json()
                    check_for_html(body)
                except HTTPException:
                    # Re-raise security alerts
                    raise
                except Exception:
                    # If JSON is malformed, let the standard FastAPI handlers deal with it
                    pass

            elif "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
                try:
                    form_data = await request.form()
                    # .multi_items() returns a list of (key, value) tuples.
                    for _, value in form_data.multi_items():
                        check_for_html(value)
                except HTTPException:
                    # Re-raise security alerts
                    raise
                except Exception:
                    pass

            return await original_route_handler(request)

        return custom_route_handler
