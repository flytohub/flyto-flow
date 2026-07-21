"""
Telemetry Health Mixin - get_health_checks, get_health_summary, get_health_timeline
"""
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from .constants import MAX_QUERY_DOCS

logger = logging.getLogger(__name__)


class TelemetryHealthMixin:
    """Mixin for cloud health check data methods"""

    def get_health_checks(self, hours: int = 24, limit: int = 50) -> Dict[str, Any]:
        """Get recent health check results."""
        if not self.collection:
            return {"ok": True, "checks": [], "total": 0}
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            cutoff_str = cutoff.isoformat() + "Z"

            query = (
                self.collection
                .where("event_type", "==", "health_check")
                .where("timestamp", ">=", cutoff_str)
                .limit(limit)
            )
            docs = list(query.stream())

            checks = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                if data.get("created_at"):
                    data["created_at"] = data["created_at"].isoformat()
                checks.append(data)

            # Sort by timestamp descending
            checks.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            return {"ok": True, "checks": checks, "total": len(checks)}

        except Exception as e:
            logger.error(f"Failed to get health checks: {e}")
            return {"ok": False, "error": str(e), "checks": [], "total": 0}

    def get_health_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get health summary: uptime %, avg response time, failure count."""
        if not self.collection:
            return {
                "ok": True,
                "uptime_pct": 0,
                "avg_duration_ms": 0,
                "total_checks": 0,
                "healthy": 0,
                "degraded": 0,
                "down": 0,
                "current_status": "unknown",
                "last_check": None,
            }
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            cutoff_str = cutoff.isoformat() + "Z"

            query = (
                self.collection
                .where("event_type", "==", "health_check")
                .where("timestamp", ">=", cutoff_str)
                .limit(MAX_QUERY_DOCS)
            )

            total = 0
            healthy = 0
            degraded = 0
            down = 0
            total_duration = 0
            latest_timestamp = ""
            latest_status = "unknown"

            for doc in query.stream():
                data = doc.to_dict()
                total += 1
                props = data.get("properties", {})
                status = props.get("overall_status", "unknown")
                duration = props.get("duration_ms", 0)
                timestamp = data.get("timestamp", "")

                if status == "healthy":
                    healthy += 1
                elif status == "degraded":
                    degraded += 1
                elif status == "down":
                    down += 1

                total_duration += duration

                if timestamp > latest_timestamp:
                    latest_timestamp = timestamp
                    latest_status = status

            uptime_pct = round(healthy / total * 100, 2) if total > 0 else 0
            avg_duration = round(total_duration / total) if total > 0 else 0

            return {
                "ok": True,
                "uptime_pct": uptime_pct,
                "avg_duration_ms": avg_duration,
                "total_checks": total,
                "healthy": healthy,
                "degraded": degraded,
                "down": down,
                "current_status": latest_status,
                "last_check": latest_timestamp or None,
                "hours": hours,
            }

        except Exception as e:
            logger.error(f"Failed to get health summary: {e}")
            return {"ok": False, "error": str(e)}

    def get_health_timeline(self, hours: int = 24) -> Dict[str, Any]:
        """Get health check timeline for charting."""
        if not self.collection:
            return {"ok": True, "timeline": [], "hours": hours}
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            cutoff_str = cutoff.isoformat() + "Z"

            query = (
                self.collection
                .where("event_type", "==", "health_check")
                .where("timestamp", ">=", cutoff_str)
                .limit(MAX_QUERY_DOCS)
            )

            timeline = []
            for doc in query.stream():
                data = doc.to_dict()
                props = data.get("properties", {})
                layers = props.get("layers", {})

                point = {
                    "timestamp": data.get("timestamp", ""),
                    "overall_status": props.get("overall_status", "unknown"),
                    "duration_ms": props.get("duration_ms", 0),
                    "failed_checks": props.get("failed_checks", []),
                    "auth_ms": layers.get("auth", {}).get("duration_ms", 0),
                }

                # Extract per-endpoint durations
                for layer_name in ("public", "admin"):
                    layer = layers.get(layer_name, {})
                    if isinstance(layer, dict):
                        for endpoint, info in layer.items():
                            if isinstance(info, dict) and "duration_ms" in info:
                                point[f"{layer_name}_{endpoint}_ms"] = info["duration_ms"]

                timeline.append(point)

            # Sort by timestamp ascending for chart
            timeline.sort(key=lambda x: x.get("timestamp", ""))

            return {"ok": True, "timeline": timeline, "hours": hours}

        except Exception as e:
            logger.error(f"Failed to get health timeline: {e}")
            return {"ok": False, "error": str(e), "timeline": []}
