"""
Offline Audit Log Provider

SQLite-backed audit log operations for offline/desktop mode.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from gateway.providers.data.base import AuditLogProvider
from gateway.providers.data.models import (
    AuditLogDTO,
    AuditLogCreateDTO,
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


class OfflineAuditLogProvider(AuditLogProvider):
    """Offline implementation — SQLite-backed audit logs."""

    async def create_log(self, data: AuditLogCreateDTO) -> AuditLogDTO:
        log_id = str(uuid.uuid4())
        now = _utc_iso()

        details = dict(data.metadata) if data.metadata else {}
        if data.actor_email:
            details["actor_email"] = data.actor_email
        if data.actor_role:
            details["actor_role"] = data.actor_role
        if data.user_agent:
            details["user_agent"] = data.user_agent

        action_val = data.action.value if hasattr(data.action, "value") else data.action

        with get_offline_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO audit_logs (id, actor_id, action, resource_type, resource_id, details, ip_address, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log_id,
                    data.actor_id,
                    action_val,
                    data.resource_type,
                    data.resource_id,
                    json.dumps(details),
                    data.ip_address,
                    now,
                ),
            )

        return AuditLogDTO(
            id=log_id,
            actor_id=data.actor_id,
            actor_email=data.actor_email,
            actor_role=data.actor_role,
            action=data.action,
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            description=data.description,
            metadata=data.metadata or {},
            ip_address=data.ip_address,
            user_agent=data.user_agent,
            created_at=_utc_now(),
        )

    async def list_logs(
        self,
        page: int = 1,
        page_size: int = 50,
        actor_id: str = None,
        action: str = None,
        resource_type: str = None,
        start_date: str = None,
        end_date: str = None,
    ) -> PaginatedResponse:
        sql = "SELECT * FROM audit_logs WHERE 1=1"
        params: list = []

        if actor_id:
            sql += " AND actor_id = ?"
            params.append(actor_id)
        if action:
            sql += " AND action = ?"
            params.append(action)
        if resource_type:
            sql += " AND resource_type = ?"
            params.append(resource_type)
        if start_date:
            sql += " AND created_at >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND created_at <= ?"
            params.append(end_date)

        sql += " ORDER BY created_at DESC"

        with get_offline_cursor() as cursor:
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

    async def get_log(self, log_id: str) -> Optional[AuditLogDTO]:
        with get_offline_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM audit_logs WHERE id = ?", (log_id,)
            )
            row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_dto(row)

    async def get_user_activity(
        self, user_id: str, limit: int = 50
    ) -> List[AuditLogDTO]:
        with get_offline_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM audit_logs WHERE actor_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            )
            rows = cursor.fetchall()

        return [self._row_to_dto(r) for r in rows]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_dto(row: dict) -> AuditLogDTO:
        details = json.loads(row.get("details") or "{}")
        return AuditLogDTO(
            id=row["id"],
            actor_id=row.get("actor_id", ""),
            actor_email=details.get("actor_email"),
            actor_role=details.get("actor_role"),
            action=row.get("action", "create"),
            resource_type=row.get("resource_type", ""),
            resource_id=row.get("resource_id"),
            description=details.get("description", row.get("result", "")),
            metadata={k: v for k, v in details.items() if k not in ("actor_email", "actor_role", "user_agent", "description")},
            ip_address=row.get("ip_address"),
            user_agent=details.get("user_agent"),
            created_at=_parse_dt(row.get("created_at")) or _utc_now(),
        )
