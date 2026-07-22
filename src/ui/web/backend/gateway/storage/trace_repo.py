"""
Trace Repository

Single responsibility: Store traces to SQLite.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from gateway.storage.database import get_cursor, get_db

logger = logging.getLogger(__name__)


@dataclass
class TraceSummary:
    """Summary of a trace."""

    trace_id: str
    root_operation: str
    service_name: str
    start_time: str
    end_time: Optional[str]
    duration_ms: Optional[int]
    span_count: int
    error_count: int
    status: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trace_id": self.trace_id,
            "root_operation": self.root_operation,
            "service_name": self.service_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "span_count": self.span_count,
            "error_count": self.error_count,
            "status": self.status,
        }


@dataclass
class TraceQuery:
    """Query parameters for traces."""

    service_name: Optional[str] = None
    operation_name: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    min_duration_ms: Optional[int] = None
    max_duration_ms: Optional[int] = None
    has_error: Optional[bool] = None
    workspace_id: Optional[str] = None
    limit: int = 100


class TraceRepository:
    """
    SQLite-based trace storage.

    Provides:
    - Span storage and retrieval
    - Trace queries with filtering
    - Trace summaries
    """

    _TABLE_NAME = "spans"
    _initialized = False

    @classmethod
    def _ensure_table(cls) -> None:
        """Ensure spans table exists."""
        if cls._initialized:
            return

        with get_cursor() as cursor:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {cls._TABLE_NAME} (
                    id TEXT PRIMARY KEY,
                    trace_id TEXT NOT NULL,
                    span_id TEXT NOT NULL,
                    parent_span_id TEXT,
                    operation_name TEXT NOT NULL,
                    service_name TEXT DEFAULT 'flyto',
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration_ms INTEGER,
                    status TEXT NOT NULL,
                    status_message TEXT,
                    attributes TEXT,
                    events TEXT,
                    workspace_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Add workspace_id column to existing tables
            try:
                cursor.execute(f"ALTER TABLE {cls._TABLE_NAME} ADD COLUMN workspace_id TEXT")
            except Exception:
                pass  # Column already exists
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_spans_trace_id
                ON {cls._TABLE_NAME}(trace_id)
            """)
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_spans_start_time
                ON {cls._TABLE_NAME}(start_time)
            """)
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_spans_operation
                ON {cls._TABLE_NAME}(operation_name)
            """)
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_spans_workspace_id
                ON {cls._TABLE_NAME}(workspace_id)
            """)

        cls._initialized = True

    @classmethod
    def save_span(cls, span_data: Dict[str, Any]) -> str:
        """
        Save a span to database.

        Args:
            span_data: Span data dictionary (may include workspace_id)

        Returns:
            Span ID
        """
        cls._ensure_table()

        span_id = span_data.get("span_id", "")

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                INSERT OR REPLACE INTO {cls._TABLE_NAME}
                (id, trace_id, span_id, parent_span_id, operation_name,
                 service_name, start_time, end_time, duration_ms, status,
                 status_message, attributes, events, workspace_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    span_id,
                    span_data.get("trace_id", ""),
                    span_id,
                    span_data.get("parent_span_id"),
                    span_data.get("operation_name", ""),
                    span_data.get("service_name", "flyto"),
                    span_data.get("start_time", ""),
                    span_data.get("end_time"),
                    span_data.get("duration_ms"),
                    span_data.get("status", "unset"),
                    span_data.get("status_message"),
                    json.dumps(span_data.get("attributes", {})),
                    json.dumps(span_data.get("events", [])),
                    span_data.get("workspace_id"),
                ),
            )

        return span_id

    @classmethod
    def save_spans(cls, spans: List[Dict[str, Any]]) -> int:
        """
        Save multiple spans.

        Args:
            spans: List of span data dictionaries (may include workspace_id)

        Returns:
            Number of spans saved
        """
        cls._ensure_table()

        records = []
        for span in spans:
            span_id = span.get("span_id", "")
            records.append((
                span_id,
                span.get("trace_id", ""),
                span_id,
                span.get("parent_span_id"),
                span.get("operation_name", ""),
                span.get("service_name", "flyto"),
                span.get("start_time", ""),
                span.get("end_time"),
                span.get("duration_ms"),
                span.get("status", "unset"),
                span.get("status_message"),
                json.dumps(span.get("attributes", {})),
                json.dumps(span.get("events", [])),
                span.get("workspace_id"),
            ))

        with get_cursor() as cursor:
            cursor.executemany(
                f"""
                INSERT OR REPLACE INTO {cls._TABLE_NAME}
                (id, trace_id, span_id, parent_span_id, operation_name,
                 service_name, start_time, end_time, duration_ms, status,
                 status_message, attributes, events, workspace_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                records,
            )

        return len(records)

    @classmethod
    def get_span(cls, span_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a span by ID.

        Args:
            span_id: Span ID

        Returns:
            Span data or None
        """
        cls._ensure_table()

        with get_cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM {cls._TABLE_NAME} WHERE span_id = ?",
                (span_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return cls._row_to_span(dict(row))

    @classmethod
    def get_trace(cls, trace_id: str, workspace_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all spans for a trace.

        Args:
            trace_id: Trace ID
            workspace_id: Filter by workspace ID (ownership check)

        Returns:
            List of span data
        """
        cls._ensure_table()

        conditions = ["trace_id = ?"]
        params = [trace_id]

        if workspace_id:
            conditions.append("(workspace_id = ? OR workspace_id IS NULL)")
            params.append(workspace_id)

        where_clause = " AND ".join(conditions)

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM {cls._TABLE_NAME}
                WHERE {where_clause}
                ORDER BY start_time
                """,
                params,
            )
            rows = cursor.fetchall()

        return [cls._row_to_span(dict(row)) for row in rows]

    @classmethod
    def query_traces(cls, query: TraceQuery) -> List[TraceSummary]:
        """
        Query traces with filtering.

        Args:
            query: Query parameters

        Returns:
            List of trace summaries
        """
        cls._ensure_table()

        # Build query for root spans (parent_span_id IS NULL)
        conditions = ["parent_span_id IS NULL"]
        params: List[Any] = []

        if query.workspace_id:
            conditions.append("(workspace_id = ? OR workspace_id IS NULL)")
            params.append(query.workspace_id)

        if query.service_name:
            conditions.append("service_name = ?")
            params.append(query.service_name)

        if query.operation_name:
            conditions.append("operation_name LIKE ?")
            params.append(f"%{query.operation_name}%")

        if query.start_time:
            conditions.append("start_time >= ?")
            params.append(query.start_time)

        if query.end_time:
            conditions.append("start_time <= ?")
            params.append(query.end_time)

        if query.min_duration_ms is not None:
            conditions.append("duration_ms >= ?")
            params.append(query.min_duration_ms)

        if query.max_duration_ms is not None:
            conditions.append("duration_ms <= ?")
            params.append(query.max_duration_ms)

        if query.has_error is not None:
            if query.has_error:
                conditions.append("status = 'error'")
            else:
                conditions.append("status != 'error'")

        where_clause = " AND ".join(conditions)

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM {cls._TABLE_NAME}
                WHERE {where_clause}
                ORDER BY start_time DESC
                LIMIT ?
                """,
                (*params, query.limit),
            )
            rows = cursor.fetchall()

            # Get trace summaries
            summaries = []
            for row in rows:
                row_dict = dict(row)
                trace_id = row_dict["trace_id"]

                # Count spans and errors
                cursor.execute(
                    f"""
                    SELECT
                        COUNT(*) as span_count,
                        SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count
                    FROM {cls._TABLE_NAME}
                    WHERE trace_id = ?
                    """,
                    (trace_id,),
                )
                counts = cursor.fetchone()

                summaries.append(TraceSummary(
                    trace_id=trace_id,
                    root_operation=row_dict["operation_name"],
                    service_name=row_dict.get("service_name", "flyto"),
                    start_time=row_dict["start_time"],
                    end_time=row_dict.get("end_time"),
                    duration_ms=row_dict.get("duration_ms"),
                    span_count=counts["span_count"] if counts else 1,
                    error_count=counts["error_count"] if counts else 0,
                    status=row_dict["status"],
                ))

        return summaries

    @classmethod
    def cleanup(cls, before: str) -> int:
        """
        Delete spans older than specified timestamp.

        Args:
            before: Delete spans before this timestamp

        Returns:
            Number of deleted spans
        """
        cls._ensure_table()

        with get_cursor() as cursor:
            cursor.execute(
                f"DELETE FROM {cls._TABLE_NAME} WHERE start_time < ?",
                (before,),
            )
            deleted = cursor.rowcount

        logger.info(f"Cleaned up {deleted} old spans")
        return deleted

    @classmethod
    def _row_to_span(cls, row: dict) -> Dict[str, Any]:
        """Convert database row to span data."""
        attributes = {}
        events = []

        if row.get("attributes"):
            try:
                attributes = json.loads(row["attributes"])
            except Exception:
                pass

        if row.get("events"):
            try:
                events = json.loads(row["events"])
            except Exception:
                pass

        return {
            "trace_id": row["trace_id"],
            "span_id": row["span_id"],
            "parent_span_id": row.get("parent_span_id"),
            "operation_name": row["operation_name"],
            "service_name": row.get("service_name", "flyto"),
            "start_time": row["start_time"],
            "end_time": row.get("end_time"),
            "duration_ms": row.get("duration_ms"),
            "status": row["status"],
            "status_message": row.get("status_message"),
            "attributes": attributes,
            "events": events,
        }
