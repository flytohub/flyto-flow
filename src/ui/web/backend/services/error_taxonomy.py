"""
Error Taxonomy

Classification of errors for retry decisions.
Defines which errors are retryable and how to categorize them.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Error category classification."""

    # Retryable errors
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"
    RATE_LIMIT = "rate_limit"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
    TRANSIENT_ERROR = "transient_error"

    # Non-retryable errors
    VALIDATION_ERROR = "validation_error"
    AUTH_ERROR = "auth_error"
    PERMISSION_DENIED = "permission_denied"
    RESOURCE_NOT_FOUND = "resource_not_found"
    BUSINESS_ERROR = "business_error"
    CONFIGURATION_ERROR = "configuration_error"

    # Unknown
    UNKNOWN = "unknown"


# Errors that should be retried
RETRYABLE_CATEGORIES: Set[ErrorCategory] = {
    ErrorCategory.TIMEOUT,
    ErrorCategory.NETWORK_ERROR,
    ErrorCategory.RATE_LIMIT,
    ErrorCategory.DEPENDENCY_UNAVAILABLE,
    ErrorCategory.TRANSIENT_ERROR,
}


@dataclass
class ClassifiedError:
    """Classified error with metadata."""

    category: ErrorCategory
    original_error: str
    retryable: bool
    suggested_delay_ms: Optional[int] = None
    fingerprint: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ErrorClassifier:
    """
    Classifies errors into categories for retry decisions.

    Uses pattern matching on error messages and exception types
    to determine the appropriate category.
    """

    # Pattern-based classification rules
    TIMEOUT_PATTERNS = [
        r"timeout",
        r"timed?\s*out",
        r"deadline\s*exceeded",
        r"request\s*took\s*too\s*long",
        r"connection\s*timed?\s*out",
    ]

    NETWORK_PATTERNS = [
        r"connection\s*(refused|reset|closed|error)",
        r"network\s*(error|unreachable)",
        r"socket\s*error",
        r"dns\s*(error|resolution|lookup)",
        r"econnrefused",
        r"econnreset",
        r"epipe",
        r"enetunreach",
        r"ehostunreach",
    ]

    RATE_LIMIT_PATTERNS = [
        r"rate\s*limit",
        r"too\s*many\s*requests",
        r"429",
        r"throttl",
        r"quota\s*exceeded",
    ]

    AUTH_PATTERNS = [
        r"auth(entication|orization)?\s*(failed|error|invalid)",
        r"401",
        r"403",
        r"invalid\s*(token|credential|api\s*key)",
        r"expired\s*(token|session|credential)",
        r"access\s*denied",
        r"permission\s*denied",
        r"unauthorized",
        r"forbidden",
    ]

    VALIDATION_PATTERNS = [
        r"validation\s*(failed|error)",
        r"invalid\s*(input|parameter|argument|value)",
        r"missing\s*required",
        r"bad\s*request",
        r"400",
        r"malformed",
    ]

    NOT_FOUND_PATTERNS = [
        r"not\s*found",
        r"404",
        r"does\s*not\s*exist",
        r"no\s*such",
        r"missing\s*(resource|file|element)",
    ]

    TRANSIENT_PATTERNS = [
        r"temporary",
        r"try\s*again",
        r"retry",
        r"service\s*unavailable",
        r"503",
        r"502",
        r"504",
        r"gateway\s*(timeout|error)",
        r"internal\s*server\s*error",
        r"500",
    ]

    @classmethod
    def classify(
        cls,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
    ) -> ClassifiedError:
        """
        Classify an exception.

        Args:
            error: The exception to classify
            context: Optional context (module_id, step_id, etc.)

        Returns:
            ClassifiedError with category and metadata
        """
        error_str = str(error).lower()
        error_type = type(error).__name__

        # Check patterns in order of specificity
        category = cls._match_patterns(error_str, error_type)

        # Calculate fingerprint
        fingerprint = cls._generate_fingerprint(
            category=category,
            error_type=error_type,
            error_str=error_str,
            context=context,
        )

        # Determine if retryable
        retryable = category in RETRYABLE_CATEGORIES

        # Suggest delay for rate limits
        suggested_delay = None
        if category == ErrorCategory.RATE_LIMIT:
            suggested_delay = cls._extract_retry_after(error_str)

        return ClassifiedError(
            category=category,
            original_error=str(error),
            retryable=retryable,
            suggested_delay_ms=suggested_delay,
            fingerprint=fingerprint,
            details={
                "error_type": error_type,
                "context": context,
            },
        )

    @classmethod
    def classify_from_message(
        cls,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ClassifiedError:
        """
        Classify an error from a message string.

        Args:
            message: Error message string
            context: Optional context

        Returns:
            ClassifiedError with category and metadata
        """
        error_str = message.lower()

        category = cls._match_patterns(error_str, "Unknown")

        fingerprint = cls._generate_fingerprint(
            category=category,
            error_type="Unknown",
            error_str=error_str,
            context=context,
        )

        retryable = category in RETRYABLE_CATEGORIES

        suggested_delay = None
        if category == ErrorCategory.RATE_LIMIT:
            suggested_delay = cls._extract_retry_after(error_str)

        return ClassifiedError(
            category=category,
            original_error=message,
            retryable=retryable,
            suggested_delay_ms=suggested_delay,
            fingerprint=fingerprint,
            details={"context": context},
        )

    @classmethod
    def _match_patterns(cls, error_str: str, error_type: str) -> ErrorCategory:
        """Match error string against patterns."""
        # Check exception type first
        error_type_lower = error_type.lower()

        if "timeout" in error_type_lower:
            return ErrorCategory.TIMEOUT

        if any(x in error_type_lower for x in ["connection", "network", "socket"]):
            return ErrorCategory.NETWORK_ERROR

        # Check patterns
        for pattern in cls.TIMEOUT_PATTERNS:
            if re.search(pattern, error_str, re.IGNORECASE):
                return ErrorCategory.TIMEOUT

        for pattern in cls.RATE_LIMIT_PATTERNS:
            if re.search(pattern, error_str, re.IGNORECASE):
                return ErrorCategory.RATE_LIMIT

        for pattern in cls.NETWORK_PATTERNS:
            if re.search(pattern, error_str, re.IGNORECASE):
                return ErrorCategory.NETWORK_ERROR

        for pattern in cls.AUTH_PATTERNS:
            if re.search(pattern, error_str, re.IGNORECASE):
                # Distinguish between auth and permission
                if re.search(r"permission|403|forbidden", error_str, re.IGNORECASE):
                    return ErrorCategory.PERMISSION_DENIED
                return ErrorCategory.AUTH_ERROR

        for pattern in cls.VALIDATION_PATTERNS:
            if re.search(pattern, error_str, re.IGNORECASE):
                return ErrorCategory.VALIDATION_ERROR

        for pattern in cls.NOT_FOUND_PATTERNS:
            if re.search(pattern, error_str, re.IGNORECASE):
                return ErrorCategory.RESOURCE_NOT_FOUND

        for pattern in cls.TRANSIENT_PATTERNS:
            if re.search(pattern, error_str, re.IGNORECASE):
                return ErrorCategory.TRANSIENT_ERROR

        return ErrorCategory.UNKNOWN

    @classmethod
    def _generate_fingerprint(
        cls,
        category: ErrorCategory,
        error_type: str,
        error_str: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate error fingerprint for aggregation.

        Format: {category}:{module_id}:{key_detail}:{location}
        """
        parts = [category.value]

        # Add module if available
        if context and context.get("module_id"):
            parts.append(context["module_id"])
        else:
            parts.append("unknown")

        # Add key detail based on category
        if category == ErrorCategory.TIMEOUT:
            # Extract timeout value if present
            match = re.search(r"(\d+)\s*(ms|s|seconds?|milliseconds?)", error_str)
            if match:
                parts.append(f"{match.group(1)}{match.group(2)}")
            else:
                parts.append("unknown_duration")

        elif category == ErrorCategory.RATE_LIMIT:
            # Extract status code if present
            match = re.search(r"(429|rate.?limit)", error_str, re.IGNORECASE)
            if match:
                parts.append("429")
            else:
                parts.append("throttled")

        elif category == ErrorCategory.NETWORK_ERROR:
            # Extract connection type
            if "refused" in error_str:
                parts.append("connection_refused")
            elif "reset" in error_str:
                parts.append("connection_reset")
            elif "dns" in error_str:
                parts.append("dns_error")
            else:
                parts.append("network")

        else:
            # Use error type for other categories
            parts.append(error_type.lower()[:20])

        # Add step/node location if available
        if context and context.get("step_id"):
            parts.append(f"step_{context['step_id']}")
        elif context and context.get("node_id"):
            parts.append(f"node_{context['node_id']}")

        return ":".join(parts)

    @classmethod
    def _extract_retry_after(cls, error_str: str) -> Optional[int]:
        """Extract retry-after value from error message."""
        # Look for explicit retry-after header value
        match = re.search(r"retry.?after[:\s]+(\d+)", error_str, re.IGNORECASE)
        if match:
            value = int(match.group(1))
            # Assume seconds if large, milliseconds if small
            if value < 1000:
                return value * 1000  # Convert to ms
            return value

        # Default suggestion for rate limits
        return 60000  # 60 seconds


def is_retryable(error: Exception) -> bool:
    """
    Quick check if an error is retryable.

    Args:
        error: Exception to check

    Returns:
        True if the error should be retried
    """
    classified = ErrorClassifier.classify(error)
    return classified.retryable


def is_retryable_message(message: str) -> bool:
    """
    Quick check if an error message indicates a retryable error.

    Args:
        message: Error message to check

    Returns:
        True if the error should be retried
    """
    classified = ErrorClassifier.classify_from_message(message)
    return classified.retryable
