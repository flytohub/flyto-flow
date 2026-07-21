"""
Offline Notification Provider

SQLite-backed notification operations for offline/desktop mode.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from gateway.providers.data.base import NotificationProvider
from gateway.providers.data.models import (
    NotificationDTO,
    NotificationCreateDTO,
    PaginatedResponse,
)
from gateway.storage.offline_db import get_offline_cursor

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso() -> str:
    return _utc_now().isoformat()


def _parse_dt(val: Optional[str]) -> Optional[datetime]:
    if not val:
        return None
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


class OfflineNotificationProvider(NotificationProvider):
    """Offline implementation — SQLite-backed notifications."""

    async def list_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        with get_offline_cursor() as cursor:
            sql = "SELECT * FROM notifications WHERE user_id = ?"
            params: list = [user_id]
            if unread_only:
                sql += " AND is_read = 0"
            sql += " ORDER BY created_at DESC"

            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()

        total = len(rows)
        start = (page - 1) * page_size
        end = start + page_size
        items = [self._row_to_dto(r) for r in rows[start:end]]

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_next=end < total,
            has_prev=page > 1,
        )

    async def create_notification(
        self,
        data: NotificationCreateDTO,
    ) -> NotificationDTO:
        notif_id = str(uuid.uuid4())
        now = _utc_iso()

        extra_data = {}
        if data.reference_id:
            extra_data["reference_id"] = data.reference_id
        if data.reference_type:
            extra_data["reference_type"] = data.reference_type
        if data.actor_id:
            extra_data["actor_id"] = data.actor_id

        with get_offline_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO notifications (id, user_id, title, message, type, is_read, data, created_at)
                VALUES (?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    notif_id,
                    data.user_id,
                    data.title,
                    data.message,
                    data.notification_type.value if hasattr(data.notification_type, "value") else data.notification_type,
                    json.dumps(extra_data),
                    now,
                ),
            )

        return NotificationDTO(
            id=notif_id,
            user_id=data.user_id,
            notification_type=data.notification_type,
            title=data.title,
            message=data.message,
            reference_id=data.reference_id,
            reference_type=data.reference_type,
            actor_id=data.actor_id,
            is_read=False,
            created_at=_utc_now(),
        )

    async def mark_as_read(
        self,
        user_id: str,
        notification_id: str,
    ) -> bool:
        with get_offline_cursor() as cursor:
            cursor.execute(
                "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
                (notification_id, user_id),
            )
            return cursor.rowcount > 0

    async def mark_all_as_read(self, user_id: str) -> int:
        with get_offline_cursor() as cursor:
            cursor.execute(
                "UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0",
                (user_id,),
            )
            return cursor.rowcount

    async def delete_notification(
        self,
        user_id: str,
        notification_id: str,
    ) -> bool:
        with get_offline_cursor() as cursor:
            cursor.execute(
                "DELETE FROM notifications WHERE id = ? AND user_id = ?",
                (notification_id, user_id),
            )
            return cursor.rowcount > 0

    async def get_unread_count(self, user_id: str) -> int:
        with get_offline_cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) as cnt FROM notifications WHERE user_id = ? AND is_read = 0",
                (user_id,),
            )
            row = cursor.fetchone()
            return row["cnt"] if row else 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_dto(row: dict) -> NotificationDTO:
        extra = json.loads(row.get("data") or "{}")
        return NotificationDTO(
            id=row["id"],
            user_id=row["user_id"],
            notification_type=row.get("type", "system"),
            title=row.get("title", ""),
            message=row.get("message", ""),
            reference_id=extra.get("reference_id"),
            reference_type=extra.get("reference_type"),
            actor_id=extra.get("actor_id"),
            actor_name=extra.get("actor_name"),
            actor_avatar=extra.get("actor_avatar"),
            is_read=bool(row.get("is_read", 0)),
            read_at=None,
            created_at=_parse_dt(row.get("created_at")) or _utc_now(),
        )
