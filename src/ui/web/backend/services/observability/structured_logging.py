"""
Structured Logging Service

Provides JSON-formatted logs with execution context for observability.
All logs include exec_id, node_id, trace_id for correlation.

SECURITY: Includes automatic redaction of sensitive data in logs.
"""

import json
import logging
import re
import sys
import time
from contextvars import ContextVar
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Callable
from functools import wraps


# SECURITY: Patterns for sensitive keys that should be redacted
SENSITIVE_KEY_PATTERNS = re.compile(
    r'(?i)(api[_-]?key|secret|password|token|credential|auth|private[_-]?key|bearer|jwt)',
    re.IGNORECASE
)

# SECURITY: Patterns for sensitive values (e.g., API keys, tokens)
SENSITIVE_VALUE_PATTERNS = [
    re.compile(r'sk-[a-zA-Z0-9]{20,}'),  # OpenAI-style keys
    re.compile(r'[A-Za-z0-9+/]{40,}={0,2}'),  # Base64 long strings (potential tokens)
    re.compile(r'ghp_[a-zA-Z0-9]{36}'),  # GitHub personal access tokens
    re.compile(r'gho_[a-zA-Z0-9]{36}'),  # GitHub OAuth tokens
    re.compile(r'Bearer\s+[A-Za-z0-9\-_\.]+'),  # Bearer tokens
]


def _redact_sensitive_value(value: Any) -> Any:
    """
    Redact sensitive values from log data.

    SECURITY: Prevents accidental logging of secrets.
    """
    if value is None:
        return value

    if isinstance(value, str):
        # Check if value matches sensitive patterns
        for pattern in SENSITIVE_VALUE_PATTERNS:
            if pattern.search(value):
                return '[REDACTED]'
        # Truncate very long strings that might be tokens
        if len(value) > 500:
            return value[:100] + '...[TRUNCATED]'
        return value

    if isinstance(value, dict):
        return _redact_sensitive_dict(value)

    if isinstance(value, (list, tuple)):
        return [_redact_sensitive_value(item) for item in value]

    return value


def _redact_sensitive_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Redact sensitive data from a dictionary.

    SECURITY: Scans both keys and values for sensitive patterns.
    """
    if not data:
        return data

    redacted = {}
    for key, value in data.items():
        # Check if key name suggests sensitive data
        if SENSITIVE_KEY_PATTERNS.search(str(key)):
            redacted[key] = '[REDACTED]'
        else:
            redacted[key] = _redact_sensitive_value(value)

    return redacted


# Context variables for log correlation
_exec_context: ContextVar[Optional["ExecutionLogContext"]] = ContextVar(
    "exec_context", default=None
)


@dataclass
class ExecutionLogContext:
    """Context for correlating logs within an execution."""

    exec_id: str
    workflow_id: Optional[str] = None
    workflow_name: Optional[str] = None
    user_id: Optional[str] = None
    trace_id: Optional[str] = None
    node_id: Optional[str] = None
    node_run_id: Optional[str] = None
    step_index: Optional[int] = None
    attempt_no: Optional[int] = None
    module_id: Optional[str] = None
    worker_id: Optional[str] = None
    span_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    def with_node(
        self,
        node_id: str,
        node_run_id: Optional[str] = None,
        step_index: Optional[int] = None,
        attempt_no: Optional[int] = None,
        module_id: Optional[str] = None,
    ) -> "ExecutionLogContext":
        """Create a new context with node-level info."""
        return ExecutionLogContext(
            exec_id=self.exec_id,
            workflow_id=self.workflow_id,
            workflow_name=self.workflow_name,
            user_id=self.user_id,
            trace_id=self.trace_id,
            worker_id=self.worker_id,
            node_id=node_id,
            node_run_id=node_run_id,
            step_index=step_index,
            attempt_no=attempt_no,
            module_id=module_id,
            span_id=self.span_id,
        )


class ExecutionContextManager:
    """Context manager for setting execution log context."""

    def __init__(self, context: ExecutionLogContext):
        """Initialize with the execution log context to set."""
        self.context = context
        self._token = None

    def __enter__(self) -> ExecutionLogContext:
        """Set the execution context and return it."""
        self._token = _exec_context.set(self.context)
        return self.context

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Reset the execution context to its previous value."""
        if self._token:
            _exec_context.reset(self._token)
        return False


def get_current_context() -> Optional[ExecutionLogContext]:
    """Get the current execution log context."""
    return _exec_context.get()


def set_context(context: ExecutionLogContext) -> None:
    """Set the current execution log context."""
    _exec_context.set(context)


def clear_context() -> None:
    """Clear the current execution log context."""
    _exec_context.set(None)


class JsonLogFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.

    Output format:
    {"time": "2025-12-23T10:30:01Z", "level": "INFO", "msg": "...", "exec_id": "...", ...}
    """

    def __init__(
        self,
        include_context: bool = True,
        include_extra: bool = True,
        include_exception: bool = True,
    ):
        """Initialize formatter with toggles for context, extras, and exceptions."""
        super().__init__()
        self.include_context = include_context
        self.include_extra = include_extra
        self.include_exception = include_exception

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "time": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }

        # Add source location for errors
        if record.levelno >= logging.ERROR:
            log_data["source"] = {
                "file": record.pathname,
                "line": record.lineno,
                "func": record.funcName,
            }

        # Add execution context
        if self.include_context:
            context = get_current_context()
            if context:
                log_data.update(context.to_dict())

        # Add extra fields from record
        if self.include_extra:
            extra_fields = {
                k: v
                for k, v in record.__dict__.items()
                if k not in (
                    "name",
                    "msg",
                    "args",
                    "created",
                    "filename",
                    "funcName",
                    "levelname",
                    "levelno",
                    "lineno",
                    "module",
                    "msecs",
                    "pathname",
                    "process",
                    "processName",
                    "relativeCreated",
                    "stack_info",
                    "exc_info",
                    "exc_text",
                    "thread",
                    "threadName",
                    "message",
                    "taskName",
                )
                and not k.startswith("_")
            }
            if extra_fields:
                # SECURITY: Redact sensitive data from extra fields
                log_data["extra"] = _redact_sensitive_dict(extra_fields)

        # Add exception info
        if self.include_exception and record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str, ensure_ascii=False)


class StructuredLogger:
    """
    Structured logger with execution context support.

    Usage:
        logger = StructuredLogger(__name__)

        with logger.execution_context(exec_id="abc123"):
            logger.info("Execution started")

            with logger.node_context(node_id="node_1"):
                logger.info("Node started")
    """

    def __init__(self, name: str):
        """Initialize with a logger name."""
        self._logger = logging.getLogger(name)

    @property
    def logger(self) -> logging.Logger:
        """Return the underlying standard library logger."""
        return self._logger

    def execution_context(
        self,
        exec_id: str,
        workflow_id: Optional[str] = None,
        workflow_name: Optional[str] = None,
        user_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        worker_id: Optional[str] = None,
    ) -> ExecutionContextManager:
        """Create an execution context manager."""
        context = ExecutionLogContext(
            exec_id=exec_id,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            user_id=user_id,
            trace_id=trace_id or exec_id,  # Use exec_id as trace_id if not provided
            worker_id=worker_id,
        )
        return ExecutionContextManager(context)

    def node_context(
        self,
        node_id: str,
        node_run_id: Optional[str] = None,
        step_index: Optional[int] = None,
        attempt_no: Optional[int] = None,
        module_id: Optional[str] = None,
    ) -> ExecutionContextManager:
        """Create a node context manager (extends current execution context)."""
        current = get_current_context()
        if current:
            context = current.with_node(
                node_id=node_id,
                node_run_id=node_run_id,
                step_index=step_index,
                attempt_no=attempt_no,
                module_id=module_id,
            )
        else:
            # No execution context, create standalone node context
            context = ExecutionLogContext(
                exec_id="unknown",
                node_id=node_id,
                node_run_id=node_run_id,
                step_index=step_index,
                attempt_no=attempt_no,
                module_id=module_id,
            )
        return ExecutionContextManager(context)

    def _log(
        self,
        level: int,
        msg: str,
        *args,
        exc_info: bool = False,
        **kwargs,
    ) -> None:
        """Internal log method with extra context."""
        self._logger.log(level, msg, *args, exc_info=exc_info, extra=kwargs)

    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        """Log info message."""
        self._log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log warning message."""
        self._log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args, exc_info: bool = True, **kwargs) -> None:
        """Log error message (includes exception by default)."""
        self._log(logging.ERROR, msg, *args, exc_info=exc_info, **kwargs)

    def critical(self, msg: str, *args, exc_info: bool = True, **kwargs) -> None:
        """Log critical message."""
        self._log(logging.CRITICAL, msg, *args, exc_info=exc_info, **kwargs)

    def node_started(
        self,
        node_id: str,
        module_id: str,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log node execution started event."""
        self.info(
            "Node execution started",
            event="node_started",
            node_id=node_id,
            module_id=module_id,
            inputs_keys=list(inputs.keys()) if inputs else [],
        )

    def node_succeeded(
        self,
        node_id: str,
        module_id: str,
        duration_ms: int,
        outputs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log node execution succeeded event."""
        self.info(
            "Node execution succeeded",
            event="node_succeeded",
            node_id=node_id,
            module_id=module_id,
            duration_ms=duration_ms,
            outputs_keys=list(outputs.keys()) if outputs else [],
        )

    def node_failed(
        self,
        node_id: str,
        module_id: str,
        error: str,
        error_type: Optional[str] = None,
        duration_ms: Optional[int] = None,
        retryable: bool = False,
    ) -> None:
        """Log node execution failed event."""
        self.error(
            "Node execution failed",
            event="node_failed",
            node_id=node_id,
            module_id=module_id,
            error=error,
            error_type=error_type,
            duration_ms=duration_ms,
            retryable=retryable,
            exc_info=False,
        )

    def node_skipped(
        self,
        node_id: str,
        module_id: str,
        reason: str,
    ) -> None:
        """Log node execution skipped event."""
        self.info(
            "Node execution skipped",
            event="node_skipped",
            node_id=node_id,
            module_id=module_id,
            reason=reason,
        )

    def execution_started(
        self,
        exec_id: str,
        workflow_id: str,
        workflow_name: Optional[str] = None,
    ) -> None:
        """Log workflow execution started event."""
        self.info(
            "Workflow execution started",
            event="execution_started",
            exec_id=exec_id,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
        )

    def execution_completed(
        self,
        exec_id: str,
        status: str,
        duration_ms: int,
        total_steps: int,
        succeeded_steps: int,
        failed_steps: int,
    ) -> None:
        """Log workflow execution completed event."""
        level = logging.INFO if status == "success" else logging.WARNING
        self._log(
            level,
            f"Workflow execution {status}",
            event="execution_completed",
            exec_id=exec_id,
            status=status,
            duration_ms=duration_ms,
            total_steps=total_steps,
            succeeded_steps=succeeded_steps,
            failed_steps=failed_steps,
        )


def setup_json_logging(
    level: int = logging.INFO,
    stream: Any = None,
    include_context: bool = True,
) -> None:
    """
    Configure root logger for JSON output.

    Args:
        level: Logging level
        stream: Output stream (defaults to sys.stdout)
        include_context: Whether to include execution context
    """
    if stream is None:
        stream = sys.stdout

    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonLogFormatter(include_context=include_context))

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)


def log_execution(func: Callable) -> Callable:
    """
    Decorator to log function execution with timing.

    Usage:
        @log_execution
        async def process_item(item_id: str):
            ...
    """
    logger = StructuredLogger(func.__module__)

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = func.__name__

        logger.debug(f"Starting {func_name}", function=func_name)
        try:
            result = await func(*args, **kwargs)
            duration_ms = int((time.time() - start_time) * 1000)
            logger.debug(
                f"Completed {func_name}",
                function=func_name,
                duration_ms=duration_ms,
            )
            return result
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Failed {func_name}: {e}",
                function=func_name,
                duration_ms=duration_ms,
            )
            raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = func.__name__

        logger.debug(f"Starting {func_name}", function=func_name)
        try:
            result = func(*args, **kwargs)
            duration_ms = int((time.time() - start_time) * 1000)
            logger.debug(
                f"Completed {func_name}",
                function=func_name,
                duration_ms=duration_ms,
            )
            return result
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Failed {func_name}: {e}",
                function=func_name,
                duration_ms=duration_ms,
            )
            raise

    import asyncio

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


# Convenience function to get a structured logger
def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)
