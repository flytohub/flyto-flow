"""
Write operations for execution records — create, update, delete.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from gateway.storage.database import get_cursor
from gateway.storage.models import Execution, ExecutionStep

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    """Get current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).isoformat()


class ExecutionWriteMixin:
    """Mixin for execution write operations."""

    @staticmethod
    def create_execution(
        workflow_id: str,
        workflow_name: str = "",
        workflow_version: str = "1.0.0",
        workspace_id: str = None,
        input_params: Dict[str, Any] = None,
        workflow_snapshot: Dict[str, Any] = None,
        modules_snapshot: List[Dict[str, Any]] = None,
        env_snapshot: Dict[str, Any] = None,
    ) -> Execution:
        """
        Create a new execution record.

        Args:
            workflow_id: Workflow identifier
            workflow_name: Display name
            workflow_version: Workflow version
            workspace_id: Workspace identifier
            input_params: Runtime parameters
            workflow_snapshot: Full workflow definition snapshot
            modules_snapshot: Module versions snapshot
            env_snapshot: Environment snapshot

        Returns:
            Execution object with generated ID
        """
        exec_id = str(uuid.uuid4())
        now = _utc_now()

        with get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO executions (
                    id, workflow_id, workflow_name, workflow_version,
                    workspace_id, status, started_at, input_params,
                    workflow_snapshot, modules_snapshot, env_snapshot
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    exec_id,
                    workflow_id,
                    workflow_name,
                    workflow_version,
                    workspace_id,
                    "pending",
                    now,
                    json.dumps(input_params or {}),
                    json.dumps(workflow_snapshot) if workflow_snapshot else None,
                    json.dumps(modules_snapshot) if modules_snapshot else None,
                    json.dumps(env_snapshot) if env_snapshot else None,
                ),
            )

        logger.info(f"Created execution: {exec_id} for workflow {workflow_id}")

        return Execution(
            id=exec_id,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            workflow_version=workflow_version,
            workspace_id=workspace_id,
            status="pending",
            started_at=now,
            input_params=input_params or {},
            workflow_snapshot=workflow_snapshot,
            modules_snapshot=modules_snapshot,
            env_snapshot=env_snapshot,
        )

    @staticmethod
    def update_execution(
        execution_id: str,
        status: str = None,
        finished_at: str = None,
        duration_ms: int = None,
        result_data: Any = None,
        error_message: str = None,
        error_step_id: str = None,
        outcome: str = None,
        outcome_reason: str = None,
        error_category: str = None,
        error_fingerprint: str = None,
    ) -> bool:
        """
        Update execution record.

        Args:
            execution_id: Execution identifier
            status: New status
            finished_at: Completion timestamp
            duration_ms: Execution duration
            result_data: Execution result
            error_message: Error message if failed
            error_step_id: Step that caused failure
            outcome: Outcome classification (success, failure, partial_success)
            outcome_reason: Human-readable outcome reason
            error_category: Error category from taxonomy
            error_fingerprint: Error fingerprint for deduplication

        Returns:
            True if updated, False if not found
        """
        updates = []
        params = []

        if status is not None:
            updates.append("status = ?")
            params.append(status)

        if finished_at is not None:
            updates.append("finished_at = ?")
            params.append(finished_at)

        if duration_ms is not None:
            updates.append("duration_ms = ?")
            params.append(duration_ms)

        if result_data is not None:
            updates.append("result_data = ?")
            params.append(json.dumps(result_data))

        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)

        if error_step_id is not None:
            updates.append("error_step_id = ?")
            params.append(error_step_id)

        if outcome is not None:
            updates.append("outcome = ?")
            params.append(outcome)

        if outcome_reason is not None:
            updates.append("outcome_reason = ?")
            params.append(outcome_reason)

        if error_category is not None:
            updates.append("error_category = ?")
            params.append(error_category)

        if error_fingerprint is not None:
            updates.append("error_fingerprint = ?")
            params.append(error_fingerprint)

        if not updates:
            return True

        params.append(execution_id)

        with get_cursor() as cursor:
            cursor.execute(
                f"UPDATE executions SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            return cursor.rowcount > 0

    @staticmethod
    def delete_execution(execution_id: str) -> bool:
        """Delete execution and its steps."""
        with get_cursor() as cursor:
            cursor.execute("DELETE FROM executions WHERE id = ?", (execution_id,))
            deleted = cursor.rowcount > 0

        if deleted:
            logger.info(f"Deleted execution: {execution_id}")

        return deleted

    @staticmethod
    def delete_old_executions(days: int = 30) -> int:
        """
        Delete executions older than specified days.

        Returns:
            Number of deleted records
        """
        from datetime import timedelta

        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        with get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM executions WHERE started_at < ?",
                (cutoff,),
            )
            count = cursor.rowcount

        if count:
            logger.info(f"Deleted {count} executions older than {days} days")

        return count

    # =========================================================================
    # Step CRUD
    # =========================================================================

    @staticmethod
    def add_step(
        execution_id: str,
        step_id: str,
        step_index: int = 0,
        module_id: str = "",
        status: str = "pending",
        input_params: Dict[str, Any] = None,
    ) -> ExecutionStep:
        """Add a step record to an execution."""
        with get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO execution_steps (
                    execution_id, step_id, step_index, module_id,
                    status, started_at, input_params
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    execution_id,
                    step_id,
                    step_index,
                    module_id,
                    status,
                    _utc_now() if status == "running" else None,
                    json.dumps(input_params or {}),
                ),
            )
            step_row_id = cursor.lastrowid

        return ExecutionStep(
            id=step_row_id,
            execution_id=execution_id,
            step_id=step_id,
            step_index=step_index,
            module_id=module_id,
            status=status,
            input_params=input_params or {},
        )

    @staticmethod
    def update_step(
        execution_id: str,
        step_id: str,
        status: str = None,
        finished_at: str = None,
        duration_ms: int = None,
        output_data: Any = None,
        error_message: str = None,
    ) -> bool:
        """Update a step record."""
        updates = []
        params = []

        if status is not None:
            updates.append("status = ?")
            params.append(status)

            if status == "running":
                updates.append("started_at = ?")
                params.append(_utc_now())

        if finished_at is not None:
            updates.append("finished_at = ?")
            params.append(finished_at)

        if duration_ms is not None:
            updates.append("duration_ms = ?")
            params.append(duration_ms)

        if output_data is not None:
            updates.append("output_data = ?")
            params.append(json.dumps(output_data))

        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)

        if not updates:
            return True

        params.extend([execution_id, step_id])

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE execution_steps
                SET {', '.join(updates)}
                WHERE execution_id = ? AND step_id = ?
                """,
                params,
            )
            return cursor.rowcount > 0
