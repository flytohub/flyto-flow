"""
Scheduler Repository

Database persistence for schedules.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from services.infra.scheduler.models import Schedule, ScheduleStatus
from services.infra.scheduler.cron_parser import CronParser

logger = logging.getLogger(__name__)


class SchedulerRepository:
    """Repository for schedule persistence."""

    _TABLE_NAME = "schedules"

    @classmethod
    def _ensure_table(cls) -> None:
        """Ensure schedules table exists."""
        from gateway.storage.database import DatabaseManager

        DatabaseManager.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {cls._TABLE_NAME} (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                workflow_id TEXT NOT NULL,
                cron_expression TEXT,
                interval_seconds INTEGER,
                timezone TEXT DEFAULT 'UTC',
                status TEXT DEFAULT 'active',
                inputs TEXT,
                max_concurrent INTEGER DEFAULT 1,
                timeout_ms INTEGER DEFAULT 300000,
                retry_on_failure INTEGER DEFAULT 0,
                user_id TEXT,
                organization_id TEXT,
                project_id TEXT,
                workspace_id TEXT,
                last_run_at TEXT,
                next_run_at TEXT,
                run_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        DatabaseManager.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_schedules_next_run
            ON {cls._TABLE_NAME}(status, next_run_at)
            """
        )

        # Add workspace_id column if it doesn't exist (migration)
        try:
            DatabaseManager.execute(
                f"ALTER TABLE {cls._TABLE_NAME} ADD COLUMN workspace_id TEXT"
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

        # Add polling columns (migration)
        for col, col_type in [
            ("poll_url", "TEXT"),
            ("poll_config", "TEXT"),
            ("last_poll_hash", "TEXT"),
            ("last_poll_data", "TEXT"),
        ]:
            try:
                DatabaseManager.execute(
                    f"ALTER TABLE {cls._TABLE_NAME} ADD COLUMN {col} {col_type}"
                )
            except Exception:
                pass  # Column already exists

    @classmethod
    def create(cls, schedule: Schedule) -> Schedule:
        """Create a new schedule."""
        from gateway.storage.database import DatabaseManager

        cls._ensure_table()

        if not schedule.id:
            schedule.id = str(uuid4())

        # Calculate next run
        if schedule.cron_expression:
            next_run = CronParser.get_next_run(
                schedule.cron_expression,
                timezone_str=schedule.timezone,
            )
            schedule.next_run_at = next_run.isoformat()
        elif schedule.interval_seconds:
            next_run = datetime.now(timezone.utc) + timedelta(
                seconds=schedule.interval_seconds
            )
            schedule.next_run_at = next_run.isoformat()

        DatabaseManager.execute(
            f"""
            INSERT INTO {cls._TABLE_NAME}
            (id, name, workflow_id, workflow_name, cron_expression, interval_seconds,
             timezone, status, inputs, max_concurrent, timeout_ms, retry_on_failure,
             user_id, organization_id, project_id, workspace_id, next_run_at,
             poll_url, poll_config, last_poll_hash, last_poll_data,
             description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                schedule.id,
                schedule.name,
                schedule.workflow_id,
                schedule.workflow_name,
                schedule.cron_expression,
                schedule.interval_seconds,
                schedule.timezone,
                schedule.status.value,
                json.dumps(schedule.inputs),
                schedule.max_concurrent,
                schedule.timeout_ms,
                1 if schedule.retry_on_failure else 0,
                schedule.user_id,
                schedule.organization_id,
                schedule.project_id,
                schedule.workspace_id,
                schedule.next_run_at,
                schedule.poll_url,
                schedule.poll_config,
                schedule.last_poll_hash,
                schedule.last_poll_data,
                schedule.description,
                schedule.created_at,
                schedule.updated_at,
            ),
        )

        logger.info(f"Created schedule: {schedule.name} (id={schedule.id})")

        return schedule

    @classmethod
    def get(cls, schedule_id: str) -> Optional[Schedule]:
        """Get schedule by ID."""
        from gateway.storage.database import DatabaseManager

        cls._ensure_table()

        row = DatabaseManager.fetchone(
            f"SELECT * FROM {cls._TABLE_NAME} WHERE id = ?",
            (schedule_id,),
        )

        if not row:
            return None

        return cls._row_to_schedule(row)

    @classmethod
    def list_schedules(
        cls,
        workflow_id: Optional[str] = None,
        status: Optional[ScheduleStatus] = None,
        user_id: Optional[str] = None,
    ) -> List[Schedule]:
        """List schedules with filters."""
        from gateway.storage.database import DatabaseManager

        cls._ensure_table()

        conditions = []
        params = []

        if workflow_id:
            conditions.append("workflow_id = ?")
            params.append(workflow_id)

        if status:
            conditions.append("status = ?")
            params.append(status.value)

        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        rows = DatabaseManager.fetchall(
            f"SELECT * FROM {cls._TABLE_NAME} WHERE {where_clause} ORDER BY name",
            tuple(params),
        )

        return [cls._row_to_schedule(row) for row in rows]

    @classmethod
    def get_due_schedules(cls) -> List[Schedule]:
        """Get schedules that are due to run."""
        from gateway.storage.database import DatabaseManager

        cls._ensure_table()

        now = datetime.now(timezone.utc).isoformat()

        rows = DatabaseManager.fetchall(
            f"""
            SELECT * FROM {cls._TABLE_NAME}
            WHERE status = 'active' AND next_run_at <= ?
            ORDER BY next_run_at
            """,
            (now,),
        )

        return [cls._row_to_schedule(row) for row in rows]

    @classmethod
    def update(cls, schedule_id: str, **kwargs) -> bool:
        """Update schedule fields."""
        from gateway.storage.database import DatabaseManager

        cls._ensure_table()

        allowed_fields = {
            "name", "cron_expression", "interval_seconds", "timezone",
            "status", "inputs", "max_concurrent", "timeout_ms",
            "retry_on_failure", "next_run_at", "last_run_at",
            "run_count", "failure_count", "description",
            "poll_url", "poll_config", "last_poll_hash", "last_poll_data",
        }

        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return False

        # Handle special conversions
        if "status" in updates and isinstance(updates["status"], ScheduleStatus):
            updates["status"] = updates["status"].value
        if "inputs" in updates and isinstance(updates["inputs"], dict):
            updates["inputs"] = json.dumps(updates["inputs"])
        if "retry_on_failure" in updates:
            updates["retry_on_failure"] = 1 if updates["retry_on_failure"] else 0

        updates["updated_at"] = datetime.now(timezone.utc).isoformat()

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [schedule_id]

        result = DatabaseManager.execute(
            f"UPDATE {cls._TABLE_NAME} SET {set_clause} WHERE id = ?",
            tuple(values),
        )

        return result.rowcount > 0

    @classmethod
    def delete(cls, schedule_id: str) -> bool:
        """Delete a schedule."""
        from gateway.storage.database import DatabaseManager

        cls._ensure_table()

        result = DatabaseManager.execute(
            f"DELETE FROM {cls._TABLE_NAME} WHERE id = ?",
            (schedule_id,),
        )

        return result.rowcount > 0

    @classmethod
    def record_run(
        cls,
        schedule_id: str,
        success: bool,
        next_run_at: Optional[str] = None,
    ) -> None:
        """Record a schedule run."""
        from gateway.storage.database import DatabaseManager

        cls._ensure_table()

        now = datetime.now(timezone.utc).isoformat()

        if success:
            DatabaseManager.execute(
                f"""
                UPDATE {cls._TABLE_NAME}
                SET last_run_at = ?, next_run_at = ?, run_count = run_count + 1,
                    updated_at = ?
                WHERE id = ?
                """,
                (now, next_run_at, now, schedule_id),
            )
        else:
            DatabaseManager.execute(
                f"""
                UPDATE {cls._TABLE_NAME}
                SET last_run_at = ?, next_run_at = ?, failure_count = failure_count + 1,
                    updated_at = ?
                WHERE id = ?
                """,
                (now, next_run_at, now, schedule_id),
            )

    @classmethod
    def _row_to_schedule(cls, row: Dict[str, Any]) -> Schedule:
        """Convert database row to Schedule."""
        inputs = {}
        if row.get("inputs"):
            try:
                inputs = json.loads(row["inputs"])
            except json.JSONDecodeError:
                pass

        return Schedule(
            id=row["id"],
            name=row["name"],
            workflow_id=row["workflow_id"],
            workflow_name=row.get("workflow_name") or "",
            cron_expression=row.get("cron_expression"),
            interval_seconds=row.get("interval_seconds"),
            timezone=row.get("timezone", "UTC"),
            status=ScheduleStatus(row.get("status", "active")),
            inputs=inputs,
            max_concurrent=row.get("max_concurrent", 1),
            timeout_ms=row.get("timeout_ms", 300000),
            retry_on_failure=bool(row.get("retry_on_failure", 0)),
            user_id=row.get("user_id"),
            organization_id=row.get("organization_id"),
            project_id=row.get("project_id"),
            workspace_id=row.get("workspace_id"),
            poll_url=row.get("poll_url"),
            poll_config=row.get("poll_config"),
            last_poll_hash=row.get("last_poll_hash"),
            last_poll_data=row.get("last_poll_data"),
            last_run_at=row.get("last_run_at"),
            next_run_at=row.get("next_run_at"),
            run_count=row.get("run_count", 0),
            failure_count=row.get("failure_count", 0),
            description=row.get("description"),
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", ""),
        )
