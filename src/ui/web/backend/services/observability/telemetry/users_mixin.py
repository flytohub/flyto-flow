"""
Telemetry Users Mixin - get_users, get_user_timeline, get_user_sessions
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .constants import MAX_QUERY_DOCS

logger = logging.getLogger(__name__)


class TelemetryUsersMixin:
    """Mixin for telemetry user analytics methods"""

    def get_users(
        self,
        days: int = 7,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user list with activity statistics

        Args:
            days: Time window in days
            limit: Maximum users to return
            offset: Number of users to skip
            search: Search by email

        Returns:
            User list with statistics
        """
        if not self.collection:
            return {"ok": True, "users": [], "total": 0}
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            cutoff_str = cutoff.isoformat() + "Z"

            query = self.collection.where("timestamp", ">=", cutoff_str).limit(MAX_QUERY_DOCS)
            docs = list(query.stream())

            # Aggregate by user
            user_stats: Dict[str, Dict] = {}

            for doc in docs:
                data = doc.to_dict()
                user_id = data.get("user_id")
                if not user_id:
                    continue

                user_email = data.get("user_email", "")

                # Apply search filter
                if search and search.lower() not in user_email.lower():
                    continue

                if user_id not in user_stats:
                    user_stats[user_id] = {
                        "user_id": user_id,
                        "email": user_email,
                        "event_count": 0,
                        "error_count": 0,
                        "sessions": set(),
                        "last_seen": "",
                        "first_seen": "",
                        "device": None
                    }

                stats = user_stats[user_id]
                stats["event_count"] += 1
                stats["sessions"].add(data.get("session_id", ""))

                timestamp = data.get("timestamp", "")
                if timestamp:
                    if not stats["first_seen"] or timestamp < stats["first_seen"]:
                        stats["first_seen"] = timestamp
                    if not stats["last_seen"] or timestamp > stats["last_seen"]:
                        stats["last_seen"] = timestamp

                if data.get("event_type") in ("frontend_error", "backend_error"):
                    stats["error_count"] += 1

                if not stats["device"] and data.get("device"):
                    stats["device"] = data.get("device")

            # Convert to list and sort by last_seen
            users = list(user_stats.values())
            for u in users:
                u["session_count"] = len(u["sessions"]) - (1 if "" in u["sessions"] else 0)
                del u["sessions"]

            users.sort(key=lambda x: x["last_seen"], reverse=True)

            # Paginate
            total = len(users)
            users = users[offset:offset + limit]

            return {
                "ok": True,
                "users": users,
                "total": total
            }

        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            return {"ok": False, "error": str(e), "users": [], "total": 0}

    def get_user_timeline(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 200
    ) -> Dict[str, Any]:
        """
        Get user's event timeline

        Args:
            user_id: User ID
            session_id: Optional session ID filter
            limit: Maximum events

        Returns:
            Timeline of user events
        """
        if not self.collection:
            return {"ok": True, "user_id": user_id, "email": "", "device": None, "events": [], "event_count": 0, "session_count": 0, "error_count": 0, "errors": []}
        try:
            query = self.collection.where("user_id", "==", user_id).limit(MAX_QUERY_DOCS)
            docs = list(query.stream())

            events = []
            sessions_set = set()
            device_info = None
            errors = []

            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id

                if data.get("created_at"):
                    data["created_at"] = data["created_at"].isoformat()

                sess_id = data.get("session_id", "")
                if session_id and sess_id != session_id:
                    continue

                sessions_set.add(sess_id)
                events.append(data)

                if not device_info and data.get("device"):
                    device_info = data.get("device")

                if data.get("event_type") in ("frontend_error", "backend_error", "sentry_event"):
                    errors.append({
                        "event_name": data.get("event_name"),
                        "message": data.get("error", {}).get("message", ""),
                        "timestamp": data.get("timestamp")
                    })

            # Sort by timestamp
            events.sort(key=lambda x: x.get("timestamp", ""))

            # Limit
            if len(events) > limit:
                events = events[-limit:]

            # Get user info
            user_email = events[0].get("user_email", "") if events else ""

            return {
                "ok": True,
                "user_id": user_id,
                "email": user_email,
                "device": device_info,
                "events": events,
                "event_count": len(events),
                "session_count": len(sessions_set) - (1 if "" in sessions_set else 0),
                "error_count": len(errors),
                "errors": errors[:10]  # Last 10 errors
            }

        except Exception as e:
            logger.error(f"Failed to get user timeline: {e}")
            return {"ok": False, "error": str(e), "events": []}

    def get_user_sessions(self, user_id: str, limit: int = 20) -> Dict[str, Any]:
        """
        Get user's session list

        Args:
            user_id: User ID
            limit: Maximum sessions

        Returns:
            List of sessions with summary
        """
        if not self.collection:
            return {"ok": True, "sessions": [], "total": 0}
        try:
            query = self.collection.where("user_id", "==", user_id).limit(MAX_QUERY_DOCS)
            docs = list(query.stream())

            # Group by session
            sessions: Dict[str, Dict] = {}

            for doc in docs:
                data = doc.to_dict()
                session_id = data.get("session_id", "")
                if not session_id:
                    continue

                if session_id not in sessions:
                    sessions[session_id] = {
                        "session_id": session_id,
                        "event_count": 0,
                        "error_count": 0,
                        "start_time": "",
                        "end_time": "",
                        "device": None,
                        "pages": set()
                    }

                sess = sessions[session_id]
                sess["event_count"] += 1

                timestamp = data.get("timestamp", "")
                if timestamp:
                    if not sess["start_time"] or timestamp < sess["start_time"]:
                        sess["start_time"] = timestamp
                    if not sess["end_time"] or timestamp > sess["end_time"]:
                        sess["end_time"] = timestamp

                if data.get("event_type") in ("frontend_error", "backend_error"):
                    sess["error_count"] += 1

                if not sess["device"] and data.get("device"):
                    sess["device"] = data.get("device")

                # Track pages visited
                if data.get("event_name") == "page.view":
                    path = data.get("properties", {}).get("path", "")
                    if path:
                        sess["pages"].add(path)

            # Convert to list
            session_list = list(sessions.values())
            for s in session_list:
                s["pages_visited"] = len(s["pages"])
                s["pages"] = list(s["pages"])[:5]  # First 5 pages

                # Calculate duration
                if s["start_time"] and s["end_time"]:
                    try:
                        start = datetime.fromisoformat(s["start_time"].replace("Z", "+00:00"))
                        end = datetime.fromisoformat(s["end_time"].replace("Z", "+00:00"))
                        s["duration_seconds"] = int((end - start).total_seconds())
                    except Exception:
                        s["duration_seconds"] = 0
                else:
                    s["duration_seconds"] = 0

            # Sort by start time descending
            session_list.sort(key=lambda x: x["start_time"], reverse=True)

            return {
                "ok": True,
                "sessions": session_list[:limit],
                "total": len(session_list)
            }

        except Exception as e:
            logger.error(f"Failed to get user sessions: {e}")
            return {"ok": False, "error": str(e), "sessions": []}
