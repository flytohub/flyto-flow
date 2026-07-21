"""
Metrics API

REST endpoints for metrics collection and export.

NOTE: This is an Enterprise-only feature (Phase 8).
Requires OBSERVABILITY_METRICS capability.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel

from api.auth import get_current_user
from capabilities import Feature, require_any_feature
from services.observability.metrics.aggregator import MetricsAggregator
from services.observability.metrics.collector import get_collector
from services.observability.metrics.exporter import PrometheusExporter
from services.observability.metrics.registry import list_metrics_by_category
from gateway.storage.metrics_repo import MetricsRepository

logger = logging.getLogger(__name__)

# All endpoints in this router require either LOCAL_METRICS or HOSTED_OBSERVABILITY
router = APIRouter(
    prefix="/metrics",
    tags=["metrics"],
    dependencies=[Depends(require_any_feature(
        Feature.LOCAL_METRICS,
        Feature.HOSTED_OBSERVABILITY,
    ))],
)


class MetricRecordRequest(BaseModel):
    """Request to record a metric."""

    name: str
    value: float
    labels: Optional[dict] = None


@router.get("/")
async def get_metrics_prometheus():
    """
    Get metrics in Prometheus format.

    Returns text/plain formatted metrics for Prometheus scraping.
    """
    collector = get_collector()
    exporter = PrometheusExporter(collector)
    content = exporter.export()

    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
    )


@router.get("/json")
async def get_metrics_json():
    """
    Get metrics in JSON format.

    Returns all current metrics as JSON.
    """
    collector = get_collector()
    metrics = collector.get_all_metrics()

    return {
        "ok": True,
        "metrics": [m.to_dict() for m in metrics],
    }


@router.get("/dashboard")
async def get_dashboard_metrics(
    window_seconds: int = Query(default=60, ge=1, le=3600),
):
    """
    Get pre-aggregated metrics for dashboard display.

    Args:
        window_seconds: Time window for rate calculations (1-3600)

    Returns:
        Dashboard-ready metrics grouped by category.
    """
    collector = get_collector()
    aggregator = MetricsAggregator(collector)

    return {
        "ok": True,
        "data": aggregator.get_dashboard_data(window_seconds),
    }


@router.get("/definitions")
async def get_metric_definitions():
    """
    Get all metric definitions.

    Returns metadata about available metrics.
    """
    by_category = list_metrics_by_category()

    return {
        "ok": True,
        "categories": {
            category: [m.to_dict() for m in metrics]
            for category, metrics in by_category.items()
        },
    }


@router.get("/history/{name}")
async def get_metric_history(
    name: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
):
    """
    Get historical values for a metric.

    Args:
        name: Metric name
        start: Start timestamp (ISO format)
        end: End timestamp (ISO format)
        limit: Maximum results (1-1000)

    Returns:
        Historical metric values.
    """
    metrics = MetricsRepository.query(
        name=name,
        start=start,
        end=end,
        limit=limit,
    )

    return {
        "ok": True,
        "name": name,
        "count": len(metrics),
        "metrics": [m.to_dict() for m in metrics],
    }


@router.get("/series/{name}")
async def get_metric_series(
    name: str,
    start: str,
    end: str,
    interval_seconds: int = Query(default=60, ge=1, le=3600),
):
    """
    Get time-series data for a metric.

    Args:
        name: Metric name
        start: Start timestamp (ISO format)
        end: End timestamp (ISO format)
        interval_seconds: Aggregation interval (1-3600)

    Returns:
        Aggregated time-series data.
    """
    series = MetricsRepository.get_series(
        name=name,
        start=start,
        end=end,
        interval_seconds=interval_seconds,
    )

    return {
        "ok": True,
        "name": name,
        "interval_seconds": interval_seconds,
        "points": series,
    }


@router.get("/names")
async def list_metric_names():
    """
    List all stored metric names.

    Returns:
        List of unique metric names.
    """
    names = MetricsRepository.get_metric_names()

    return {
        "ok": True,
        "names": names,
    }


@router.post("/record")
async def record_metric(request: MetricRecordRequest):
    """
    Record a metric value.

    This endpoint allows external systems to push metrics.
    """
    collector = get_collector()
    collector.set_gauge(
        name=request.name,
        value=request.value,
        labels=request.labels,
    )

    # Also persist to database
    MetricsRepository.record(
        name=request.name,
        type="gauge",
        value=request.value,
        labels=request.labels,
    )

    return {
        "ok": True,
        "message": f"Recorded metric {request.name}",
    }


@router.delete("/cleanup")
async def cleanup_old_metrics(
    before: str,
):
    """
    Delete metrics older than specified timestamp.

    Args:
        before: Delete metrics before this timestamp (ISO format)

    Returns:
        Number of deleted metrics.
    """
    deleted = MetricsRepository.cleanup(before)

    return {
        "ok": True,
        "deleted": deleted,
    }


# =============================================================================
# Execution Analytics Endpoints (for Observability Dashboard)
# =============================================================================

@router.get("/summary")
async def get_execution_summary(
    time_range: str = Query(default="7d", alias="range", pattern="^(24h|7d|30d|90d)$"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get execution statistics summary.

    Args:
        time_range: Time range (24h, 7d, 30d, 90d)

    Returns:
        Execution summary with totals, success rate, and trends.
    """
    from services.observability.metrics_service import MetricsService

    summary = MetricsService.get_execution_summary(time_range, user_id=current_user["id"])
    return summary.to_dict()


@router.get("/trend")
async def get_execution_trend(
    time_range: str = Query(default="7d", alias="range", pattern="^(24h|7d|30d|90d)$"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get execution trend data for charts.

    Args:
        time_range: Time range (24h, 7d, 30d, 90d)

    Returns:
        Daily execution counts for charting.
    """
    from services.observability.metrics_service import MetricsService

    trend = MetricsService.get_execution_trend(time_range, user_id=current_user["id"])
    return {"trend": trend}


@router.get("/top-workflows")
async def get_top_workflows(
    limit: int = Query(default=5, ge=1, le=20),
    time_range: str = Query(default="7d", alias="range", pattern="^(24h|7d|30d|90d)$"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get top workflows by execution count.

    Args:
        limit: Number of workflows to return
        time_range: Time range (24h, 7d, 30d, 90d)

    Returns:
        Top workflows with execution stats.
    """
    from services.observability.metrics_service import MetricsService

    workflows = MetricsService.get_top_workflows(time_range, limit, user_id=current_user["id"])
    return {"workflows": workflows}


@router.get("/recent-failures")
async def get_recent_failures(
    limit: int = Query(default=5, ge=1, le=20),
    current_user: dict = Depends(get_current_user),
):
    """
    Get recent failed executions.

    Args:
        limit: Number of failures to return

    Returns:
        Recent failed executions.
    """
    from datetime import datetime
    from gateway.storage.execution_repo import ExecutionRepository

    # Get failed executions using multi-status filter
    # Handles both 'failure' (SQLite) and 'failed' (Firebase) status values
    all_execs = ExecutionRepository.list_executions(
        statuses=["failure", "failed"],
        user_id=current_user["id"],
        limit=limit,
    )

    # Filter failed executions
    failures = []
    for exec_obj in all_execs:
        start_str = exec_obj.started_at or ""
        try:
            exec_time = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            # Use camelCase for frontend compatibility
            failures.append({
                "executionId": exec_obj.id or "",
                "workflowId": exec_obj.workflow_id or "",
                "workflowName": exec_obj.workflow_name or "Unknown",
                "error": exec_obj.error_message or "Unknown error",
                "failedAt": start_str,
                "durationMs": exec_obj.duration_ms or 0,
                "_sort_time": exec_time,
            })
        except (ValueError, TypeError):
            continue

    # Sort by time (most recent first) and take top N
    failures.sort(key=lambda f: f.get("_sort_time", datetime.min), reverse=True)
    failures = failures[:limit]

    # Remove sort key
    for f in failures:
        f.pop("_sort_time", None)

    return {"failures": failures}


@router.get("/export")
async def export_metrics(
    format: str = Query(default="json", pattern="^(json|csv|prometheus)$"),
    time_range: str = Query(default="24h", pattern="^(1h|6h|24h|7d|30d)$"),
):
    """
    Export metrics in specified format.

    Args:
        format: Export format (json, csv, prometheus)
        time_range: Time range for export

    Returns:
        Metrics data in requested format.
    """
    from datetime import datetime, timedelta, timezone

    # Calculate time range
    now = datetime.now(timezone.utc)
    range_map = {
        "1h": timedelta(hours=1),
        "6h": timedelta(hours=6),
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
    }
    start_time = now - range_map.get(time_range, timedelta(hours=24))

    # Get metrics
    metrics = MetricsRepository.query(
        start=start_time.isoformat(),
        end=now.isoformat(),
        limit=10000,
    )

    if format == "prometheus":
        # Return Prometheus format
        collector = get_collector()
        exporter = PrometheusExporter(collector)
        content = exporter.export()
        return Response(
            content=content,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=metrics_{time_range}.txt"},
        )

    elif format == "csv":
        # Return CSV format
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["timestamp", "name", "type", "value", "labels"])

        for m in metrics:
            writer.writerow([
                m.timestamp if hasattr(m, "timestamp") else "",
                m.name if hasattr(m, "name") else "",
                m.type if hasattr(m, "type") else "",
                m.value if hasattr(m, "value") else "",
                str(m.labels) if hasattr(m, "labels") else "",
            ])

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=metrics_{time_range}.csv"},
        )

    else:
        # Return JSON format
        return {
            "ok": True,
            "time_range": time_range,
            "start": start_time.isoformat(),
            "end": now.isoformat(),
            "count": len(metrics),
            "metrics": [m.to_dict() for m in metrics],
        }
