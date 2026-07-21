"""
Span Model

Single responsibility: Define trace span data model.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class SpanStatus(str, Enum):
    """Span execution status."""

    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


@dataclass
class SpanEvent:
    """An event that occurred during a span."""

    name: str
    timestamp: str
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "timestamp": self.timestamp,
            "attributes": self.attributes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SpanEvent":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            timestamp=data["timestamp"],
            attributes=data.get("attributes", {}),
        )


@dataclass
class Span:
    """
    A trace span representing a unit of work.

    Spans form a tree structure with parent-child relationships.
    Each span captures timing, status, and contextual information.
    """

    # Identity
    trace_id: str
    span_id: str = field(default_factory=lambda: str(uuid4())[:16])
    parent_span_id: Optional[str] = None

    # Description
    operation_name: str = ""
    service_name: str = "flyto"

    # Timing
    start_time: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    end_time: Optional[str] = None
    duration_ms: Optional[int] = None

    # Status
    status: SpanStatus = SpanStatus.UNSET
    status_message: Optional[str] = None

    # Data
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[SpanEvent] = field(default_factory=list)

    # Sampling
    is_recording: bool = True

    # Callback invoked when span ends (set by tracer)
    _on_end: Optional[Callable[["Span", SpanStatus, Optional[str]], None]] = field(
        default=None, repr=False, compare=False
    )

    def end(self, status: SpanStatus = SpanStatus.OK, message: Optional[str] = None) -> None:
        """
        End the span.

        Args:
            status: Final status
            message: Optional status message
        """
        if self.end_time is not None:
            logger.warning(f"Span {self.span_id} already ended")
            return

        self.end_time = datetime.now(timezone.utc).isoformat()
        self.status = status
        self.status_message = message

        # Calculate duration
        try:
            start = datetime.fromisoformat(self.start_time.replace("Z", "+00:00"))
            end = datetime.fromisoformat(self.end_time.replace("Z", "+00:00"))
            self.duration_ms = int((end - start).total_seconds() * 1000)
        except Exception:
            pass

    def set_attribute(self, key: str, value: Any) -> None:
        """
        Set a span attribute.

        Args:
            key: Attribute key
            value: Attribute value (must be serializable)
        """
        if not self.is_recording:
            return
        self.attributes[key] = value

    def set_attributes(self, attributes: Dict[str, Any]) -> None:
        """
        Set multiple span attributes.

        Args:
            attributes: Dictionary of attributes
        """
        if not self.is_recording:
            return
        self.attributes.update(attributes)

    def add_event(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
    ) -> None:
        """
        Add an event to the span.

        Args:
            name: Event name
            attributes: Optional event attributes
            timestamp: Optional timestamp (defaults to now)
        """
        if not self.is_recording:
            return

        event = SpanEvent(
            name=name,
            timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
            attributes=attributes or {},
        )
        self.events.append(event)

    def record_exception(self, exception: Exception) -> None:
        """
        Record an exception as a span event.

        Args:
            exception: The exception to record
        """
        self.add_event(
            name="exception",
            attributes={
                "exception.type": type(exception).__name__,
                "exception.message": str(exception),
            },
        )
        self.status = SpanStatus.ERROR
        self.status_message = str(exception)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "operation_name": self.operation_name,
            "service_name": self.service_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "status_message": self.status_message,
            "attributes": self.attributes,
            "events": [e.to_dict() for e in self.events],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Span":
        """Create from dictionary."""
        span = cls(
            trace_id=data["trace_id"],
            span_id=data.get("span_id", str(uuid4())[:16]),
            parent_span_id=data.get("parent_span_id"),
            operation_name=data.get("operation_name", ""),
            service_name=data.get("service_name", "flyto"),
            start_time=data.get("start_time", datetime.now(timezone.utc).isoformat()),
            end_time=data.get("end_time"),
            duration_ms=data.get("duration_ms"),
            status=SpanStatus(data.get("status", "unset")),
            status_message=data.get("status_message"),
            attributes=data.get("attributes", {}),
        )

        # Parse events
        for event_data in data.get("events", []):
            span.events.append(SpanEvent.from_dict(event_data))

        return span

    @property
    def is_root(self) -> bool:
        """Check if this is a root span (no parent)."""
        return self.parent_span_id is None

    @property
    def is_ended(self) -> bool:
        """Check if span has ended."""
        return self.end_time is not None

    def __enter__(self) -> "Span":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        if exc_val is not None:
            self.record_exception(exc_val)
        status = SpanStatus.ERROR if exc_val else SpanStatus.OK
        # Use callback if set (allows tracer to handle export)
        if self._on_end is not None:
            self._on_end(self, status, None)
        else:
            self.end(status=status)
