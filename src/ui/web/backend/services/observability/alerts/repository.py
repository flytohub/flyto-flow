"""
Alert Repository

Single responsibility: Store alert rules and alert history.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from gateway.storage.database import get_cursor

from services.observability.alerts.rule import AlertRule, AlertSeverity, AlertState

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    """An alert instance that has fired."""

    id: str
    rule_id: str
    status: str  # firing, resolved
    severity: AlertSeverity
    started_at: str
    ended_at: Optional[str] = None
    silenced_until: Optional[str] = None
    labels: Dict[str, str] = None
    annotations: Dict[str, str] = None
    evaluated_value: Optional[float] = None
    threshold_value: Optional[float] = None

    def __post_init__(self):
        """Default labels and annotations to empty dicts if None."""
        if self.labels is None:
            self.labels = {}
        if self.annotations is None:
            self.annotations = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "status": self.status,
            "severity": self.severity.value if isinstance(self.severity, AlertSeverity) else self.severity,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "silenced_until": self.silenced_until,
            "labels": self.labels,
            "annotations": self.annotations,
            "evaluated_value": self.evaluated_value,
            "threshold_value": self.threshold_value,
        }


class AlertRuleRepository:
    """
    SQLite-based alert rule storage.

    Provides CRUD operations for alert rules.
    """

    _TABLE_NAME = "alert_rules"
    _initialized = False

    @classmethod
    def _ensure_table(cls) -> None:
        """Ensure alert_rules table exists."""
        if cls._initialized:
            return

        with get_cursor() as cursor:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {cls._TABLE_NAME} (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    condition TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    duration_seconds INTEGER DEFAULT 0,
                    labels TEXT,
                    annotations TEXT,
                    enabled INTEGER DEFAULT 1,
                    user_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT
                )
            """)
            # Add user_id column to existing tables
            try:
                cursor.execute(f"ALTER TABLE {cls._TABLE_NAME} ADD COLUMN user_id TEXT")
            except Exception:
                pass  # Column already exists
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_alert_rules_user_id
                ON {cls._TABLE_NAME}(user_id)
            """)

        cls._initialized = True

    @classmethod
    def create(cls, rule: AlertRule, user_id: str = None) -> str:
        """
        Create a new alert rule.

        Args:
            rule: Alert rule to create
            user_id: Owner user ID

        Returns:
            Rule ID
        """
        cls._ensure_table()

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {cls._TABLE_NAME}
                (id, name, condition, severity, duration_seconds, labels,
                 annotations, enabled, user_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rule.id,
                    rule.name,
                    rule.condition,
                    rule.severity.value,
                    rule.duration_seconds,
                    json.dumps(rule.labels),
                    json.dumps(rule.annotations),
                    1 if rule.enabled else 0,
                    user_id,
                    rule.created_at,
                ),
            )

        return rule.id

    @classmethod
    def get(cls, rule_id: str, user_id: str = None) -> Optional[AlertRule]:
        """Get an alert rule by ID, optionally filtered by user."""
        cls._ensure_table()

        conditions = ["id = ?"]
        params = [rule_id]

        if user_id:
            conditions.append("(user_id = ? OR user_id IS NULL)")
            params.append(user_id)

        where_clause = " AND ".join(conditions)

        with get_cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM {cls._TABLE_NAME} WHERE {where_clause}",
                params,
            )
            row = cursor.fetchone()

        if not row:
            return None

        return cls._row_to_rule(dict(row))

    @classmethod
    def list_all(cls, enabled_only: bool = False, user_id: str = None) -> List[AlertRule]:
        """
        List all alert rules.

        Args:
            enabled_only: Only return enabled rules
            user_id: Filter by owner user ID

        Returns:
            List of alert rules
        """
        cls._ensure_table()

        conditions = []
        params = []

        if user_id:
            conditions.append("(user_id = ? OR user_id IS NULL)")
            params.append(user_id)

        if enabled_only:
            conditions.append("enabled = 1")

        query = f"SELECT * FROM {cls._TABLE_NAME}"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_at DESC"

        with get_cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [cls._row_to_rule(dict(row)) for row in rows]

    @classmethod
    def update(cls, rule_id: str, **kwargs) -> bool:
        """
        Update an alert rule.

        Args:
            rule_id: Rule ID
            **kwargs: Fields to update

        Returns:
            True if updated
        """
        cls._ensure_table()

        allowed_fields = {
            "name", "condition", "severity", "duration_seconds",
            "labels", "annotations", "enabled"
        }

        updates = []
        params = []

        for key, value in kwargs.items():
            if key not in allowed_fields:
                continue

            if key == "severity" and isinstance(value, AlertSeverity):
                value = value.value
            elif key in ("labels", "annotations") and isinstance(value, dict):
                value = json.dumps(value)
            elif key == "enabled":
                value = 1 if value else 0

            updates.append(f"{key} = ?")
            params.append(value)

        if not updates:
            return False

        updates.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())
        params.append(rule_id)

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE {cls._TABLE_NAME}
                SET {", ".join(updates)}
                WHERE id = ?
                """,
                params,
            )
            return cursor.rowcount > 0

    @classmethod
    def delete(cls, rule_id: str, user_id: str = None) -> bool:
        """Delete an alert rule."""
        cls._ensure_table()

        conditions = ["id = ?"]
        params = [rule_id]

        if user_id:
            conditions.append("(user_id = ? OR user_id IS NULL)")
            params.append(user_id)

        where_clause = " AND ".join(conditions)

        with get_cursor() as cursor:
            cursor.execute(
                f"DELETE FROM {cls._TABLE_NAME} WHERE {where_clause}",
                params,
            )
            return cursor.rowcount > 0

    @classmethod
    def _row_to_rule(cls, row: dict) -> AlertRule:
        """Convert database row to AlertRule."""
        labels = {}
        annotations = {}

        if row.get("labels"):
            try:
                labels = json.loads(row["labels"])
            except Exception:
                pass

        if row.get("annotations"):
            try:
                annotations = json.loads(row["annotations"])
            except Exception:
                pass

        return AlertRule(
            id=row["id"],
            name=row["name"],
            condition=row["condition"],
            severity=AlertSeverity(row["severity"]),
            duration_seconds=row.get("duration_seconds", 0),
            labels=labels,
            annotations=annotations,
            enabled=bool(row.get("enabled", 1)),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


class AlertRepository:
    """
    SQLite-based alert history storage.

    Stores fired alerts and their history.
    """

    _TABLE_NAME = "alerts"
    _initialized = False

    @classmethod
    def _ensure_table(cls) -> None:
        """Ensure alerts table exists."""
        if cls._initialized:
            return

        with get_cursor() as cursor:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {cls._TABLE_NAME} (
                    id TEXT PRIMARY KEY,
                    rule_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    silenced_until TEXT,
                    labels TEXT,
                    annotations TEXT,
                    evaluated_value REAL,
                    threshold_value REAL,
                    user_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Add user_id column to existing tables
            try:
                cursor.execute(f"ALTER TABLE {cls._TABLE_NAME} ADD COLUMN user_id TEXT")
            except Exception:
                pass  # Column already exists
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_alerts_rule_id
                ON {cls._TABLE_NAME}(rule_id)
            """)
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_alerts_status
                ON {cls._TABLE_NAME}(status)
            """)
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_alerts_user_id
                ON {cls._TABLE_NAME}(user_id)
            """)

        cls._initialized = True

    @classmethod
    def create(cls, alert: Alert) -> str:
        """Create a new alert."""
        cls._ensure_table()

        severity = alert.severity
        if isinstance(severity, AlertSeverity):
            severity = severity.value

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {cls._TABLE_NAME}
                (id, rule_id, status, severity, started_at, ended_at,
                 silenced_until, labels, annotations, evaluated_value,
                 threshold_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert.id,
                    alert.rule_id,
                    alert.status,
                    severity,
                    alert.started_at,
                    alert.ended_at,
                    alert.silenced_until,
                    json.dumps(alert.labels),
                    json.dumps(alert.annotations),
                    alert.evaluated_value,
                    alert.threshold_value,
                ),
            )

        return alert.id

    @classmethod
    def get(cls, alert_id: str) -> Optional[Alert]:
        """Get an alert by ID."""
        cls._ensure_table()

        with get_cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM {cls._TABLE_NAME} WHERE id = ?",
                (alert_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return cls._row_to_alert(dict(row))

    @classmethod
    def get_active(cls, user_id: str = None) -> List[Alert]:
        """Get all active (firing) alerts."""
        cls._ensure_table()

        conditions = ["status = 'firing'"]
        params = []

        if user_id:
            conditions.append("(user_id = ? OR user_id IS NULL)")
            params.append(user_id)

        where_clause = " AND ".join(conditions)

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM {cls._TABLE_NAME}
                WHERE {where_clause}
                ORDER BY started_at DESC
                """,
                params,
            )
            rows = cursor.fetchall()

        return [cls._row_to_alert(dict(row)) for row in rows]

    @classmethod
    def get_by_rule(cls, rule_id: str, limit: int = 100, user_id: str = None) -> List[Alert]:
        """Get alerts for a specific rule."""
        cls._ensure_table()

        conditions = ["rule_id = ?"]
        params = [rule_id]

        if user_id:
            conditions.append("(user_id = ? OR user_id IS NULL)")
            params.append(user_id)

        where_clause = " AND ".join(conditions)

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM {cls._TABLE_NAME}
                WHERE {where_clause}
                ORDER BY started_at DESC
                LIMIT ?
                """,
                (*params, limit),
            )
            rows = cursor.fetchall()

        return [cls._row_to_alert(dict(row)) for row in rows]

    @classmethod
    def update(cls, alert_id: str, **kwargs) -> bool:
        """Update an alert."""
        cls._ensure_table()

        allowed_fields = {"status", "ended_at", "silenced_until"}

        updates = []
        params = []

        for key, value in kwargs.items():
            if key not in allowed_fields:
                continue
            updates.append(f"{key} = ?")
            params.append(value)

        if not updates:
            return False

        params.append(alert_id)

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE {cls._TABLE_NAME}
                SET {", ".join(updates)}
                WHERE id = ?
                """,
                params,
            )
            return cursor.rowcount > 0

    @classmethod
    def resolve(cls, alert_id: str) -> bool:
        """Resolve an alert."""
        return cls.update(
            alert_id,
            status="resolved",
            ended_at=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def silence(cls, alert_id: str, until: str) -> bool:
        """Silence an alert until specified time."""
        return cls.update(alert_id, silenced_until=until)

    @classmethod
    def update_status(cls, alert_id: str, status: str) -> bool:
        """Update alert status."""
        return cls.update(alert_id, status=status)

    @classmethod
    def _row_to_alert(cls, row: dict) -> Alert:
        """Convert database row to Alert."""
        labels = {}
        annotations = {}

        if row.get("labels"):
            try:
                labels = json.loads(row["labels"])
            except Exception:
                pass

        if row.get("annotations"):
            try:
                annotations = json.loads(row["annotations"])
            except Exception:
                pass

        return Alert(
            id=row["id"],
            rule_id=row["rule_id"],
            status=row["status"],
            severity=AlertSeverity(row["severity"]),
            started_at=row["started_at"],
            ended_at=row.get("ended_at"),
            silenced_until=row.get("silenced_until"),
            labels=labels,
            annotations=annotations,
            evaluated_value=row.get("evaluated_value"),
            threshold_value=row.get("threshold_value"),
        )
