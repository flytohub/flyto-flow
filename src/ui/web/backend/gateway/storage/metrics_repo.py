"""
Metrics Repository

Single responsibility: Store metrics to SQLite for historical queries.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from gateway.storage.database import get_cursor, get_db

logger = logging.getLogger(__name__)


@dataclass
class StoredMetric:
    """Stored metric record."""

    id: str
    name: str
    type: str
    value: float
    labels: Dict[str, str]
    timestamp: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "value": self.value,
            "labels": self.labels,
            "timestamp": self.timestamp,
            "created_at": self.created_at,
        }

    @classmethod
    def from_row(cls, row: dict) -> "StoredMetric":
        """Create from database row."""
        labels = {}
        if row.get("labels"):
            try:
                labels = json.loads(row["labels"])
            except Exception:
                pass

        return cls(
            id=row["id"],
            name=row["name"],
            type=row["type"],
            value=row["value"],
            labels=labels,
            timestamp=row["timestamp"],
            created_at=row.get("created_at", ""),
        )


class MetricsRepository:
    """
    SQLite-based metrics storage for historical queries.

    Provides:
    - Time-series storage of metric values
    - Query by name, time range, and labels
    - Automatic cleanup of old metrics
    """

    _TABLE_NAME = "metrics"
    _initialized = False

    @classmethod
    def _ensure_table(cls) -> None:
        """Ensure metrics table exists."""
        if cls._initialized:
            return

        with get_cursor() as cursor:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {cls._TABLE_NAME} (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    value REAL NOT NULL,
                    labels TEXT,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_metrics_name_ts
                ON {cls._TABLE_NAME}(name, timestamp)
            """)
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp
                ON {cls._TABLE_NAME}(timestamp)
            """)

        cls._initialized = True

    @classmethod
    def record(
        cls,
        name: str,
        type: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        timestamp: Optional[str] = None,
    ) -> str:
        """
        Record a metric value.

        Args:
            name: Metric name
            type: Metric type (counter, gauge, histogram)
            value: Metric value
            labels: Optional labels
            timestamp: Optional timestamp (defaults to now)

        Returns:
            Metric ID
        """
        cls._ensure_table()

        metric_id = str(uuid4())
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        labels_json = json.dumps(labels or {})

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {cls._TABLE_NAME}
                (id, name, type, value, labels, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (metric_id, name, type, value, labels_json, ts),
            )

        return metric_id

    @classmethod
    def record_batch(
        cls,
        metrics: List[Dict[str, Any]],
    ) -> int:
        """
        Record multiple metrics in a single transaction.

        Args:
            metrics: List of metric dictionaries with keys:
                     name, type, value, labels, timestamp

        Returns:
            Number of metrics recorded
        """
        cls._ensure_table()

        records = []
        for m in metrics:
            records.append((
                str(uuid4()),
                m["name"],
                m["type"],
                m["value"],
                json.dumps(m.get("labels", {})),
                m.get("timestamp", datetime.now(timezone.utc).isoformat()),
            ))

        with get_cursor() as cursor:
            cursor.executemany(
                f"""
                INSERT INTO {cls._TABLE_NAME}
                (id, name, type, value, labels, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                records,
            )

        return len(records)

    @classmethod
    def query(
        cls,
        name: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        limit: int = 1000,
    ) -> List[StoredMetric]:
        """
        Query metrics by name and time range.

        Args:
            name: Metric name
            start: Start timestamp (inclusive)
            end: End timestamp (inclusive)
            labels: Filter by labels
            limit: Maximum results

        Returns:
            List of stored metrics
        """
        cls._ensure_table()

        conditions = ["name = ?"]
        params: List[Any] = [name]

        if start:
            conditions.append("timestamp >= ?")
            params.append(start)

        if end:
            conditions.append("timestamp <= ?")
            params.append(end)

        where_clause = " AND ".join(conditions)

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM {cls._TABLE_NAME}
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (*params, limit),
            )
            rows = cursor.fetchall()

        metrics = [StoredMetric.from_row(dict(row)) for row in rows]

        # Filter by labels if specified
        if labels:
            metrics = [
                m for m in metrics
                if all(m.labels.get(k) == v for k, v in labels.items())
            ]

        return metrics

    @classmethod
    def get_latest(
        cls,
        name: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> Optional[StoredMetric]:
        """
        Get the latest value for a metric.

        Args:
            name: Metric name
            labels: Filter by labels

        Returns:
            Latest metric or None
        """
        metrics = cls.query(name, labels=labels, limit=1)
        return metrics[0] if metrics else None

    @classmethod
    def get_series(
        cls,
        name: str,
        start: str,
        end: str,
        interval_seconds: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        Get time-series data with aggregation.

        Args:
            name: Metric name
            start: Start timestamp
            end: End timestamp
            interval_seconds: Aggregation interval

        Returns:
            List of time-series points with avg, min, max, count
        """
        cls._ensure_table()

        # SQLite doesn't have great time bucketing, so we query all and aggregate
        metrics = cls.query(name, start, end, limit=10000)

        if not metrics:
            return []

        # Group by time bucket
        from datetime import datetime as dt

        buckets: Dict[str, List[float]] = {}

        for m in metrics:
            try:
                ts = dt.fromisoformat(m.timestamp.replace("Z", "+00:00"))
                bucket_ts = ts.replace(
                    second=(ts.second // interval_seconds) * interval_seconds,
                    microsecond=0,
                )
                bucket_key = bucket_ts.isoformat()

                if bucket_key not in buckets:
                    buckets[bucket_key] = []
                buckets[bucket_key].append(m.value)
            except Exception:
                continue

        # Aggregate each bucket
        result = []
        for bucket_key in sorted(buckets.keys()):
            values = buckets[bucket_key]
            result.append({
                "timestamp": bucket_key,
                "count": len(values),
                "sum": sum(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
            })

        return result

    @classmethod
    def cleanup(
        cls,
        before: str,
    ) -> int:
        """
        Delete metrics older than specified timestamp.

        Args:
            before: Delete metrics before this timestamp

        Returns:
            Number of deleted metrics
        """
        cls._ensure_table()

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                DELETE FROM {cls._TABLE_NAME}
                WHERE timestamp < ?
                """,
                (before,),
            )
            deleted = cursor.rowcount

        logger.info(f"Cleaned up {deleted} old metrics")
        return deleted

    @classmethod
    def get_metric_names(cls) -> List[str]:
        """Get list of unique metric names."""
        cls._ensure_table()

        with get_cursor() as cursor:
            cursor.execute(
                f"SELECT DISTINCT name FROM {cls._TABLE_NAME} ORDER BY name"
            )
            rows = cursor.fetchall()

        return [row["name"] for row in rows]

    @classmethod
    def count(cls, name: Optional[str] = None) -> int:
        """
        Count stored metrics.

        Args:
            name: Optional metric name filter

        Returns:
            Number of metrics
        """
        cls._ensure_table()

        with get_cursor() as cursor:
            if name:
                cursor.execute(
                    f"SELECT COUNT(*) as cnt FROM {cls._TABLE_NAME} WHERE name = ?",
                    (name,),
                )
            else:
                cursor.execute(f"SELECT COUNT(*) as cnt FROM {cls._TABLE_NAME}")
            row = cursor.fetchone()

        return row["cnt"] if row else 0
