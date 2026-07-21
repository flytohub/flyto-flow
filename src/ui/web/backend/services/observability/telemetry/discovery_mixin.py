"""
Telemetry Discovery Mixin - discover_events
"""
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from .constants import MAX_QUERY_DOCS

logger = logging.getLogger(__name__)


class TelemetryDiscoveryMixin:
    """Mixin for telemetry event discovery methods"""

    def discover_events(self, days: int = 30) -> Dict[str, Any]:
        """
        Discover all unique events in the system

        Args:
            days: Time window in days

        Returns:
            List of unique event names with counts and categories
        """
        if not self.collection:
            return {"ok": True, "events": [], "total_events": 0, "total_occurrences": 0, "categories": {}, "by_category": {}, "days": days}
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            cutoff_str = cutoff.isoformat() + "Z"

            query = self.collection.where("timestamp", ">=", cutoff_str).limit(MAX_QUERY_DOCS)
            docs = list(query.stream())

            # Aggregate events
            events: Dict[str, Dict] = {}
            categories: Dict[str, int] = defaultdict(int)

            for doc in docs:
                data = doc.to_dict()
                event_name = data.get("event_name", "unknown")
                event_type = data.get("event_type", "unknown")

                if event_name not in events:
                    events[event_name] = {
                        "event_name": event_name,
                        "event_type": event_type,
                        "count": 0,
                        "users": set(),
                        "first_seen": "",
                        "last_seen": ""
                    }

                evt = events[event_name]
                evt["count"] += 1

                user_id = data.get("user_id") or data.get("session_id")
                if user_id:
                    evt["users"].add(user_id)

                timestamp = data.get("timestamp", "")
                if timestamp:
                    if not evt["first_seen"] or timestamp < evt["first_seen"]:
                        evt["first_seen"] = timestamp
                    if not evt["last_seen"] or timestamp > evt["last_seen"]:
                        evt["last_seen"] = timestamp

                # Extract category from event name
                category = event_name.split(".")[0] if "." in event_name else "other"
                categories[category] += 1

            # Convert to list
            event_list = []
            for name, evt in events.items():
                evt["user_count"] = len(evt["users"])
                del evt["users"]

                # Extract category
                evt["category"] = name.split(".")[0] if "." in name else "other"
                event_list.append(evt)

            # Sort by count descending
            event_list.sort(key=lambda x: -x["count"])

            # Group by category
            by_category = defaultdict(list)
            for evt in event_list:
                by_category[evt["category"]].append(evt)

            return {
                "ok": True,
                "events": event_list,
                "total_events": len(event_list),
                "total_occurrences": sum(e["count"] for e in event_list),
                "categories": dict(categories),
                "by_category": dict(by_category),
                "days": days
            }

        except Exception as e:
            logger.error(f"Failed to discover events: {e}")
            return {"ok": False, "error": str(e)}
