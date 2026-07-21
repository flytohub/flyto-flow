"""
Metrics Service

Business logic layer for execution metrics.
Single responsibility: calculate and format execution statistics.
"""

from dataclasses import dataclass
from typing import Dict, Any, List

from gateway.storage.execution_repo import ExecutionRepository
from utils.time_utils import TimeRange, get_comparison_ranges, parse_time_range


@dataclass(frozen=True)
class ExecutionSummary:
    """Execution statistics summary with comparison to previous period."""

    total_executions: int
    successful: int
    failed: int
    success_rate: float
    avg_duration_ms: float
    executions_change: float
    success_rate_change: float
    duration_change: float
    failures_change: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API response format (camelCase for frontend)."""
        return {
            "totalExecutions": self.total_executions,
            "successful": self.successful,
            "failed": self.failed,
            "successRate": round(self.success_rate, 1),
            "avgDurationMs": round(self.avg_duration_ms, 0),
            "executionsChange": round(self.executions_change, 1),
            "successRateChange": round(self.success_rate_change, 1),
            "durationChange": round(self.duration_change, 1),
            "failuresChange": self.failures_change,
        }


class MetricsService:
    """Service for execution metrics calculations."""

    @staticmethod
    def _calculate_percentage_change(current: float, previous: float) -> float:
        """Calculate percentage change between two values."""
        if previous == 0:
            return 0.0
        return ((current - previous) / previous) * 100

    @staticmethod
    def _calculate_success_rate(successful: int, total: int) -> float:
        """Calculate success rate as percentage."""
        if total == 0:
            return 0.0
        return (successful / total) * 100

    @classmethod
    def get_execution_summary(cls, time_range_str: str, user_id: str = None) -> ExecutionSummary:
        """
        Get execution statistics summary with comparison to previous period.

        Args:
            time_range_str: Time range string (24h, 7d, 30d, 90d)
            user_id: Filter by user ID

        Returns:
            ExecutionSummary with current stats and changes from previous period
        """
        current, previous = get_comparison_ranges(time_range_str)

        # Get stats from repository
        current_stats = ExecutionRepository.get_execution_stats_by_date_range(
            current.start, current.end, user_id=user_id
        )
        prev_stats = ExecutionRepository.get_execution_stats_by_date_range(
            previous.start, previous.end, user_id=user_id
        )

        # Extract current period values
        total = current_stats["total"]
        successful = current_stats["successful"]
        failed = current_stats["failed"]
        avg_duration = current_stats["avg_duration_ms"]
        success_rate = cls._calculate_success_rate(successful, total)

        # Extract previous period values
        prev_total = prev_stats["total"]
        prev_successful = prev_stats["successful"]
        prev_failed = prev_stats["failed"]
        prev_avg_duration = prev_stats["avg_duration_ms"]
        prev_success_rate = cls._calculate_success_rate(prev_successful, prev_total)

        # Calculate changes
        return ExecutionSummary(
            total_executions=total,
            successful=successful,
            failed=failed,
            success_rate=success_rate,
            avg_duration_ms=avg_duration,
            executions_change=cls._calculate_percentage_change(total, prev_total),
            success_rate_change=success_rate - prev_success_rate,
            duration_change=cls._calculate_percentage_change(avg_duration, prev_avg_duration),
            failures_change=failed - prev_failed,
        )

    @classmethod
    def get_execution_trend(cls, time_range_str: str, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Get daily execution trend data for charts.

        Args:
            time_range_str: Time range string (24h, 7d, 30d, 90d)
            user_id: Filter by user ID

        Returns:
            List of daily stats with date, successful, failed, total
        """
        from datetime import timedelta

        tr = parse_time_range(time_range_str)
        daily_stats_list = ExecutionRepository.get_daily_stats(tr.start, tr.end, user_id=user_id)

        # Convert to dict for fast lookup
        stats_by_date = {
            item["date"]: {"successful": item["successful"], "failed": item["failed"]}
            for item in daily_stats_list
        }

        # Generate complete date range (fill missing dates with zeros)
        trend = []
        for i in range(tr.days):
            date = tr.start + timedelta(days=i)
            date_key = date.strftime("%Y-%m-%d")
            stats = stats_by_date.get(date_key, {"successful": 0, "failed": 0})
            trend.append({
                "date": date_key,
                "label": date.strftime("%m/%d"),
                "successful": stats["successful"],
                "failed": stats["failed"],
                "total": stats["successful"] + stats["failed"],
            })

        return trend

    @classmethod
    def get_top_workflows(
        cls, time_range_str: str, limit: int = 5, user_id: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get top workflows by execution count.

        Args:
            time_range_str: Time range string (24h, 7d, 30d, 90d)
            limit: Maximum number of workflows to return
            user_id: Filter by user ID

        Returns:
            List of workflow stats with id, name, executions, success_rate, avg_duration
        """
        tr = parse_time_range(time_range_str)
        top_workflows = ExecutionRepository.get_top_workflows_stats(
            tr.start, tr.end, limit, user_id=user_id
        )

        # Format response with success rate calculation (camelCase for frontend)
        return [
            {
                "id": w["id"],
                "name": w["name"],
                "executions": w["executions"],
                "successRate": round(
                    cls._calculate_success_rate(w["successful"], w["executions"]), 1
                ),
                "avgDurationMs": round(w["avg_duration_ms"], 0),
            }
            for w in top_workflows
        ]
