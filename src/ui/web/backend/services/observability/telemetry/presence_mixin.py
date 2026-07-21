"""
Telemetry Presence Mixin - update_presence, get_online_users, get_users_with_presence
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from .constants import PRESENCE_TIMEOUT

logger = logging.getLogger(__name__)


class TelemetryPresenceMixin:
    """Mixin for telemetry presence/heartbeat tracking methods"""

    def update_presence(
        self,
        user_id: str,
        session_id: str,
        email: Optional[str] = None,
        page: Optional[str] = None,
        device: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Update user presence (heartbeat)

        Args:
            user_id: User ID
            session_id: Session ID
            email: User email
            page: Current page path
            device: Device info

        Returns:
            Success status
        """
        if not self.presence_collection:
            return {"ok": True, "last_seen": None}
        try:
            now = datetime.now(timezone.utc)
            last_seen = now.isoformat() + "Z"
            doc_ref = self.presence_collection.document(user_id)

            presence_data = {
                "user_id": user_id,
                "session_id": session_id,
                "email": email,
                "current_page": page,
                "device": device,
                "last_seen": last_seen,
                "updated_at": self._firestore.SERVER_TIMESTAMP
            }

            doc_ref.set(presence_data, merge=True)
            logger.info(f"Presence updated: user_id={user_id} last_seen={last_seen}")

            return {"ok": True, "last_seen": last_seen}

        except Exception as e:
            logger.error(f"Failed to update presence for {user_id}: {e}", exc_info=True)
            return {"ok": False, "error": str(e)}

    def get_online_users(self) -> Dict[str, Any]:
        """
        Get list of currently online users (active in last 2 minutes)

        Returns:
            List of online users with their current activity
        """
        if not self.presence_collection:
            return {"ok": True, "online_users": [], "count": 0, "cutoff": None}
        try:
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(seconds=PRESENCE_TIMEOUT)
            cutoff_str = cutoff.isoformat() + "Z"

            logger.info(f"Checking online users: now={now.isoformat()}Z cutoff={cutoff_str}")

            # Get all presence records
            docs = list(self.presence_collection.stream())
            logger.info(f"Found {len(docs)} presence records in Firestore")

            online_users = []
            offline_count = 0
            for doc in docs:
                data = doc.to_dict()
                last_seen = data.get("last_seen", "")
                user_id = data.get("user_id")

                if last_seen >= cutoff_str:
                    online_users.append({
                        "user_id": user_id,
                        "email": data.get("email"),
                        "session_id": data.get("session_id"),
                        "current_page": data.get("current_page"),
                        "device": data.get("device"),
                        "last_seen": last_seen,
                        "is_online": True
                    })
                    logger.debug(f"User {user_id} is ONLINE: last_seen={last_seen}")
                else:
                    offline_count += 1
                    logger.debug(f"User {user_id} is OFFLINE: last_seen={last_seen} < cutoff={cutoff_str}")

            logger.info(f"Online: {len(online_users)}, Offline: {offline_count}")

            # Sort by last_seen descending
            online_users.sort(key=lambda x: x["last_seen"], reverse=True)

            return {
                "ok": True,
                "online_users": online_users,
                "count": len(online_users),
                "cutoff": cutoff_str
            }

        except Exception as e:
            logger.error(f"Failed to get online users: {e}", exc_info=True)
            return {"ok": False, "error": str(e), "online_users": [], "count": 0}

    def get_users_with_presence(
        self,
        days: int = 7,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user list with online status

        Args:
            days: Time window in days
            limit: Maximum users to return
            offset: Number of users to skip
            search: Search by email

        Returns:
            User list with online status
        """
        if not self.presence_collection:
            return {"ok": True, "users": [], "total": 0, "online_count": 0}
        try:
            # First get basic user stats
            result = self.get_users(days=days, limit=limit, offset=offset, search=search)

            if not result.get("ok"):
                return result

            # Get ALL presence records (not just online)
            presence_data = {}
            try:
                docs = list(self.presence_collection.stream())
                logger.info(f"Found {len(docs)} presence records")
                for doc in docs:
                    data = doc.to_dict()
                    user_id = data.get("user_id")
                    if user_id:
                        presence_data[user_id] = {
                            "last_seen": data.get("last_seen"),
                            "current_page": data.get("current_page"),
                            "email": data.get("email"),
                            "device": data.get("device")
                        }
                        logger.debug(f"Presence: {user_id} -> {data.get('last_seen')}")
            except Exception as e:
                logger.warning(f"Failed to get presence data: {e}")

            # Determine online status cutoff
            cutoff = datetime.now(timezone.utc) - timedelta(seconds=PRESENCE_TIMEOUT)
            cutoff_str = cutoff.isoformat() + "Z"

            online_count = 0

            # Merge presence info into users
            user_ids_in_list = [u.get("user_id") for u in result.get("users", [])]
            logger.info(f"User IDs in list: {user_ids_in_list[:5]}...")
            logger.info(f"Presence user IDs: {list(presence_data.keys())[:5]}...")

            # Track which user IDs are already in the list
            existing_user_ids = set(u.get("user_id") for u in result.get("users", []))

            for user in result.get("users", []):
                user_id = user.get("user_id")

                if user_id in presence_data:
                    presence = presence_data[user_id]
                    presence_last_seen = presence.get("last_seen", "")

                    # Use presence last_seen if it's more recent
                    if presence_last_seen and presence_last_seen > (user.get("last_seen") or ""):
                        user["last_seen"] = presence_last_seen

                    # Check if online (active in last 2 minutes)
                    if presence_last_seen and presence_last_seen >= cutoff_str:
                        user["is_online"] = True
                        user["current_page"] = presence.get("current_page")
                        online_count += 1
                    else:
                        user["is_online"] = False
                        user["current_page"] = None
                else:
                    user["is_online"] = False
                    user["current_page"] = None

            # Add heartbeat-only users (users with presence but no telemetry events)
            for user_id, presence in presence_data.items():
                if user_id in existing_user_ids:
                    continue

                presence_last_seen = presence.get("last_seen", "")
                email = presence.get("email", "")

                # Apply search filter if provided
                if search and search.lower() not in email.lower():
                    continue

                is_online = presence_last_seen and presence_last_seen >= cutoff_str
                if is_online:
                    online_count += 1

                result["users"].append({
                    "user_id": user_id,
                    "email": email,
                    "event_count": 0,
                    "error_count": 0,
                    "session_count": 1,
                    "last_seen": presence_last_seen,
                    "first_seen": presence_last_seen,
                    "is_online": is_online,
                    "current_page": presence.get("current_page") if is_online else None,
                    "device": presence.get("device")
                })

            # Update total count
            result["total"] = len(result["users"])

            # Re-sort by last_seen after updating
            result["users"] = sorted(
                result.get("users", []),
                key=lambda x: x.get("last_seen") or "",
                reverse=True
            )

            # Add online count to response
            result["online_count"] = online_count

            return result

        except Exception as e:
            logger.error(f"Failed to get users with presence: {e}")
            return {"ok": False, "error": str(e), "users": [], "total": 0}
