"""
Tracer

Single responsibility: Create and manage trace spans.
"""

import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional
from uuid import uuid4

from services.observability.tracing.span import Span, SpanStatus
from services.observability.tracing.context import get_current_span, set_current_span

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from services.observability.tracing.exporter import TraceExporter
    from services.observability.tracing.sampler import TraceSampler


class Tracer:
    """
    Tracer for creating and managing spans.

    Provides methods to create spans, manage parent-child relationships,
    and export completed spans.
    """

    def __init__(
        self,
        service_name: str = "flyto",
        sampler: Optional["TraceSampler"] = None,
        exporter: Optional["TraceExporter"] = None,
    ):
        """
        Initialize tracer.

        Args:
            service_name: Name of the service
            sampler: Optional sampler for sampling decisions
            exporter: Optional exporter for span export
        """
        self.service_name = service_name
        self._sampler = sampler
        self._exporter = exporter
        self._active_spans: Dict[str, Span] = {}

    def start_span(
        self,
        name: str,
        parent: Optional[Span] = None,
        trace_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Span:
        """
        Start a new span.

        Args:
            name: Operation name
            parent: Optional parent span
            trace_id: Optional trace ID (generates new if not provided)
            attributes: Optional initial attributes

        Returns:
            New span
        """
        # Determine parent
        if parent is None:
            parent = get_current_span()

        # Determine trace ID
        if trace_id is None:
            if parent:
                trace_id = parent.trace_id
            else:
                trace_id = str(uuid4())

        # Create span with end callback
        span = Span(
            trace_id=trace_id,
            span_id=str(uuid4())[:16],
            parent_span_id=parent.span_id if parent else None,
            operation_name=name,
            service_name=self.service_name,
            attributes=attributes or {},
            _on_end=self.end_span,
        )

        # Check sampling
        if self._sampler:
            from services.observability.tracing.sampler import SamplingDecision
            decision = self._sampler.should_sample(trace_id, span.attributes)
            span.is_recording = decision == SamplingDecision.RECORD

        # Track active span
        self._active_spans[span.span_id] = span

        # Set as current span
        set_current_span(span)

        return span

    def end_span(
        self,
        span: Span,
        status: SpanStatus = SpanStatus.OK,
        message: Optional[str] = None,
    ) -> None:
        """
        End a span.

        Args:
            span: Span to end
            status: Final status
            message: Optional status message
        """
        span.end(status, message)

        # Remove from active spans
        self._active_spans.pop(span.span_id, None)

        # Export if we have an exporter
        if self._exporter and span.is_recording:
            try:
                self._exporter.export([span])
            except Exception as e:
                logger.error(f"Failed to export span: {e}")

        # Restore parent as current span
        if span.parent_span_id and span.parent_span_id in self._active_spans:
            parent = self._active_spans[span.parent_span_id]
            set_current_span(parent)

    def create_span(
        self,
        name: str,
        parent: Optional[Span] = None,
        **attributes,
    ) -> Span:
        """
        Create a span as a context manager.

        Usage:
            with tracer.create_span("operation") as span:
                # do work
                span.set_attribute("key", "value")

        Args:
            name: Operation name
            parent: Optional parent span
            **attributes: Initial attributes

        Returns:
            Span that can be used as context manager
        """
        return self.start_span(name, parent, attributes=attributes)

    def get_active_spans(self) -> List[Span]:
        """Get all active spans."""
        return list(self._active_spans.values())

    def get_span(self, span_id: str) -> Optional[Span]:
        """Get an active span by ID."""
        return self._active_spans.get(span_id)


# Global tracer instance
_tracer: Optional[Tracer] = None


def get_tracer(
    service_name: str = "flyto",
    sampler: Optional["TraceSampler"] = None,
    exporter: Optional["TraceExporter"] = None,
) -> Tracer:
    """
    Get or create the global tracer.

    Args:
        service_name: Service name (only used on first call)
        sampler: Optional sampler
        exporter: Optional exporter

    Returns:
        Global tracer instance
    """
    global _tracer
    if _tracer is None:
        _tracer = Tracer(
            service_name=service_name,
            sampler=sampler,
            exporter=exporter,
        )
    return _tracer


def trace(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
) -> Callable:
    """
    Decorator to trace a function.

    Usage:
        @trace("my_operation")
        async def my_function():
            ...

    Args:
        name: Operation name (defaults to function name)
        attributes: Initial span attributes

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        import asyncio
        import functools

        operation_name = name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            span = tracer.start_span(operation_name, attributes=attributes)
            try:
                result = await func(*args, **kwargs)
                tracer.end_span(span, SpanStatus.OK)
                return result
            except Exception as e:
                span.record_exception(e)
                tracer.end_span(span, SpanStatus.ERROR, str(e))
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            span = tracer.start_span(operation_name, attributes=attributes)
            try:
                result = func(*args, **kwargs)
                tracer.end_span(span, SpanStatus.OK)
                return result
            except Exception as e:
                span.record_exception(e)
                tracer.end_span(span, SpanStatus.ERROR, str(e))
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
