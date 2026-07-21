"""
Webhook Repository

Database persistence for webhooks.
"""

import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from services.webhook.models import Webhook, WebhookStatus

logger = logging.getLogger(__name__)


class WebhookRepository:
    """Repository for webhook persistence."""

    _TABLE_NAME = "webhooks"

    @classmethod
    def _ensure_table(cls) -> None:
        """Ensure webhooks table exists."""
        from gateway.storage.database import DatabaseManager

        DatabaseManager.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {cls._TABLE_NAME} (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                workflow_id TEXT NOT NULL,
                secret TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                inputs_mapping TEXT,
                require_signature INTEGER DEFAULT 1,
                allowed_ips TEXT,
                timestamp_tolerance_seconds INTEGER DEFAULT 300,
                user_id TEXT,
                organization_id TEXT,
                project_id TEXT,
                workspace_id TEXT,
                provider TEXT,
                trigger_count INTEGER DEFAULT 0,
                last_triggered_at TEXT,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Add new columns if they don't exist (migration for existing tables)
        try:
            DatabaseManager.execute(
                f"ALTER TABLE {cls._TABLE_NAME} ADD COLUMN workspace_id TEXT"
            )
        except Exception:
            pass  # Column already exists

        try:
            DatabaseManager.execute(
                f"ALTER TABLE {cls._TABLE_NAME} ADD COLUMN provider TEXT"
            )
        except Exception:
            pass  # Column already exists

        # Add workflow_name column if it doesn't exist (migration)
        try:
            DatabaseManager.execute(
                f"ALTER TABLE {cls._TABLE_NAME} ADD COLUMN workflow_name TEXT DEFAULT ''"
            )
        except Exception:
            pass  # Column already exists

    @classmethod
    def create(cls, webhook: Webhook) -> Webhook:
        """Create a new webhook."""
        from gateway.storage.database import DatabaseManager

        cls._ensure_table()

        if not webhook.id:
            webhook.id = str(uuid4())

        if not webhook.secret:
            webhook.secret = secrets.token_urlsafe(32)

        DatabaseManager.execute(
            f"""
            INSERT INTO {cls._TABLE_NAME}
            (id, name, workflow_id, workflow_name, secret, status, inputs_mapping,
             require_signature, allowed_ips, timestamp_tolerance_seconds,
             user_id, organization_id, project_id, workspace_id, provider,
             description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                webhook.id,
                webhook.name,
                webhook.workflow_id,
                webhook.workflow_name,
                webhook.secret,
                webhook.status.value,
                json.dumps(webhook.inputs_mapping),
                1 if webhook.require_signature else 0,
                json.dumps(webhook.allowed_ips),
                webhook.timestamp_tolerance_seconds,
                webhook.user_id,
                webhook.organization_id,
                webhook.project_id,
                webhook.workspace_id,
                webhook.provider,
                webhook.description,
                webhook.created_at,
                webhook.updated_at,
            ),
        )

        logger.info(f"Created webhook: {webhook.name} (id={webhook.id})")

        return webhook

    @classmethod
    def get(cls, webhook_id: str) -> Optional[Webhook]:
        """Get webhook by ID."""
        from gateway.storage.database import DatabaseManager

        cls._ensure_table()

        row = DatabaseManager.fetchone(
            f"SELECT * FROM {cls._TABLE_NAME} WHERE id = ?",
            (webhook_id,),
        )

        if not row:
            return None

        return cls._row_to_webhook(row)

    @classmethod
    def list_webhooks(
        cls,
        workflow_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[Webhook]:
        """List webhooks with filters."""
        from gateway.storage.database import DatabaseManager

        cls._ensure_table()

        conditions = []
        params = []

        if workflow_id:
            conditions.append("workflow_id = ?")
            params.append(workflow_id)

        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        rows = DatabaseManager.fetchall(
            f"SELECT * FROM {cls._TABLE_NAME} WHERE {where_clause} ORDER BY name",
            tuple(params),
        )

        return [cls._row_to_webhook(row) for row in rows]

    @classmethod
    def update(cls, webhook_id: str, **kwargs) -> bool:
        """Update webhook fields."""
        from gateway.storage.database import DatabaseManager

        cls._ensure_table()

        allowed_fields = {
            "name", "status", "inputs_mapping", "require_signature",
            "allowed_ips", "timestamp_tolerance_seconds", "description",
            "trigger_count", "last_triggered_at"
        }

        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return False

        # Handle conversions
        if "status" in updates and isinstance(updates["status"], WebhookStatus):
            updates["status"] = updates["status"].value
        if "inputs_mapping" in updates and isinstance(updates["inputs_mapping"], dict):
            updates["inputs_mapping"] = json.dumps(updates["inputs_mapping"])
        if "allowed_ips" in updates and isinstance(updates["allowed_ips"], list):
            updates["allowed_ips"] = json.dumps(updates["allowed_ips"])
        if "require_signature" in updates:
            updates["require_signature"] = 1 if updates["require_signature"] else 0

        updates["updated_at"] = datetime.now(timezone.utc).isoformat()

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [webhook_id]

        result = DatabaseManager.execute(
            f"UPDATE {cls._TABLE_NAME} SET {set_clause} WHERE id = ?",
            tuple(values),
        )

        return result.rowcount > 0

    @classmethod
    def delete(cls, webhook_id: str) -> bool:
        """Delete a webhook."""
        from gateway.storage.database import DatabaseManager

        cls._ensure_table()

        result = DatabaseManager.execute(
            f"DELETE FROM {cls._TABLE_NAME} WHERE id = ?",
            (webhook_id,),
        )

        return result.rowcount > 0

    @classmethod
    def regenerate_secret(cls, webhook_id: str) -> Optional[str]:
        """Regenerate webhook secret."""
        from gateway.storage.database import DatabaseManager

        cls._ensure_table()

        new_secret = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc).isoformat()

        result = DatabaseManager.execute(
            f"UPDATE {cls._TABLE_NAME} SET secret = ?, updated_at = ? WHERE id = ?",
            (new_secret, now, webhook_id),
        )

        return new_secret if result.rowcount > 0 else None

    @classmethod
    def record_trigger(cls, webhook_id: str) -> None:
        """Record a webhook trigger."""
        from gateway.storage.database import DatabaseManager

        cls._ensure_table()

        now = datetime.now(timezone.utc).isoformat()

        DatabaseManager.execute(
            f"""
            UPDATE {cls._TABLE_NAME}
            SET trigger_count = trigger_count + 1, last_triggered_at = ?
            WHERE id = ?
            """,
            (now, webhook_id),
        )

    @classmethod
    def _row_to_webhook(cls, row: Dict[str, Any]) -> Webhook:
        """Convert database row to Webhook."""
        inputs_mapping = {}
        if row.get("inputs_mapping"):
            try:
                inputs_mapping = json.loads(row["inputs_mapping"])
            except json.JSONDecodeError:
                pass

        allowed_ips = []
        if row.get("allowed_ips"):
            try:
                allowed_ips = json.loads(row["allowed_ips"])
            except json.JSONDecodeError:
                pass

        return Webhook(
            id=row["id"],
            name=row["name"],
            workflow_id=row["workflow_id"],
            workflow_name=row.get("workflow_name") or "",
            secret=row["secret"],
            status=WebhookStatus(row.get("status", "active")),
            inputs_mapping=inputs_mapping,
            require_signature=bool(row.get("require_signature", 1)),
            allowed_ips=allowed_ips,
            timestamp_tolerance_seconds=row.get("timestamp_tolerance_seconds", 300),
            user_id=row.get("user_id"),
            organization_id=row.get("organization_id"),
            project_id=row.get("project_id"),
            workspace_id=row.get("workspace_id"),
            provider=row.get("provider"),
            trigger_count=row.get("trigger_count", 0),
            last_triggered_at=row.get("last_triggered_at"),
            description=row.get("description"),
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", ""),
        )
