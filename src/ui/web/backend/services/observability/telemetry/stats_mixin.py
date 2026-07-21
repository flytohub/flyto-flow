"""
Telemetry Statistics Mixin - get_stats, get_overview
"""
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Set

from .constants import MAX_QUERY_DOCS

logger = logging.getLogger(__name__)


def _pct_change(current: int, previous: int) -> float:
    """Compute percentage change, returning 0 if previous is 0."""
    if previous <= 0:
        return 0
    return round((current - previous) / previous * 100, 1)


def _compute_trends(
    dau_today: int, dau_yesterday: int,
    wau: int, wau_prev: int,
    mau: int, mau_prev: int,
) -> Dict[str, float]:
    """Compute DAU/WAU/MAU trend percentages."""
    return {
        "dau_change": _pct_change(dau_today, dau_yesterday),
        "wau_change": _pct_change(wau, wau_prev),
        "mau_change": _pct_change(mau, mau_prev),
    }


def _build_dau_chart(now: datetime, daily_users: Dict[str, Set[str]]) -> list:
    """Build daily active users chart data for the last 14 days."""
    chart = []
    for i in range(13, -1, -1):
        date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        chart.append({"date": date, "count": len(daily_users.get(date, set()))})
    return chart


def _compute_avg_session_duration(session_times: Dict[str, Dict[str, str]]) -> str:
    """Compute and format average session duration from session timestamps."""
    total_duration = 0
    session_count = 0
    for _sess_id, times in session_times.items():
        if times["first"] and times["last"]:
            try:
                first = datetime.fromisoformat(times["first"].replace("Z", "+00:00"))
                last = datetime.fromisoformat(times["last"].replace("Z", "+00:00"))
                duration = (last - first).total_seconds()
                if duration > 0:
                    total_duration += duration
                    session_count += 1
            except Exception:
                pass

    avg_seconds = total_duration / session_count if session_count > 0 else 0
    if avg_seconds < 60:
        return f"{int(avg_seconds)}s"
    elif avg_seconds < 3600:
        return f"{int(avg_seconds // 60)}m {int(avg_seconds % 60)}s"
    else:
        return f"{int(avg_seconds // 3600)}h {int((avg_seconds % 3600) // 60)}m"


def _aggregate_events(query, now: datetime, days: int) -> dict:
    """Single-pass aggregation of events into user/session/error buckets."""
    daily_users: Dict[str, Set[str]] = defaultdict(set)
    weekly_users: Dict[int, Set[str]] = defaultdict(set)
    monthly_users: Set[str] = set()
    prior_month_users: Set[str] = set()
    total_events = 0
    error_events = 0
    events_by_name: Dict[str, int] = defaultdict(int)
    session_times: Dict[str, Dict[str, str]] = defaultdict(lambda: {"first": "", "last": ""})

    for doc in query.stream():
        data = doc.to_dict()
        total_events += 1
        user_id = data.get("user_id") or data.get("session_id") or "anonymous"
        timestamp = data.get("timestamp", "")
        event_name = data.get("event_name", "unknown")
        session_id = data.get("session_id", "")

        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                days_ago = (now - dt).days
                if days_ago < days:
                    daily_users[dt.strftime("%Y-%m-%d")].add(user_id)
                    weekly_users[days_ago // 7].add(user_id)
                    monthly_users.add(user_id)
                elif days_ago < days * 2:
                    prior_month_users.add(user_id)
            except Exception:
                pass

            if session_id:
                st = session_times[session_id]
                if not st["first"] or timestamp < st["first"]:
                    st["first"] = timestamp
                if not st["last"] or timestamp > st["last"]:
                    st["last"] = timestamp

        events_by_name[event_name] += 1
        if data.get("event_type") in ("frontend_error", "backend_error", "sentry_event"):
            error_events += 1

    return {
        "daily_users": daily_users,
        "weekly_users": weekly_users,
        "monthly_users": monthly_users,
        "prior_month_users": prior_month_users,
        "total_events": total_events,
        "error_events": error_events,
        "events_by_name": events_by_name,
        "session_times": session_times,
    }


class TelemetryStatsMixin:
    """Mixin for telemetry statistics methods"""

    def get_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get telemetry statistics

        Args:
            hours: Time window in hours

        Returns:
            Statistics dictionary
        """
        if not self.collection:
            return {"ok": True, "total_events": 0, "by_type": {}, "by_source": {}, "error_rate": 0}
        try:
            from datetime import timedelta

            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            cutoff_str = cutoff.isoformat() + "Z"

            query = self.collection.where("timestamp", ">=", cutoff_str).limit(MAX_QUERY_DOCS)
            docs = list(query.stream())

            stats = {
                "total_events": len(docs),
                "by_type": {},
                "by_source": {},
                "error_rate": 0,
            }

            error_count = 0
            for doc in docs:
                data = doc.to_dict()
                event_type = data.get("event_type", "unknown")
                source = data.get("source", "unknown")

                stats["by_type"][event_type] = stats["by_type"].get(event_type, 0) + 1
                stats["by_source"][source] = stats["by_source"].get(source, 0) + 1

                if event_type in ("frontend_error", "backend_error", "sentry_event"):
                    error_count += 1

            if stats["total_events"] > 0:
                stats["error_rate"] = round(error_count / stats["total_events"] * 100, 2)

            return {"ok": True, **stats}

        except Exception as e:
            logger.error(f"Failed to get telemetry stats: {e}")
            return {"ok": False, "error": str(e)}

    # =========================================================================
    # User Analytics
    # =========================================================================

    def get_overview(self, days: int = 30) -> Dict[str, Any]:
        """
        Get overview statistics including DAU, WAU, MAU, retention

        Args:
            days: Number of days to analyze

        Returns:
            Overview statistics
        """
        if not self.collection:
            return {
                "ok": True,
                "dau": 0,
                "wau": 0,
                "mau": 0,
                "trends": {"dau_change": 0, "wau_change": 0, "mau_change": 0},
                "total_events": 0,
                "total_errors": 0,
                "error_rate": 0,
                "avg_session_duration": "0s",
                "top_events": [],
                "dau_chart": []
            }
        try:
            from datetime import timezone
            now = datetime.now(timezone.utc)
            # Fetch 2x window to enable MAU trend comparison
            cutoff = now - timedelta(days=days * 2)
            cutoff_str = cutoff.isoformat().replace("+00:00", "Z")

            # Stream events with safety cap (avoid OOM on Cloud Run)
            query = self.collection.where("timestamp", ">=", cutoff_str).limit(MAX_QUERY_DOCS)

            agg = _aggregate_events(query, now, days)

            today = now.strftime("%Y-%m-%d")
            yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")

            dau_today = len(agg["daily_users"].get(today, set()))
            wau = len(agg["weekly_users"].get(0, set()))
            mau = len(agg["monthly_users"])

            trends = _compute_trends(
                dau_today, len(agg["daily_users"].get(yesterday, set())),
                wau, len(agg["weekly_users"].get(1, set())),
                mau, len(agg["prior_month_users"]),
            )
            dau_chart = _build_dau_chart(now, agg["daily_users"])
            avg_session_duration = _compute_avg_session_duration(agg["session_times"])
            top_events = sorted(agg["events_by_name"].items(), key=lambda x: -x[1])[:10]

            return {
                "ok": True,
                "dau": dau_today,
                "wau": wau,
                "mau": mau,
                "trends": trends,
                "total_events": agg["total_events"],
                "total_errors": agg["error_events"],
                "error_rate": round(agg["error_events"] / agg["total_events"] * 100, 2) if agg["total_events"] > 0 else 0,
                "avg_session_duration": avg_session_duration,
                "top_events": [{"name": name, "count": count} for name, count in top_events],
                "dau_chart": dau_chart,
            }

        except Exception as e:
            logger.error(f"Failed to get overview: {e}")
            return {"ok": False, "error": str(e)}
