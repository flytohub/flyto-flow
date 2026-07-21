"""
Trace Context

Single responsibility: Context propagation via ContextVar.
"""

import logging
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from services.observability.tracing.span import Span


@dataclass
class TraceContext:
    """Trace context carrying trace and span information."""

    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    sampled: bool = True
    baggage: dict = field(default_factory=dict)

    def to_headers(self) -> dict:
        """
        Convert to HTTP headers for propagation.

        Returns:
            Dictionary of headers
        """
        headers = {
            "X-Trace-ID": self.trace_id,
            "X-Span-ID": self.span_id,
        }
        if self.parent_span_id:
            headers["X-Parent-Span-ID"] = self.parent_span_id
        if not self.sampled:
            headers["X-Trace-Sampled"] = "0"
        return headers

    @classmethod
    def from_headers(cls, headers: dict) -> Optional["TraceContext"]:
        """
        Create from HTTP headers.

        Args:
            headers: Dictionary of headers (case-insensitive)

        Returns:
            TraceContext or None if no trace info in headers
        """
        # Normalize header keys
        normalized = {k.lower(): v for k, v in headers.items()}

        trace_id = normalized.get("x-trace-id")
        if not trace_id:
            return None

        span_id = normalized.get("x-span-id", "")
        parent_span_id = normalized.get("x-parent-span-id")
        sampled = normalized.get("x-trace-sampled", "1") != "0"

        return cls(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            sampled=sampled,
        )


# Context variable for current span
_current_span: ContextVar[Optional["Span"]] = ContextVar("current_span", default=None)

# Context variable for trace context
_trace_context: ContextVar[Optional[TraceContext]] = ContextVar(
    "trace_context", default=None
)


def get_current_span() -> Optional["Span"]:
    """
    Get the current active span.

    Returns:
        Current span or None
    """
    return _current_span.get()


def set_current_span(span: Optional["Span"]) -> Token:
    """
    Set the current active span.

    Args:
        span: Span to set as current

    Returns:
        Token that can be used to reset the context
    """
    return _current_span.set(span)


def reset_current_span(token: Token) -> None:
    """
    Reset current span to previous value.

    Args:
        token: Token from set_current_span
    """
    _current_span.reset(token)


def get_trace_context() -> Optional[TraceContext]:
    """
    Get the current trace context.

    Returns:
        TraceContext or None
    """
    return _trace_context.get()


def set_trace_context(context: Optional[TraceContext]) -> Token:
    """
    Set the current trace context.

    Args:
        context: TraceContext to set

    Returns:
        Token that can be used to reset the context
    """
    return _trace_context.set(context)


def reset_trace_context(token: Token) -> None:
    """
    Reset trace context to previous value.

    Args:
        token: Token from set_trace_context
    """
    _trace_context.reset(token)


def get_current_trace_id() -> Optional[str]:
    """
    Get the current trace ID.

    Returns:
        Trace ID or None
    """
    span = get_current_span()
    if span:
        return span.trace_id

    ctx = get_trace_context()
    if ctx:
        return ctx.trace_id

    return None


def get_current_span_id() -> Optional[str]:
    """
    Get the current span ID.

    Returns:
        Span ID or None
    """
    span = get_current_span()
    if span:
        return span.span_id

    ctx = get_trace_context()
    if ctx:
        return ctx.span_id

    return None


def extract_context_from_headers(headers: dict) -> Optional[TraceContext]:
    """
    Extract trace context from HTTP headers.

    Args:
        headers: HTTP headers dictionary

    Returns:
        TraceContext or None
    """
    return TraceContext.from_headers(headers)


def inject_context_to_headers(headers: dict) -> dict:
    """
    Inject current trace context into HTTP headers.

    Args:
        headers: Existing headers dictionary

    Returns:
        Headers with trace context added
    """
    ctx = get_trace_context()
    if ctx:
        headers.update(ctx.to_headers())
    else:
        span = get_current_span()
        if span:
            headers["X-Trace-ID"] = span.trace_id
            headers["X-Span-ID"] = span.span_id
            if span.parent_span_id:
                headers["X-Parent-Span-ID"] = span.parent_span_id

    return headers
