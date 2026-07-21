"""
Unified API Error Handling

Provides consistent error response format across all API endpoints.
Addresses API-1, API-2, API-3 from security audit.

Standard Response Format:
{
    "ok": false,
    "error": "Human readable error message",
    "error_code": "ERROR_CODE",
    "details": {...}  // Optional validation details
}
"""

import logging
import os
import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, NoReturn, Optional

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from gateway.exceptions import ProviderException

# Patterns that indicate internal/sensitive info in error messages
_SENSITIVE_PATTERNS = [
    re.compile(r'Traceback \(most recent', re.IGNORECASE),
    re.compile(r'File "/', re.IGNORECASE),           # File paths
    re.compile(r'line \d+, in ', re.IGNORECASE),     # Stack trace lines
    re.compile(r'sqlite3?\.\w+Error', re.IGNORECASE),  # SQLite errors
    re.compile(r'psycopg2?\.\w+Error', re.IGNORECASE),  # PostgreSQL errors
    re.compile(r'ConnectionRefusedError', re.IGNORECASE),
    re.compile(r'ModuleNotFoundError', re.IGNORECASE),
    re.compile(r'ImportError', re.IGNORECASE),
    re.compile(r'KeyError:', re.IGNORECASE),
    re.compile(r'AttributeError:', re.IGNORECASE),
    re.compile(r'TypeError:', re.IGNORECASE),
    re.compile(r'ValueError:', re.IGNORECASE),
    re.compile(r'/home/\w+/', re.IGNORECASE),        # Home dir paths
    re.compile(r'/usr/lib/', re.IGNORECASE),          # System paths
    re.compile(r'/app/', re.IGNORECASE),              # Container paths
    re.compile(r'password|secret|token|key=', re.IGNORECASE),  # Credentials
]


def _contains_sensitive_info(detail: str) -> bool:
    """Check if an error detail contains sensitive internal information."""
    if not detail or len(detail) < 10:
        return False
    for pattern in _SENSITIVE_PATTERNS:
        if pattern.search(detail):
            return True
    return False


# =============================================================================
# Telemetry Integration
# =============================================================================

def _track_error_to_telemetry(
    request: Request,
    status_code: int,
    error_message: str,
    error_type: str = "http_error",
    error_code: str = None,
    exc: Exception = None
):
    """
    Track error to telemetry system.

    This is non-blocking - telemetry failures should never affect the response.
    """
    try:
        from services.observability.telemetry_service import get_telemetry_service

        service = get_telemetry_service()
        service.save_event({
            "event_type": "backend_error",
            "event_name": f"http.{status_code}",
            "trace_id": request.headers.get("x-trace-id"),
            "session_id": request.headers.get("x-session-id"),
            "error": {
                "message": error_message,
                "type": error_type,
                "code": error_code or str(status_code),
                "stack": str(exc) if exc and status_code >= 500 else None
            },
            "request": {
                "method": request.method,
                "url": str(request.url),
                "status": status_code,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            },
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "source": "backend"
        })
    except Exception as e:
        # Telemetry should never fail the request
        logger.debug(f"Telemetry tracking failed: {e}")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    ok: bool = False
    error: str
    error_code: str
    details: Optional[Dict[str, Any]] = None


# Error code mapping for HTTP status codes
HTTP_ERROR_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    502: "BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
    504: "GATEWAY_TIMEOUT",
}


def get_error_code(status_code: int) -> str:
    """Get standardized error code for HTTP status."""
    return HTTP_ERROR_CODES.get(status_code, f"HTTP_{status_code}")


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handle HTTPException with standardized format.

    Converts all HTTPException responses to:
    {
        "ok": false,
        "error": "<detail>",
        "error_code": "<ERROR_CODE>",
        "details": {...}  // Optional, for validation errors
    }
    """
    error_code = get_error_code(exc.status_code)
    details = None

    # Handle dict detail (e.g., payment errors, validation errors with structured data)
    if isinstance(exc.detail, dict):
        error_message = (
            exc.detail.get("error")
            or exc.detail.get("message")
            or error_code.replace("_", " ").title()
        )
        # Preserve the full dict as details so frontend can read fields
        # like error_code, balance, template_id, feature, etc.
        details = exc.detail
        # Override error_code if the dict specifies one
        if exc.detail.get("error_code"):
            error_code = exc.detail["error_code"]
    elif exc.status_code >= 500:
        # Sanitize error message - don't expose internal details for 5xx
        error_message = "Internal server error"
        logger.error(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")
    else:
        raw_detail = str(exc.detail) if exc.detail else ""
        # Sanitize 4xx errors: strip internal details (stack traces, file paths, SQL)
        if raw_detail and _contains_sensitive_info(raw_detail):
            logger.warning(f"Sanitized 4xx detail on {request.url.path}: {raw_detail}")
            error_message = error_code.replace("_", " ").title()
        else:
            error_message = raw_detail or error_code.replace("_", " ").title()

    # Track error to telemetry (4xx and 5xx)
    if exc.status_code >= 400:
        _track_error_to_telemetry(
            request=request,
            status_code=exc.status_code,
            error_message=str(exc.detail) if exc.detail else error_message,
            error_type="HTTPException",
            error_code=error_code,
            exc=exc if exc.status_code >= 500 else None
        )

    response_content = {
        "ok": False,
        "error": error_message,
        "error_code": error_code,
    }

    # Include details for 4xx errors only
    if exc.status_code < 500 and details:
        response_content["details"] = details

    return JSONResponse(
        status_code=exc.status_code,
        content=response_content,
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors with standardized format.

    Converts validation errors to:
    {
        "ok": false,
        "error": "Validation failed",
        "error_code": "VALIDATION_ERROR",
        "details": {
            "errors": [
                {"field": "...", "message": "...", "type": "..."}
            ]
        }
    }
    """
    # Format validation errors for frontend consumption
    formatted_errors: List[Dict[str, str]] = []

    for error in exc.errors():
        # Get field path (e.g., "body.name" or "query.page")
        loc = error.get("loc", [])
        field_path = ".".join(str(x) for x in loc if x not in ("body", "query", "path"))
        if not field_path:
            field_path = ".".join(str(x) for x in loc)

        formatted_errors.append({
            "field": field_path,
            "message": error.get("msg", "Invalid value"),
            "type": error.get("type", "value_error"),
        })

    # Create summary message
    if len(formatted_errors) == 1:
        summary = f"Validation failed: {formatted_errors[0]['field']} - {formatted_errors[0]['message']}"
    else:
        summary = f"Validation failed: {len(formatted_errors)} errors"

    logger.warning(f"Validation error on {request.url.path}: {formatted_errors}")

    # Track validation error to telemetry
    _track_error_to_telemetry(
        request=request,
        status_code=422,
        error_message=summary,
        error_type="ValidationError",
        error_code="VALIDATION_ERROR"
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "ok": False,
            "error": summary,
            "error_code": "VALIDATION_ERROR",
            "details": {
                "errors": formatted_errors,
            },
        },
    )


async def provider_exception_handler(
    request: Request,
    exc: "ProviderException"
) -> JSONResponse:
    """
    Handle ProviderException from gateway layer.

    Converts ProviderException to standardized HTTP response:
    {
        "ok": false,
        "error": "<message>",
        "error_code": "<PROVIDER_ERROR_CODE>",
        "details": {...}  // If provided
    }
    """
    from gateway.exceptions import ProviderException

    # Log based on severity
    if exc.http_status >= 500:
        logger.error(
            f"Provider error on {request.method} {request.url.path}: "
            f"{exc.code.value} - {exc.message}"
        )
        # Sanitize 5xx errors for client
        error_message = "Service temporarily unavailable"
    else:
        logger.warning(
            f"Provider error on {request.method} {request.url.path}: "
            f"{exc.code.value} - {exc.message}"
        )
        error_message = exc.message

    response_content = {
        "ok": False,
        "error": error_message,
        "error_code": exc.code.value,
    }

    # Include details for 4xx errors only
    if exc.http_status < 500 and exc.details:
        response_content["details"] = exc.details

    # Track provider error to telemetry
    _track_error_to_telemetry(
        request=request,
        status_code=exc.http_status,
        error_message=exc.message,
        error_type="ProviderException",
        error_code=exc.code.value,
        exc=exc if exc.http_status >= 500 else None
    )

    return JSONResponse(
        status_code=exc.http_status,
        content=response_content,
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle uncaught exceptions with sanitized response.

    Never exposes stack traces or internal error details.
    """
    # Log full error for debugging
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}",
        exc_info=True
    )

    # Track unhandled exception to telemetry
    _track_error_to_telemetry(
        request=request,
        status_code=500,
        error_message=str(exc),
        error_type=type(exc).__name__,
        error_code="INTERNAL_ERROR",
        exc=exc
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "ok": False,
            "error": "Internal server error",
            "error_code": "INTERNAL_ERROR",
        },
    )


# =============================================================================
# Error Factory Functions
# =============================================================================
# Use these instead of `raise HTTPException(status_code=..., detail=...)`
# for consistent error formatting across all routes.
# These functions never return — they always raise.


def not_found(detail: str = "Not found") -> NoReturn:
    """Raise 404 Not Found."""
    raise HTTPException(status_code=404, detail=detail)


def bad_request(detail: str = "Bad request") -> NoReturn:
    """Raise 400 Bad Request."""
    raise HTTPException(status_code=400, detail=detail)


def forbidden(detail: str = "Forbidden") -> NoReturn:
    """Raise 403 Forbidden."""
    raise HTTPException(status_code=403, detail=detail)


def unauthorized(detail: str = "Unauthorized") -> NoReturn:
    """Raise 401 Unauthorized."""
    raise HTTPException(status_code=401, detail=detail)


def conflict(detail: str = "Conflict") -> NoReturn:
    """Raise 409 Conflict."""
    raise HTTPException(status_code=409, detail=detail)


def internal_error(detail: str = "Internal server error") -> NoReturn:
    """Raise 500 Internal Server Error."""
    raise HTTPException(status_code=500, detail=detail)


def safe_error_response(e: Exception, message: str = "Operation failed", status_code: int = 500) -> dict:
    """Return safe error dict. Log full error internally, never expose to client."""
    logger.error(f"{message}: {e}", exc_info=True)
    return {"ok": False, "error": message}


def register_exception_handlers(app):
    """
    Register all exception handlers on FastAPI app.

    Usage in main.py:
        from api.api.errors import register_exception_handlers
        register_exception_handlers(app)

    Handler priority (most specific first):
    1. ProviderException - Gateway layer errors
    2. StarletteHTTPException - HTTP errors from routes
    3. RequestValidationError - Pydantic validation
    4. Exception - Catch-all for unhandled errors
    """
    # Import ProviderException here to avoid circular import
    from gateway.exceptions import ProviderException

    # Register handlers (order matters - most specific first)
    app.add_exception_handler(ProviderException, provider_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
