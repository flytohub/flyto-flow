"""
Telemetry Service - Centralized event collection and storage

Handles:
- Frontend errors
- Backend errors
- Business tracking events
- Sentry webhook events
- User analytics
- Funnel analysis
- Error flow analysis
- User presence/heartbeat tracking
- Event discovery

All events are stored in Firestore with trace_id correlation.
"""
import hashlib
import logging
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, Dict, Optional, Sequence

from .constants import MAX_QUERY_DOCS, SENSITIVE_FIELDS
from .stats_mixin import TelemetryStatsMixin
from .users_mixin import TelemetryUsersMixin
from .funnel_mixin import TelemetryFunnelMixin
from .errors_mixin import TelemetryErrorsMixin
from .presence_mixin import TelemetryPresenceMixin
from .discovery_mixin import TelemetryDiscoveryMixin
from .health_mixin import TelemetryHealthMixin

logger = logging.getLogger(__name__)


class _TelemetryDocumentAdapter:
    """Small document adapter used by the telemetry mixins."""

    def __init__(self, provider, target: str, doc_id: str | None = None) -> None:
        self._provider = provider
        self._target = target
        self.id = doc_id

    def set(self, data: dict[str, Any], merge: bool = False) -> None:
        if self._target == "presence":
            if self.id is None:
                raise ValueError("presence records require a document id")
            self._provider.save_presence(self.id, data, merge=merge)
            return
        self.id = self._provider.save_event(data)


class _TelemetryQueryAdapter:
    """Provider-neutral query adapter for existing telemetry analytics code."""

    def __init__(
        self,
        provider,
        target: str,
        filters: Sequence[tuple[str, str, Any]] = (),
        limit_value: int | None = None,
        order_by_value: tuple[str, Any] | None = None,
    ) -> None:
        self._provider = provider
        self._target = target
        self._filters = tuple(filters)
        self._limit = limit_value
        self._order_by = order_by_value

    def where(self, field: str, op: str, value: Any):
        return self.__class__(
            self._provider,
            self._target,
            (*self._filters, (field, op, value)),
            self._limit,
            self._order_by,
        )

    def limit(self, value: int):
        return self.__class__(
            self._provider,
            self._target,
            self._filters,
            value,
            self._order_by,
        )

    def order_by(self, field: str, direction=None):
        return self.__class__(
            self._provider,
            self._target,
            self._filters,
            self._limit,
            (field, direction),
        )

    def stream(self):
        if self._target == "presence":
            return self._provider.list_presence()
        return self._provider.query_events(
            filters=self._filters,
            limit=self._limit,
            order_by=self._order_by,
        )


class _TelemetryCollectionAdapter(_TelemetryQueryAdapter):
    """Collection adapter that supports document creation for telemetry writes."""

    def document(self, doc_id: str | None = None):
        return _TelemetryDocumentAdapter(self._provider, self._target, doc_id)


class TelemetryService(
    TelemetryStatsMixin,
    TelemetryUsersMixin,
    TelemetryFunnelMixin,
    TelemetryErrorsMixin,
    TelemetryPresenceMixin,
    TelemetryDiscoveryMixin,
    TelemetryHealthMixin,
):
    """Service for collecting and storing telemetry events"""

    def __init__(self, telemetry_provider=None):
        self._telemetry_provider = None
        try:
            self._telemetry_provider = telemetry_provider or _resolve_telemetry_provider()
            self._firestore = SimpleNamespace(
                SERVER_TIMESTAMP=self._telemetry_provider.server_timestamp,
                Query=SimpleNamespace(DESCENDING=self._telemetry_provider.descending_order),
            )
            self.collection = _TelemetryCollectionAdapter(self._telemetry_provider, "events")
            self.presence_collection = _TelemetryCollectionAdapter(
                self._telemetry_provider,
                "presence",
            )
        except Exception as e:
            logger.warning(f"Telemetry disabled (provider unavailable): {e}")
            self._firestore = None
            self.collection = None
            self.presence_collection = None

    def save_event(self, event: Dict[str, Any]) -> Optional[str]:
        """
        Save telemetry event to Firestore

        Args:
            event: Event data dictionary

        Returns:
            Document ID if saved, None if duplicate
        """
        if not self.collection:
            return None
        try:
            # Scrub sensitive data
            event = self._scrub_sensitive_data(event)

            # Generate dedupe key
            event["dedupe_key"] = self._generate_dedupe_key(event)

            # Check for duplicates
            if self._is_duplicate(event["dedupe_key"]):
                logger.debug(f"Duplicate event skipped: {event['dedupe_key']}")
                return None

            # Add Firestore timestamp
            event["created_at"] = self._firestore.SERVER_TIMESTAMP

            # Ensure timestamp exists
            if not event.get("timestamp"):
                event["timestamp"] = datetime.now(timezone.utc).isoformat() + "Z"

            # Write to Firestore
            doc_ref = self.collection.document()
            doc_ref.set(event)

            logger.info(
                f"Telemetry event saved: {event.get('event_type')}/{event.get('event_name')}"
            )
            return doc_ref.id

        except Exception as e:
            logger.error(f"Failed to save telemetry event: {e}")
            return None

    def _scrub_sensitive_data(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive fields from event data"""

        def scrub_dict(d: Any) -> Any:
            if not isinstance(d, dict):
                return d
            return {
                k: "[REDACTED]" if k.lower() in SENSITIVE_FIELDS else scrub_dict(v)
                for k, v in d.items()
            }

        # Scrub request headers and body
        if "request" in event and isinstance(event["request"], dict):
            if "headers" in event["request"]:
                event["request"]["headers"] = scrub_dict(event["request"]["headers"])
            if "body" in event["request"]:
                event["request"]["body"] = scrub_dict(event["request"]["body"])

        # Scrub properties
        if "properties" in event and isinstance(event["properties"], dict):
            event["properties"] = scrub_dict(event["properties"])

        return event

    def _generate_dedupe_key(self, event: Dict[str, Any]) -> str:
        """Generate deduplication key for event"""
        # Use event_type + event_name + error.message + timestamp (second precision)
        parts = [
            event.get("event_type", ""),
            event.get("event_name", ""),
            str(event.get("error", {}).get("message", "")),
            event.get("trace_id", ""),
            # Truncate timestamp to minute precision for dedup window
            (event.get("timestamp") or "")[:16],
        ]
        content = "|".join(parts)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _is_duplicate(self, dedupe_key: str) -> bool:
        """Check if event with same dedupe_key exists recently"""
        if not self._telemetry_provider:
            return False
        try:
            return self._telemetry_provider.has_event_with_dedupe_key(dedupe_key)
        except Exception as e:
            logger.warning(f"Dedupe check failed: {e}")
            return False

    def get_events(
        self,
        event_type: Optional[str] = None,
        trace_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Query telemetry events

        Args:
            event_type: Filter by event type
            trace_id: Filter by trace ID
            user_id: Filter by user ID
            limit: Maximum events to return
            offset: Number of events to skip

        Returns:
            Dictionary with items and total count
        """
        if not self.collection:
            return {"ok": True, "items": [], "total": 0}
        try:
            query = self.collection

            if event_type:
                query = query.where("event_type", "==", event_type)
            if trace_id:
                query = query.where("trace_id", "==", trace_id)
            if user_id:
                query = query.where("user_id", "==", user_id)

            # Order by created_at descending
            query = query.order_by("created_at", direction=self._firestore.Query.DESCENDING)

            # Stream with pagination: count total while skipping to the requested page
            total = 0
            skip_remaining = offset
            items = []

            for doc in query.limit(MAX_QUERY_DOCS).stream():
                total += 1
                if skip_remaining > 0:
                    skip_remaining -= 1
                    continue
                if len(items) < limit:
                    data = doc.to_dict()
                    data["id"] = doc.id
                    if data.get("created_at"):
                        data["created_at"] = data["created_at"].isoformat()
                    items.append(data)

            return {"ok": True, "items": items, "total": total}

        except Exception as e:
            logger.error(f"Failed to query telemetry events: {e}")
            return {"ok": False, "error": str(e), "items": [], "total": 0}

    def get_trace_timeline(self, trace_id: str) -> Dict[str, Any]:
        """
        Get all events for a trace ID, ordered by timestamp

        Args:
            trace_id: Trace ID to query

        Returns:
            Dictionary with events and metadata
        """
        if not self.collection:
            return {"ok": True, "trace_id": trace_id, "events": [], "duration_ms": 0, "has_error": False}
        try:
            # Query without order_by to avoid requiring composite index
            query = self.collection.where("trace_id", "==", trace_id).limit(1000)

            events = []
            has_error = False

            for doc in query.stream():
                data = doc.to_dict()
                data["id"] = doc.id
                if data.get("created_at"):
                    data["created_at"] = data["created_at"].isoformat()
                events.append(data)

                if data.get("event_type") in ("frontend_error", "backend_error", "sentry_event"):
                    has_error = True

            # Sort by timestamp in Python (avoid composite index requirement)
            events.sort(key=lambda x: x.get("timestamp", ""))

            # Calculate duration
            duration_ms = 0
            if len(events) >= 2:
                try:
                    first = datetime.fromisoformat(events[0]["timestamp"].replace("Z", "+00:00"))
                    last = datetime.fromisoformat(events[-1]["timestamp"].replace("Z", "+00:00"))
                    duration_ms = int((last - first).total_seconds() * 1000)
                except Exception:
                    pass

            return {
                "ok": True,
                "trace_id": trace_id,
                "events": events,
                "duration_ms": duration_ms,
                "has_error": has_error,
            }

        except Exception as e:
            logger.error(f"Failed to get trace timeline: {e}")
            return {"ok": False, "error": str(e), "trace_id": trace_id, "events": []}


def _resolve_telemetry_provider():
    from gateway.providers.hub import get_data_provider

    provider = get_data_provider()
    if provider is None:
        raise RuntimeError("Telemetry provider is not available without a data provider")
    return provider.telemetry
