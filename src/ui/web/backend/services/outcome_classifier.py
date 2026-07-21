"""
Outcome Classifier Service

Classifies execution outcomes with error fingerprinting and root cause analysis.
Provides actionable insights for debugging and retry decisions.
"""

import hashlib
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class OutcomeType(str, Enum):
    """Execution outcome types."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL_SUCCESS = "partial_success"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ErrorCategory(str, Enum):
    """Error category for classification."""

    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"
    RATE_LIMIT = "rate_limit"
    AUTH_ERROR = "auth_error"
    VALIDATION_ERROR = "validation_error"
    SELECTOR_NOT_FOUND = "selector_not_found"
    RESOURCE_NOT_FOUND = "resource_not_found"
    PERMISSION_DENIED = "permission_denied"
    QUOTA_EXCEEDED = "quota_exceeded"
    SERVICE_UNAVAILABLE = "service_unavailable"
    INTERNAL_ERROR = "internal_error"
    UNKNOWN = "unknown"


@dataclass
class ErrorTaxonomyEntry:
    """Error taxonomy entry with metadata."""

    category: ErrorCategory
    retryable: bool
    max_retries: int = 3
    backoff_base_ms: int = 1000
    backoff_multiplier: float = 2.0
    backoff_max_ms: int = 30000
    jitter_factor: float = 0.1


# Error taxonomy with retry policies
ERROR_TAXONOMY: Dict[ErrorCategory, ErrorTaxonomyEntry] = {
    ErrorCategory.TIMEOUT: ErrorTaxonomyEntry(
        category=ErrorCategory.TIMEOUT,
        retryable=True,
        max_retries=3,
        backoff_base_ms=5000,
    ),
    ErrorCategory.NETWORK_ERROR: ErrorTaxonomyEntry(
        category=ErrorCategory.NETWORK_ERROR,
        retryable=True,
        max_retries=5,
        backoff_base_ms=2000,
    ),
    ErrorCategory.RATE_LIMIT: ErrorTaxonomyEntry(
        category=ErrorCategory.RATE_LIMIT,
        retryable=True,
        max_retries=5,
        backoff_base_ms=10000,
        backoff_multiplier=3.0,
    ),
    ErrorCategory.AUTH_ERROR: ErrorTaxonomyEntry(
        category=ErrorCategory.AUTH_ERROR,
        retryable=False,
    ),
    ErrorCategory.VALIDATION_ERROR: ErrorTaxonomyEntry(
        category=ErrorCategory.VALIDATION_ERROR,
        retryable=False,
    ),
    ErrorCategory.SELECTOR_NOT_FOUND: ErrorTaxonomyEntry(
        category=ErrorCategory.SELECTOR_NOT_FOUND,
        retryable=True,
        max_retries=2,
        backoff_base_ms=1000,
    ),
    ErrorCategory.RESOURCE_NOT_FOUND: ErrorTaxonomyEntry(
        category=ErrorCategory.RESOURCE_NOT_FOUND,
        retryable=False,
    ),
    ErrorCategory.PERMISSION_DENIED: ErrorTaxonomyEntry(
        category=ErrorCategory.PERMISSION_DENIED,
        retryable=False,
    ),
    ErrorCategory.QUOTA_EXCEEDED: ErrorTaxonomyEntry(
        category=ErrorCategory.QUOTA_EXCEEDED,
        retryable=True,
        max_retries=1,
        backoff_base_ms=60000,
    ),
    ErrorCategory.SERVICE_UNAVAILABLE: ErrorTaxonomyEntry(
        category=ErrorCategory.SERVICE_UNAVAILABLE,
        retryable=True,
        max_retries=5,
        backoff_base_ms=5000,
    ),
    ErrorCategory.INTERNAL_ERROR: ErrorTaxonomyEntry(
        category=ErrorCategory.INTERNAL_ERROR,
        retryable=True,
        max_retries=2,
        backoff_base_ms=2000,
    ),
    ErrorCategory.UNKNOWN: ErrorTaxonomyEntry(
        category=ErrorCategory.UNKNOWN,
        retryable=True,
        max_retries=1,
        backoff_base_ms=5000,
    ),
}


@dataclass
class StepStats:
    """Statistics about step execution."""

    total: int = 0
    success: int = 0
    failure: int = 0
    skipped: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total == 0:
            return 0.0
        return self.success / self.total


@dataclass
class FailureInfo:
    """Information about execution failure."""

    step_id: str
    step_index: int
    module_id: str
    error_type: str
    error_message: str
    error_category: ErrorCategory
    fingerprint: str
    retryable: bool


@dataclass
class ExecutionOutcome:
    """Complete execution outcome classification."""

    exec_id: str
    outcome: OutcomeType
    outcome_reason: str
    stats: StepStats
    failure_info: Optional[FailureInfo] = None
    duration_ms: Optional[int] = None
    completed_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set completed_at to current UTC time if not provided."""
        if not self.completed_at:
            self.completed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "exec_id": self.exec_id,
            "outcome": self.outcome.value,
            "outcome_reason": self.outcome_reason,
            "stats": asdict(self.stats),
            "duration_ms": self.duration_ms,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
        }
        if self.failure_info:
            result["failure_info"] = {
                "step_id": self.failure_info.step_id,
                "step_index": self.failure_info.step_index,
                "module_id": self.failure_info.module_id,
                "error_type": self.failure_info.error_type,
                "error_message": self.failure_info.error_message,
                "error_category": self.failure_info.error_category.value,
                "fingerprint": self.failure_info.fingerprint,
                "retryable": self.failure_info.retryable,
            }
        return result


class OutcomeClassifier:
    """
    Classifies execution outcomes with error fingerprinting.

    Features:
    - Error categorization with taxonomy
    - Fingerprint generation for deduplication
    - Retry policy recommendations
    - Root cause identification
    """

    # Error message patterns for classification
    ERROR_PATTERNS: List[Tuple[str, ErrorCategory]] = [
        # Timeout patterns
        (r"timeout|timed out|deadline exceeded", ErrorCategory.TIMEOUT),
        # Network patterns
        (r"connection refused|network|dns|resolve|socket|ECONNREFUSED", ErrorCategory.NETWORK_ERROR),
        (r"ssl|tls|certificate", ErrorCategory.NETWORK_ERROR),
        # Rate limit patterns
        (r"rate limit|too many requests|429|throttl", ErrorCategory.RATE_LIMIT),
        # Auth patterns
        (r"unauthorized|401|authentication|invalid token|expired token", ErrorCategory.AUTH_ERROR),
        (r"forbidden|403|access denied|permission denied", ErrorCategory.PERMISSION_DENIED),
        # Validation patterns
        (r"validation|invalid|required field|missing parameter", ErrorCategory.VALIDATION_ERROR),
        (r"parse error|json|syntax error|malformed", ErrorCategory.VALIDATION_ERROR),
        # Selector patterns
        (r"selector|element not found|no such element|locator", ErrorCategory.SELECTOR_NOT_FOUND),
        (r"xpath|css selector|query selector", ErrorCategory.SELECTOR_NOT_FOUND),
        # Resource patterns
        (r"not found|404|does not exist|no such", ErrorCategory.RESOURCE_NOT_FOUND),
        # Quota patterns
        (r"quota|limit exceeded|insufficient|credits", ErrorCategory.QUOTA_EXCEEDED),
        # Service unavailable
        (r"503|service unavailable|temporarily unavailable|maintenance", ErrorCategory.SERVICE_UNAVAILABLE),
        (r"502|bad gateway|upstream", ErrorCategory.SERVICE_UNAVAILABLE),
        # Internal errors
        (r"500|internal server error|internal error", ErrorCategory.INTERNAL_ERROR),
    ]

    @classmethod
    def generate_error_fingerprint(
        cls,
        error_type: str,
        module_id: str,
        key_fields: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Generate a stable fingerprint for error deduplication.

        Format: {error_type}:{module_id}:{key_hash}

        Args:
            error_type: Type of error (e.g., "TimeoutError")
            module_id: Module that raised the error
            key_fields: Additional fields to include in fingerprint

        Returns:
            Fingerprint string
        """
        # Normalize inputs
        error_type = cls._normalize_error_type(error_type)
        module_id = cls._normalize_module_id(module_id)

        # Create key hash from additional fields
        key_hash = ""
        if key_fields:
            key_str = ":".join(f"{k}={v}" for k, v in sorted(key_fields.items()))
            key_hash = hashlib.sha256(key_str.encode()).hexdigest()[:8]

        parts = [error_type, module_id]
        if key_hash:
            parts.append(key_hash)

        return ":".join(parts)

    @classmethod
    def classify_error(
        cls,
        error_type: str,
        error_message: str,
    ) -> ErrorCategory:
        """
        Classify an error into a category.

        Args:
            error_type: Type of error
            error_message: Error message

        Returns:
            ErrorCategory
        """
        # Combine type and message for pattern matching
        combined = f"{error_type} {error_message}".lower()

        for pattern, category in cls.ERROR_PATTERNS:
            if re.search(pattern, combined, re.IGNORECASE):
                return category

        return ErrorCategory.UNKNOWN

    @classmethod
    def get_taxonomy_entry(cls, category: ErrorCategory) -> ErrorTaxonomyEntry:
        """Get taxonomy entry for error category."""
        return ERROR_TAXONOMY.get(
            category,
            ERROR_TAXONOMY[ErrorCategory.UNKNOWN]
        )

    @classmethod
    def classify_execution(
        cls,
        exec_id: str,
        step_records: List[Dict[str, Any]],
        duration_ms: Optional[int] = None,
        was_cancelled: bool = False,
    ) -> ExecutionOutcome:
        """
        Classify execution outcome based on step records.

        Args:
            exec_id: Execution identifier
            step_records: List of step records
            duration_ms: Total execution duration
            was_cancelled: Whether execution was cancelled

        Returns:
            ExecutionOutcome with full classification
        """
        # Calculate stats
        stats = StepStats(total=len(step_records))

        failed_step = None
        for step in step_records:
            status = step.get("status", "").lower()
            if status == "success":
                stats.success += 1
            elif status in ("failure", "failed"):
                stats.failure += 1
                if failed_step is None:
                    failed_step = step
            elif status == "skipped":
                stats.skipped += 1

        # Determine outcome
        if was_cancelled:
            outcome = OutcomeType.CANCELLED
            outcome_reason = "Execution was cancelled"
        elif stats.failure == 0:
            outcome = OutcomeType.SUCCESS
            outcome_reason = f"All {stats.success} steps completed successfully"
        elif stats.success > 0:
            outcome = OutcomeType.PARTIAL_SUCCESS
            outcome_reason = f"{stats.success}/{stats.total} steps succeeded, {stats.failure} failed"
        else:
            outcome = OutcomeType.FAILURE
            outcome_reason = f"Execution failed at step {failed_step.get('step_index', 0)}"

        # Build failure info if applicable
        failure_info = None
        if failed_step:
            error_type = failed_step.get("error_type", "Error")
            error_message = failed_step.get("error_message", "Unknown error")
            module_id = failed_step.get("module_id", "unknown")

            error_category = cls.classify_error(error_type, error_message)
            taxonomy = cls.get_taxonomy_entry(error_category)

            fingerprint = cls.generate_error_fingerprint(
                error_type=error_type,
                module_id=module_id,
                key_fields={
                    "step_id": failed_step.get("step_id", ""),
                },
            )

            failure_info = FailureInfo(
                step_id=failed_step.get("step_id", ""),
                step_index=failed_step.get("step_index", 0),
                module_id=module_id,
                error_type=error_type,
                error_message=error_message,
                error_category=error_category,
                fingerprint=fingerprint,
                retryable=taxonomy.retryable,
            )

        return ExecutionOutcome(
            exec_id=exec_id,
            outcome=outcome,
            outcome_reason=outcome_reason,
            stats=stats,
            failure_info=failure_info,
            duration_ms=duration_ms,
        )

    @classmethod
    def _normalize_error_type(cls, error_type: str) -> str:
        """Normalize error type for fingerprinting."""
        # Remove common suffixes
        error_type = error_type.replace("Error", "").replace("Exception", "")
        # Convert to snake_case
        error_type = re.sub(r"(?<!^)(?=[A-Z])", "_", error_type).lower()
        return error_type.strip("_") or "error"

    @classmethod
    def _normalize_module_id(cls, module_id: str) -> str:
        """Normalize module ID for fingerprinting."""
        # Remove common prefixes
        for prefix in ("core.", "pro.", "atomic."):
            if module_id.startswith(prefix):
                module_id = module_id[len(prefix):]
        return module_id or "unknown"

    @classmethod
    def calculate_backoff(
        cls,
        category: ErrorCategory,
        attempt: int,
        jitter: bool = True,
    ) -> int:
        """
        Calculate backoff delay for retry.

        Args:
            category: Error category
            attempt: Current attempt number (1-based)
            jitter: Whether to add random jitter

        Returns:
            Delay in milliseconds
        """
        import random

        taxonomy = cls.get_taxonomy_entry(category)

        # Exponential backoff
        delay = taxonomy.backoff_base_ms * (taxonomy.backoff_multiplier ** (attempt - 1))

        # Cap at maximum
        delay = min(delay, taxonomy.backoff_max_ms)

        # Add jitter
        if jitter and taxonomy.jitter_factor > 0:
            jitter_range = delay * taxonomy.jitter_factor
            delay += random.uniform(-jitter_range, jitter_range)

        return int(max(0, delay))

    @classmethod
    def should_retry(
        cls,
        category: ErrorCategory,
        attempt: int,
    ) -> bool:
        """
        Determine if error should be retried.

        Args:
            category: Error category
            attempt: Current attempt number (1-based)

        Returns:
            True if should retry
        """
        taxonomy = cls.get_taxonomy_entry(category)
        return taxonomy.retryable and attempt < taxonomy.max_retries
