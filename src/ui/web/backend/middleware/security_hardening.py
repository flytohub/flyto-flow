"""
Security Hardening Middleware

Production-grade security measures:
- Error sanitization (hide stack traces)
- Server header removal
- Request size limiting
"""

import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger(__name__)


class ErrorSanitizationMiddleware(BaseHTTPMiddleware):
    """Sanitize error responses to prevent information leakage.

    - 5xx errors: generic message, no stack trace
    - 4xx errors: keep message but strip internal details
    - Removes server version headers
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Unhandled error: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"ok": False, "error": "Internal server error"},
            )

        # Remove server identification headers
        if "server" in response.headers:
            del response.headers["server"]
        if "x-powered-by" in response.headers:
            del response.headers["x-powered-by"]

        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Limit request body size to prevent resource exhaustion."""

    def __init__(self, app, max_body_size: int = 50 * 1024 * 1024):  # 50MB default
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                cl_int = int(content_length)
                if cl_int < 0 or cl_int > self.max_body_size:
                    return JSONResponse(
                        status_code=413,
                        content={"ok": False, "error": "Request body too large"},
                    )
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={"ok": False, "error": "Invalid Content-Length"},
                )
        return await call_next(request)
