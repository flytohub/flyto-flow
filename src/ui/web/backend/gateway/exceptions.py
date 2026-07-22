"""
Gateway Provider Exceptions

Exception classes for local CE provider operations.
"""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(str, Enum):
    """Standard error codes for provider exceptions."""

    # Resource errors
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"

    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"

    # Service errors
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    SERVICE_TIMEOUT = "SERVICE_TIMEOUT"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"

    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Generic
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class ProviderException(Exception):
    """
    Base exception for all provider operations.

    Provides a consistent error format for local provider failures.

    Usage:
        raise ProviderException(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message="Template not found",
            http_status=404,
            details={"template_id": "abc123"}
        )
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        http_status: int = 500,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize with error code, message, HTTP status, and optional details."""
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status
        self.details = details or {}
        self.original_error = original_error

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to API response format."""
        result = {
            "ok": False,
            "error": self.message,
            "error_code": self.code.value,
        }
        if self.details:
            result["details"] = self.details
        return result

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return f"ProviderException({self.code.value}: {self.message})"


# Convenience exception classes

class NotFoundError(ProviderException):
    """Resource not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
        message: Optional[str] = None,
    ):
        """Initialize with 404 status, auto-generating message from resource info."""
        if message is None:
            if resource_id:
                message = f"{resource_type} '{resource_id}' not found"
            else:
                message = f"{resource_type} not found"

        super().__init__(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message=message,
            http_status=404,
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class ConflictError(ProviderException):
    """Resource conflict (e.g., optimistic locking failure)."""

    def __init__(
        self,
        message: str = "Resource conflict",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize with 409 status."""
        super().__init__(
            code=ErrorCode.RESOURCE_CONFLICT,
            message=message,
            http_status=409,
            details=details,
        )


class ValidationError(ProviderException):
    """Validation error."""

    def __init__(
        self,
        message: str = "Validation failed",
        errors: Optional[list] = None,
    ):
        """Initialize with 400 status and optional error list."""
        super().__init__(
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            http_status=400,
            details={"errors": errors} if errors else None,
        )


class ServiceUnavailableError(ProviderException):
    """External service unavailable."""

    def __init__(
        self,
        service_name: str = "service",
        message: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize with 503 status and service name."""
        if message is None:
            message = f"{service_name} is currently unavailable"

        super().__init__(
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message=message,
            http_status=503,
            details={"service": service_name},
            original_error=original_error,
        )


class RateLimitError(ProviderException):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ):
        """Initialize with 429 status and optional retry_after hint."""
        details = {}
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=message,
            http_status=429,
            details=details if details else None,
        )


class DatabaseError(ProviderException):
    """Database operation failed."""

    def __init__(
        self,
        message: str = "Database operation failed",
        original_error: Optional[Exception] = None,
    ):
        """Initialize with 500 status and optional original exception."""
        super().__init__(
            code=ErrorCode.DATABASE_ERROR,
            message=message,
            http_status=500,
            original_error=original_error,
        )
