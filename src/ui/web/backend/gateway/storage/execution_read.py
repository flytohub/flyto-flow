"""
Read operations for execution records — get, list, search, statistics.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from gateway.storage.database import get_cursor
from gateway.storage.models import Execution, ExecutionStep

logger = logging.getLogger(__name__)


class ExecutionReadMixin:
    """Mixin for execution read operations."""

    @staticmethod
    def get_execution(execution_id: str, include_steps: bool = True) -> Optional[Execution]:
        """
        Get execution by ID.

        Args:
            execution_id: Execution UUID
            include_steps: Whether to load step records

        Returns:
            Execution object or None
        """
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM executions WHERE id = ?",
                (execution_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            execution = Execution.from_row(row)

            if include_steps:
                cursor.execute(
                    """
                    SELECT * FROM execution_steps
                    WHERE execution_id = ?
                    ORDER BY step_index
                    """,
                    (execution_id,),
                )
                execution.steps = [ExecutionStep.from_row(r) for r in cursor.fetchall()]

            return execution

    @staticmethod
    def list_executions(
        workflow_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        status: Optional[str] = None,
        statuses: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Execution]:
        """
        List executions with filters.

        Args:
            workflow_id: Filter by workflow ID
            workspace_id: Filter by workspace ID
            status: Filter by single status
            statuses: Filter by multiple statuses (e.g., ['failed', 'failure'])
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of Execution objects (without steps)
        """
        conditions = []
        params = []

        if workflow_id:
            conditions.append("workflow_id = ?")
            params.append(workflow_id)

        if workspace_id:
            conditions.append("workspace_id = ?")
            params.append(workspace_id)

        if statuses:
            placeholders = ",".join("?" * len(statuses))
            conditions.append(f"status IN ({placeholders})")
            params.extend(statuses)
        elif status:
            conditions.append("status = ?")
            params.append(status)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        params.extend([limit, offset])

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM executions
                {where_clause}
                ORDER BY started_at DESC
                LIMIT ? OFFSET ?
                """,
                params,
            )
            return [Execution.from_row(row) for row in cursor.fetchall()]

    @staticmethod
    def query_by_date_range(
        start_time: datetime,
        end_time: datetime = None,
        workflow_id: str = None,
        workspace_id: str = None,
    ) -> List[Execution]:
        """
        Query executions within a date range using SQL WHERE.

        This is much more efficient than loading all records and filtering in Python.

        Args:
            start_time: Start of time range (inclusive)
            end_time: End of time range (exclusive), defaults to now
            workflow_id: Optional workflow filter
            workspace_id: Optional workspace filter

        Returns:
            List of Execution objects (without steps)
        """
        if end_time is None:
            end_time = datetime.now(timezone.utc)

        # Convert to ISO strings for SQLite comparison
        start_str = start_time.isoformat() if start_time.tzinfo else start_time.replace(tzinfo=timezone.utc).isoformat()
        end_str = end_time.isoformat() if end_time.tzinfo else end_time.replace(tzinfo=timezone.utc).isoformat()

        conditions = ["started_at >= ?", "started_at < ?"]
        params = [start_str, end_str]

        if workflow_id:
            conditions.append("workflow_id = ?")
            params.append(workflow_id)

        if workspace_id:
            conditions.append("workspace_id = ?")
            params.append(workspace_id)

        where_clause = " AND ".join(conditions)

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM executions
                WHERE {where_clause}
                ORDER BY started_at DESC
                """,
                params,
            )
            return [Execution.from_row(row) for row in cursor.fetchall()]

    @staticmethod
    def get_execution_stats_by_date_range(
        start_time: datetime,
        end_time: datetime = None,
        workspace_id: str = None,
    ) -> Dict[str, Any]:
        """
        Get aggregated execution statistics for a date range using SQL.

        Much more efficient than loading all records and computing in Python.

        Args:
            start_time: Start of time range
            end_time: End of time range, defaults to now
            workspace_id: Filter by workspace ID

        Returns:
            Dictionary with total, successful, failed counts and avg duration
        """
        if end_time is None:
            end_time = datetime.now(timezone.utc)

        start_str = start_time.isoformat() if start_time.tzinfo else start_time.replace(tzinfo=timezone.utc).isoformat()
        end_str = end_time.isoformat() if end_time.tzinfo else end_time.replace(tzinfo=timezone.utc).isoformat()

        conditions = ["started_at >= ?", "started_at < ?"]
        params = [start_str, end_str]

        if workspace_id:
            conditions.append("workspace_id = ?")
            params.append(workspace_id)

        where_clause = " AND ".join(conditions)

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status IN ('completed', 'success') THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN status IN ('failed', 'failure') THEN 1 ELSE 0 END) as failed,
                    AVG(duration_ms) as avg_duration_ms
                FROM executions
                WHERE {where_clause}
                """,
                params,
            )
            row = cursor.fetchone()

            return {
                "total": row["total"] or 0,
                "successful": row["successful"] or 0,
                "failed": row["failed"] or 0,
                "avg_duration_ms": int(row["avg_duration_ms"]) if row["avg_duration_ms"] else 0,
            }

    @staticmethod
    def get_daily_stats(
        start_time: datetime,
        end_time: datetime = None,
        workspace_id: str = None,
    ) -> List[Dict[str, Any]]:
        """
        Get daily execution statistics using SQL GROUP BY.

        Args:
            start_time: Start of time range
            end_time: End of time range, defaults to now
            workspace_id: Filter by workspace ID

        Returns:
            List of daily stats with date, successful, failed counts
        """
        if end_time is None:
            end_time = datetime.now(timezone.utc)

        start_str = start_time.isoformat() if start_time.tzinfo else start_time.replace(tzinfo=timezone.utc).isoformat()
        end_str = end_time.isoformat() if end_time.tzinfo else end_time.replace(tzinfo=timezone.utc).isoformat()

        conditions = ["started_at >= ?", "started_at < ?"]
        params = [start_str, end_str]

        if workspace_id:
            conditions.append("workspace_id = ?")
            params.append(workspace_id)

        where_clause = " AND ".join(conditions)

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    DATE(started_at) as date,
                    SUM(CASE WHEN status IN ('completed', 'success') THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN status IN ('failed', 'failure') THEN 1 ELSE 0 END) as failed
                FROM executions
                WHERE {where_clause}
                GROUP BY DATE(started_at)
                ORDER BY date
                """,
                params,
            )
            return [
                {
                    "date": row["date"],
                    "successful": row["successful"] or 0,
                    "failed": row["failed"] or 0,
                }
                for row in cursor.fetchall()
            ]

    @staticmethod
    def get_top_workflows_stats(
        start_time: datetime,
        end_time: datetime = None,
        limit: int = 5,
        workspace_id: str = None,
    ) -> List[Dict[str, Any]]:
        """
        Get top workflows by execution count using SQL GROUP BY.

        Args:
            start_time: Start of time range
            end_time: End of time range, defaults to now
            limit: Number of top workflows to return
            workspace_id: Filter by workspace ID

        Returns:
            List of workflow stats with id, name, counts, and avg duration
        """
        if end_time is None:
            end_time = datetime.now(timezone.utc)

        start_str = start_time.isoformat() if start_time.tzinfo else start_time.replace(tzinfo=timezone.utc).isoformat()
        end_str = end_time.isoformat() if end_time.tzinfo else end_time.replace(tzinfo=timezone.utc).isoformat()

        conditions = ["started_at >= ?", "started_at < ?"]
        params = [start_str, end_str]

        if workspace_id:
            conditions.append("workspace_id = ?")
            params.append(workspace_id)

        where_clause = " AND ".join(conditions)

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    workflow_id,
                    workflow_name,
                    COUNT(*) as executions,
                    SUM(CASE WHEN status IN ('completed', 'success') THEN 1 ELSE 0 END) as successful,
                    AVG(duration_ms) as avg_duration_ms
                FROM executions
                WHERE {where_clause}
                GROUP BY workflow_id, workflow_name
                ORDER BY executions DESC
                LIMIT ?
                """,
                (*params, limit),
            )
            return [
                {
                    "id": row["workflow_id"] or "unknown",
                    "name": row["workflow_name"] or "Unknown Workflow",
                    "executions": row["executions"] or 0,
                    "successful": row["successful"] or 0,
                    "avg_duration_ms": int(row["avg_duration_ms"]) if row["avg_duration_ms"] else 0,
                }
                for row in cursor.fetchall()
            ]

    # =========================================================================
    # Statistics
    # =========================================================================

    @staticmethod
    def get_workflow_stats(workflow_id: str) -> Dict[str, Any]:
        """Get execution statistics for a workflow."""
        with get_cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status IN ('completed', 'success') THEN 1 ELSE 0 END) as success,
                    SUM(CASE WHEN status IN ('failed', 'failure') THEN 1 ELSE 0 END) as failure,
                    AVG(duration_ms) as avg_duration_ms,
                    MAX(started_at) as last_run
                FROM executions
                WHERE workflow_id = ?
                """,
                (workflow_id,),
            )
            row = cursor.fetchone()

            return {
                "total_executions": row["total"] or 0,
                "success_count": row["success"] or 0,
                "failure_count": row["failure"] or 0,
                "avg_duration_ms": int(row["avg_duration_ms"]) if row["avg_duration_ms"] else None,
                "last_run": row["last_run"],
            }

    @staticmethod
    def get_workspace_stats(workspace_id: str) -> Dict[str, Any]:
        """Get execution statistics for a user."""
        with get_cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status IN ('completed', 'success') THEN 1 ELSE 0 END) as success,
                    SUM(CASE WHEN status IN ('failed', 'failure') THEN 1 ELSE 0 END) as failure,
                    COUNT(DISTINCT workflow_id) as workflow_count
                FROM executions
                WHERE workspace_id = ?
                """,
                (workspace_id,),
            )
            row = cursor.fetchone()

            return {
                "total_executions": row["total"] or 0,
                "success_count": row["success"] or 0,
                "failure_count": row["failure"] or 0,
                "workflow_count": row["workflow_count"] or 0,
            }
