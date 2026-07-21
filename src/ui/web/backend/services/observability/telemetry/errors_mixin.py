"""
Telemetry Errors Mixin - get_error_summary, get_error_flow, get_error_timeline, get_error_details
"""
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from .constants import MAX_QUERY_DOCS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers for get_error_details (extracted to reduce complexity)
# ---------------------------------------------------------------------------

_ERROR_TYPES = ("frontend_error", "backend_error", "sentry_event")


def _partition_docs(docs, event_name: str):
    """Split docs into session groups and matching error occurrences."""
    sessions: Dict[str, List[Dict]] = defaultdict(list)
    error_occurrences = []

    for doc in docs:
        data = doc.to_dict()
        data["_doc_id"] = doc.id
        session_id = data.get("session_id", "")
        if session_id:
            sessions[session_id].append(data)
        if data.get("event_name") == event_name and data.get("event_type") in _ERROR_TYPES:
            error_occurrences.append(data)

    return sessions, error_occurrences


def _describe_journey_event(evt: Dict) -> Dict:
    """Build a readable journey step from a session event."""
    evt_name = evt.get("event_name", "unknown")
    evt_props = evt.get("properties", {})
    evt_request = evt.get("request", {})

    step: Dict[str, Any] = {
        "event": evt_name,
        "timestamp": evt.get("timestamp"),
    }

    if evt_name == "page.view":
        step["description"] = f"Visited: {evt_props.get('path', evt_props.get('url', 'unknown page'))}"
        step["detail"] = evt_props.get("title", "")
    elif evt_name.startswith("button."):
        step["description"] = f"Clicked: {evt_props.get('buttonId', 'button')}"
    elif evt_name.startswith("api."):
        step["description"] = f"API: {evt_request.get('method', 'GET')} {evt_request.get('url', '')}"
        step["detail"] = f"Status: {evt_request.get('status', 'N/A')}"
    elif "error" in evt_name.lower():
        step["description"] = f"Error: {evt.get('error', {}).get('message', '')[:50]}"
    else:
        desc_parts = []
        for key in ["path", "page", "component", "action", "buttonId", "templateId"]:
            if key in evt_props:
                desc_parts.append(f"{key}={evt_props[key]}")
        step["description"] = f"{evt_name}: {', '.join(desc_parts[:3])}" if desc_parts else evt_name

    return step


def _build_user_journey(session_events: List[Dict], error_timestamp: str) -> List[Dict]:
    """Build the journey (last 10 events) leading up to an error."""
    sorted_events = sorted(session_events, key=lambda x: x.get("timestamp", ""))
    before_events = [
        e for e in sorted_events
        if e.get("timestamp", "") < error_timestamp
    ][-10:]
    return [_describe_journey_event(evt) for evt in before_events]


def _build_occurrence(data: Dict, sessions: Dict[str, List[Dict]]) -> Dict:
    """Assemble a single error occurrence dict with journey and context."""
    error_info = data.get("error", {})
    device = data.get("device", {})
    request = data.get("request", {})
    properties = data.get("properties", {})
    session_id = data.get("session_id", "")

    journey = []
    if session_id and session_id in sessions:
        journey = _build_user_journey(sessions[session_id], data.get("timestamp", ""))

    page = (
        request.get("url")
        or properties.get("path")
        or properties.get("page")
        or properties.get("component")
        or "unknown"
    )

    return {
        "id": data.get("_doc_id"),
        "timestamp": data.get("timestamp"),
        "message": error_info.get("message", "Unknown error"),
        "stack": error_info.get("stack"),
        "type": error_info.get("type", "Error"),
        "code": error_info.get("code"),
        "user_id": data.get("user_id"),
        "user_email": data.get("user_email"),
        "session_id": session_id,
        "browser": device.get("browser", "unknown"),
        "os": device.get("os", "unknown"),
        "page": page,
        "trace_id": data.get("trace_id"),
        "journey": journey,
        "context": {
            "component": properties.get("component"),
            "lifecycle": properties.get("lifecycle"),
            "action": properties.get("action"),
            "api_url": request.get("url"),
            "api_method": request.get("method"),
            "api_status": request.get("status"),
        },
    }


def _calculate_severity(count: int, user_count: int) -> str:
    """Derive severity label from occurrence and user counts."""
    if count >= 100 or user_count >= 20:
        return "critical"
    if count >= 20 or user_count >= 5:
        return "high"
    if count >= 5 or user_count >= 2:
        return "medium"
    return "low"


class TelemetryErrorsMixin:
    """Mixin for telemetry error analysis methods"""

    def get_error_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get summary of all errors

        Returns:
            Error summary with counts and affected users
        """
        if not self.collection:
            return {"ok": True, "errors": [], "total_errors": 0, "unique_errors": 0, "days": days}
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            cutoff_str = cutoff.isoformat() + "Z"

            query = self.collection.where("timestamp", ">=", cutoff_str).limit(MAX_QUERY_DOCS)
            docs = list(query.stream())

            # Filter errors
            errors: Dict[str, Dict] = {}

            for doc in docs:
                data = doc.to_dict()
                event_type = data.get("event_type", "")

                if event_type not in ("frontend_error", "backend_error", "sentry_event"):
                    continue

                event_name = data.get("event_name", "unknown")
                error_msg = data.get("error", {}).get("message", "Unknown error")
                user_id = data.get("user_id") or data.get("session_id") or "anonymous"

                # Create error key
                error_key = f"{event_name}:{error_msg[:100]}"

                if error_key not in errors:
                    errors[error_key] = {
                        "event_name": event_name,
                        "message": error_msg,
                        "count": 0,
                        "users": set(),
                        "first_seen": "",
                        "last_seen": "",
                        "source": data.get("source", "unknown")
                    }

                err = errors[error_key]
                err["count"] += 1
                err["users"].add(user_id)

                timestamp = data.get("timestamp", "")
                if timestamp:
                    if not err["first_seen"] or timestamp < err["first_seen"]:
                        err["first_seen"] = timestamp
                    if not err["last_seen"] or timestamp > err["last_seen"]:
                        err["last_seen"] = timestamp

            # Convert to list
            error_list = []
            for key, err in errors.items():
                err["user_count"] = len(err["users"])
                del err["users"]
                error_list.append(err)

            # Sort by count
            error_list.sort(key=lambda x: -x["count"])

            return {
                "ok": True,
                "errors": error_list[:50],
                "total_errors": sum(e["count"] for e in error_list),
                "unique_errors": len(error_list),
                "days": days
            }

        except Exception as e:
            logger.error(f"Failed to get error summary: {e}")
            return {"ok": False, "error": str(e)}

    @staticmethod
    def _find_error_sessions(sessions: Dict[str, list], event_name: str) -> list:
        """Find sessions that contain the specified error event."""
        error_types = ("frontend_error", "backend_error", "sentry_event")
        error_sessions = []
        for session_id, events in sessions.items():
            for i, event in enumerate(events):
                if event.get("event_name") == event_name and event.get("event_type") in error_types:
                    error_sessions.append({
                        "session_id": session_id,
                        "events": events,
                        "error_index": i,
                        "error_event": event,
                    })
                    break
        return error_sessions

    @staticmethod
    def _analyze_error_paths(error_sessions: list, event_name: str):
        """Analyze paths before/after error events. Returns (paths_before, paths_after, affected_users, error_messages)."""
        error_types = ("frontend_error", "backend_error", "sentry_event")
        paths_before: Dict[str, int] = defaultdict(int)
        paths_after: Dict[str, int] = defaultdict(int)
        affected_users = set()
        error_messages: Dict[str, int] = defaultdict(int)

        for session in error_sessions:
            events = sorted(session["events"], key=lambda x: x.get("timestamp", ""))
            error_idx = None

            for i, evt in enumerate(events):
                if evt.get("event_name") == event_name and evt.get("event_type") in error_types:
                    error_idx = i
                    error_msg = evt.get("error", {}).get("message", "Unknown")
                    error_messages[error_msg[:100]] += 1
                    user_id = evt.get("user_id") or evt.get("session_id")
                    if user_id:
                        affected_users.add(user_id)
                    break

            if error_idx is None:
                continue

            before_events = events[max(0, error_idx - 5):error_idx]
            path_before = " \u2192 ".join([e.get("event_name", "?") for e in before_events])
            if path_before:
                paths_before[path_before] += 1

            after_events = events[error_idx + 1:error_idx + 4]
            for evt in after_events:
                paths_after[evt.get("event_name", "unknown")] += 1

        return paths_before, paths_after, affected_users, error_messages

    def get_error_flow(self, event_name: str, days: int = 7) -> Dict[str, Any]:
        """
        Analyze the flow leading to and after an error

        Args:
            event_name: Error event name
            days: Time window

        Returns:
            Error flow analysis
        """
        empty_result = {"ok": True, "event_name": event_name, "occurrences": 0, "paths_before": [], "paths_after": [], "affected_users": 0}
        if not self.collection:
            return empty_result
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            cutoff_str = cutoff.isoformat() + "Z"

            query = self.collection.where("timestamp", ">=", cutoff_str).limit(MAX_QUERY_DOCS)
            docs = list(query.stream())

            # Group all events by session
            sessions: Dict[str, List[Dict]] = defaultdict(list)
            for doc in docs:
                data = doc.to_dict()
                session_id = data.get("session_id", "")
                if session_id:
                    sessions[session_id].append(data)

            error_sessions = self._find_error_sessions(sessions, event_name)
            if not error_sessions:
                return empty_result

            paths_before, paths_after, affected_users, error_messages = self._analyze_error_paths(error_sessions, event_name)

            top_paths_before = sorted(paths_before.items(), key=lambda x: -x[1])[:10]
            top_paths_after = sorted(paths_after.items(), key=lambda x: -x[1])[:10]
            top_messages = sorted(error_messages.items(), key=lambda x: -x[1])[:5]

            total_after = sum(paths_after.values())
            after_behavior = [
                {"action": action, "count": count, "percentage": round(count / total_after * 100, 1)}
                for action, count in top_paths_after
            ] if total_after > 0 else []

            return {
                "ok": True,
                "event_name": event_name,
                "occurrences": len(error_sessions),
                "affected_users": len(affected_users),
                "common_paths_before": [
                    {"path": path, "count": count}
                    for path, count in top_paths_before
                ],
                "after_behavior": after_behavior,
                "error_messages": [
                    {"message": msg, "count": count}
                    for msg, count in top_messages
                ],
                "days": days,
            }

        except Exception as e:
            logger.error(f"Failed to get error flow: {e}", exc_info=True)
            return {"ok": False, "error": str(e)}

    # =========================================================================
    # Enhanced Error Analysis
    # =========================================================================

    def get_error_timeline(self, days: int = 7, interval: str = "hour") -> Dict[str, Any]:
        """
        Get error counts over time for timeline chart

        Args:
            days: Time window in days
            interval: Grouping interval ('hour' or 'day')

        Returns:
            Timeline data with error counts
        """
        if not self.collection:
            return {"ok": True, "timeline": [], "summary": {"total": 0, "frontend_error": 0, "backend_error": 0, "sentry_event": 0}, "days": days, "interval": interval}
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            cutoff_str = cutoff.isoformat() + "Z"

            query = self.collection.where("timestamp", ">=", cutoff_str).limit(MAX_QUERY_DOCS)
            docs = list(query.stream())

            # Group by time interval
            timeline: Dict[str, Dict] = defaultdict(lambda: {
                "total": 0,
                "frontend_error": 0,
                "backend_error": 0,
                "sentry_event": 0
            })

            for doc in docs:
                data = doc.to_dict()
                event_type = data.get("event_type", "")

                if event_type not in ("frontend_error", "backend_error", "sentry_event"):
                    continue

                timestamp = data.get("timestamp", "")
                if not timestamp:
                    continue

                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

                    if interval == "hour":
                        key = dt.strftime("%Y-%m-%d %H:00")
                    else:
                        key = dt.strftime("%Y-%m-%d")

                    timeline[key]["total"] += 1
                    timeline[key][event_type] += 1
                except Exception:
                    pass

            # Convert to sorted list
            timeline_list = [
                {
                    "timestamp": ts,
                    "total": data["total"],
                    "frontend_error": data["frontend_error"],
                    "backend_error": data["backend_error"],
                    "sentry_event": data["sentry_event"]
                }
                for ts, data in sorted(timeline.items())
            ]

            # Calculate totals
            total_errors = sum(t["total"] for t in timeline_list)
            frontend_total = sum(t["frontend_error"] for t in timeline_list)
            backend_total = sum(t["backend_error"] for t in timeline_list)
            sentry_total = sum(t["sentry_event"] for t in timeline_list)

            return {
                "ok": True,
                "timeline": timeline_list,
                "summary": {
                    "total": total_errors,
                    "frontend_error": frontend_total,
                    "backend_error": backend_total,
                    "sentry_event": sentry_total
                },
                "days": days,
                "interval": interval
            }

        except Exception as e:
            logger.error(f"Failed to get error timeline: {e}")
            return {"ok": False, "error": str(e)}

    def get_error_details(self, event_name: str, days: int = 7, limit: int = 20) -> Dict[str, Any]:
        """
        Get detailed error information including full stack traces and user journey

        Args:
            event_name: Error event name
            days: Time window
            limit: Max occurrences to return

        Returns:
            Detailed error information with user journey
        """
        if not self.collection:
            return {"ok": True, "event_name": event_name, "occurrences": [], "total_occurrences": 0, "affected_users": 0, "severity": "low", "by_browser": [], "by_os": [], "by_page": [], "by_message": [], "days": days}
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            cutoff_str = cutoff.isoformat() + "Z"

            query = self.collection.where("timestamp", ">=", cutoff_str).limit(MAX_QUERY_DOCS)
            docs = list(query.stream())

            sessions, error_occurrences = _partition_docs(docs, event_name)

            # Build occurrences with journey and aggregate stats
            occurrences = []
            browsers: Dict[str, int] = defaultdict(int)
            os_counts: Dict[str, int] = defaultdict(int)
            pages: Dict[str, int] = defaultdict(int)
            messages: Dict[str, int] = defaultdict(int)
            affected_users = set()

            for data in error_occurrences:
                occurrence = _build_occurrence(data, sessions)
                occurrences.append(occurrence)

                browsers[occurrence["browser"]] += 1
                os_counts[occurrence["os"]] += 1
                pages[occurrence["page"]] += 1
                messages[occurrence["message"][:200]] += 1

                user_id = data.get("user_id") or data.get("session_id", "")
                if user_id:
                    affected_users.add(user_id)

            occurrences.sort(key=lambda x: x["timestamp"] or "", reverse=True)

            count = len(occurrences)
            user_count = len(affected_users)
            severity = _calculate_severity(count, user_count)

            return {
                "ok": True,
                "event_name": event_name,
                "occurrences": occurrences[:limit],
                "total_occurrences": count,
                "affected_users": user_count,
                "severity": severity,
                "by_browser": [{"name": k, "count": v} for k, v in sorted(browsers.items(), key=lambda x: -x[1])],
                "by_os": [{"name": k, "count": v} for k, v in sorted(os_counts.items(), key=lambda x: -x[1])],
                "by_page": [{"name": k, "count": v} for k, v in sorted(pages.items(), key=lambda x: -x[1])[:10]],
                "by_message": [{"message": k, "count": v} for k, v in sorted(messages.items(), key=lambda x: -x[1])[:5]],
                "days": days
            }

        except Exception as e:
            logger.error(f"Failed to get error details: {e}", exc_info=True)
            return {"ok": False, "error": str(e)}
