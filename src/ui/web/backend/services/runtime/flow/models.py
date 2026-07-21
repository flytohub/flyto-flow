"""
Flow Control Models

Enums and data classes for flow control.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from services.error_taxonomy import ErrorCategory


class OnErrorStrategy(str, Enum):
    """Strategy for handling errors in a step."""

    STOP = "stop"  # Stop execution immediately
    CONTINUE = "continue"  # Continue to next step
    SKIP = "skip"  # Skip remaining steps in current block
    GOTO = "goto"  # Jump to specified node
    RETRY = "retry"  # Retry with configured policy
    CATCH = "catch"  # Execute catch block


@dataclass
class ErrorHandlerConfig:
    """Configuration for error handling."""

    on_error: OnErrorStrategy = OnErrorStrategy.STOP
    on_error_goto: Optional[str] = None  # Node ID for GOTO strategy
    catch_errors: List[ErrorCategory] = field(default_factory=list)  # Empty = catch all
    propagate_error: bool = True  # Propagate to parent after handling

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "on_error": self.on_error.value,
            "on_error_goto": self.on_error_goto,
            "catch_errors": [c.value for c in self.catch_errors],
            "propagate_error": self.propagate_error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ErrorHandlerConfig":
        """Create from dictionary."""
        on_error = data.get("on_error", "stop")
        if isinstance(on_error, str):
            on_error = OnErrorStrategy(on_error)

        catch_errors = data.get("catch_errors", [])
        if catch_errors:
            catch_errors = [ErrorCategory(c) for c in catch_errors]

        return cls(
            on_error=on_error,
            on_error_goto=data.get("on_error_goto"),
            catch_errors=catch_errors,
            propagate_error=data.get("propagate_error", True),
        )


@dataclass
class TryCatchFinallyConfig:
    """
    Configuration for Try-Catch-Finally block.

    Structure:
        try:
            - step1
            - step2
        catch:
            - error_handler
        finally:
            - cleanup
    """

    try_steps: List[str] = field(default_factory=list)  # Node IDs in try block
    catch_steps: List[str] = field(default_factory=list)  # Node IDs in catch block
    finally_steps: List[str] = field(default_factory=list)  # Node IDs in finally block
    catch_errors: List[ErrorCategory] = field(default_factory=list)  # Empty = catch all

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "try_steps": self.try_steps,
            "catch_steps": self.catch_steps,
            "finally_steps": self.finally_steps,
            "catch_errors": [c.value for c in self.catch_errors],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TryCatchFinallyConfig":
        """Create from dictionary."""
        catch_errors = data.get("catch_errors", [])
        if catch_errors:
            catch_errors = [ErrorCategory(c) for c in catch_errors]

        return cls(
            try_steps=data.get("try_steps", []),
            catch_steps=data.get("catch_steps", []),
            finally_steps=data.get("finally_steps", []),
            catch_errors=catch_errors,
        )


@dataclass
class TryCatchFinallyResult:
    """Result of Try-Catch-Finally execution."""

    success: bool
    try_completed: bool
    catch_executed: bool
    finally_executed: bool
    error: Optional[str] = None
    error_category: Optional[ErrorCategory] = None
    try_results: Dict[str, Any] = field(default_factory=dict)
    catch_results: Dict[str, Any] = field(default_factory=dict)
    finally_results: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "try_completed": self.try_completed,
            "catch_executed": self.catch_executed,
            "finally_executed": self.finally_executed,
            "error": self.error,
            "error_category": self.error_category.value if self.error_category else None,
            "try_results": self.try_results,
            "catch_results": self.catch_results,
            "finally_results": self.finally_results,
        }


class CompensationOrder(str, Enum):
    """Order for executing compensations."""

    LIFO = "lifo"  # Last In First Out (default, like stack)
    FIFO = "fifo"  # First In First Out


class OnCompensationFailure(str, Enum):
    """Strategy for compensation failure."""

    RETRY = "retry"  # Retry compensation
    ALERT = "alert"  # Send alert and continue
    MANUAL = "manual"  # Create manual task
    ABORT = "abort"  # Abort remaining compensations


@dataclass
class CompensationConfig:
    """
    Configuration for a step's compensation.

    Example:
        steps:
          - id: charge_payment
            compensation:
              module: payment.refund
              idempotency_key: "${exec_id}_refund"
    """

    module_id: str
    params: Dict[str, Any] = field(default_factory=dict)
    idempotency_key: Optional[str] = None
    timeout_ms: int = 60000
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "module_id": self.module_id,
            "params": self.params,
            "idempotency_key": self.idempotency_key,
            "timeout_ms": self.timeout_ms,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompensationConfig":
        """Create from dictionary."""
        return cls(
            module_id=data.get("module_id", ""),
            params=data.get("params", {}),
            idempotency_key=data.get("idempotency_key"),
            timeout_ms=data.get("timeout_ms", 60000),
            max_retries=data.get("max_retries", 3),
        )


@dataclass
class SagaStep:
    """A step in a Saga with optional compensation."""

    step_id: str
    module_id: str
    params: Dict[str, Any] = field(default_factory=dict)
    compensation: Optional[CompensationConfig] = None
    executed: bool = False
    result: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_id": self.step_id,
            "module_id": self.module_id,
            "params": self.params,
            "compensation": self.compensation.to_dict() if self.compensation else None,
            "executed": self.executed,
            "result": self.result,
        }


@dataclass
class SagaConfig:
    """Configuration for Saga execution."""

    compensation_order: CompensationOrder = CompensationOrder.LIFO
    on_compensation_failure: OnCompensationFailure = OnCompensationFailure.ALERT
    max_compensation_retries: int = 3
    require_idempotency: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "compensation_order": self.compensation_order.value,
            "on_compensation_failure": self.on_compensation_failure.value,
            "max_compensation_retries": self.max_compensation_retries,
            "require_idempotency": self.require_idempotency,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SagaConfig":
        """Create from dictionary."""
        return cls(
            compensation_order=CompensationOrder(
                data.get("compensation_order", "lifo")
            ),
            on_compensation_failure=OnCompensationFailure(
                data.get("on_compensation_failure", "alert")
            ),
            max_compensation_retries=data.get("max_compensation_retries", 3),
            require_idempotency=data.get("require_idempotency", True),
        )


@dataclass
class CompensationResult:
    """Result of a compensation execution."""

    step_id: str
    success: bool
    attempts: int
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_id": self.step_id,
            "success": self.success,
            "attempts": self.attempts,
            "error": self.error,
        }


@dataclass
class SagaResult:
    """Result of Saga execution."""

    success: bool
    completed_steps: List[str]
    failed_step: Optional[str] = None
    error: Optional[str] = None
    compensations_run: bool = False
    compensation_results: List[CompensationResult] = field(default_factory=list)
    requires_manual_intervention: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "completed_steps": self.completed_steps,
            "failed_step": self.failed_step,
            "error": self.error,
            "compensations_run": self.compensations_run,
            "compensation_results": [r.to_dict() for r in self.compensation_results],
            "requires_manual_intervention": self.requires_manual_intervention,
        }
