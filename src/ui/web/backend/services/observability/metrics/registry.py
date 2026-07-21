"""
Metrics Registry

Single responsibility: Define available metrics and their metadata.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from services.observability.metrics.collector import MetricType


@dataclass
class MetricDefinition:
    """Definition of a metric."""

    name: str
    type: MetricType
    help_text: str
    labels: List[str]
    unit: Optional[str] = None
    buckets: Optional[List[float]] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type.value,
            "help": self.help_text,
            "labels": self.labels,
            "unit": self.unit,
        }


# Duration buckets in seconds
DURATION_BUCKETS_SECONDS = [
    0.001,  # 1ms
    0.005,  # 5ms
    0.01,  # 10ms
    0.025,  # 25ms
    0.05,  # 50ms
    0.1,  # 100ms
    0.25,  # 250ms
    0.5,  # 500ms
    1.0,  # 1s
    2.5,  # 2.5s
    5.0,  # 5s
    10.0,  # 10s
    30.0,  # 30s
    60.0,  # 1min
    120.0,  # 2min
    300.0,  # 5min
]

# Queue depth buckets
QUEUE_DEPTH_BUCKETS = [0, 1, 5, 10, 25, 50, 100, 250, 500, 1000]


# Workflow execution metrics
WORKFLOW_METRICS: Dict[str, MetricDefinition] = {
    "workflow_executions_total": MetricDefinition(
        name="workflow_executions_total",
        type=MetricType.COUNTER,
        help_text="Total number of workflow executions",
        labels=["workflow_id", "workflow_name", "status"],
    ),
    "workflow_execution_duration_seconds": MetricDefinition(
        name="workflow_execution_duration_seconds",
        type=MetricType.HISTOGRAM,
        help_text="Duration of workflow executions in seconds",
        labels=["workflow_id", "workflow_name"],
        unit="seconds",
        buckets=DURATION_BUCKETS_SECONDS,
    ),
    "workflow_active_executions": MetricDefinition(
        name="workflow_active_executions",
        type=MetricType.GAUGE,
        help_text="Number of currently active workflow executions",
        labels=["workflow_id"],
    ),
}

# Node execution metrics
NODE_METRICS: Dict[str, MetricDefinition] = {
    "node_executions_total": MetricDefinition(
        name="node_executions_total",
        type=MetricType.COUNTER,
        help_text="Total number of node executions",
        labels=["module", "status"],
    ),
    "node_execution_duration_seconds": MetricDefinition(
        name="node_execution_duration_seconds",
        type=MetricType.HISTOGRAM,
        help_text="Duration of node executions in seconds",
        labels=["module"],
        unit="seconds",
        buckets=DURATION_BUCKETS_SECONDS,
    ),
    "node_retries_total": MetricDefinition(
        name="node_retries_total",
        type=MetricType.COUNTER,
        help_text="Total number of node execution retries",
        labels=["module", "error_type"],
    ),
}

# Job queue metrics
QUEUE_METRICS: Dict[str, MetricDefinition] = {
    "queue_jobs_total": MetricDefinition(
        name="queue_jobs_total",
        type=MetricType.COUNTER,
        help_text="Total number of jobs enqueued",
        labels=["priority"],
    ),
    "queue_depth": MetricDefinition(
        name="queue_depth",
        type=MetricType.GAUGE,
        help_text="Current number of jobs in queue",
        labels=["status"],
    ),
    "queue_job_wait_seconds": MetricDefinition(
        name="queue_job_wait_seconds",
        type=MetricType.HISTOGRAM,
        help_text="Time jobs spent waiting in queue",
        labels=[],
        unit="seconds",
        buckets=DURATION_BUCKETS_SECONDS,
    ),
}

# Worker metrics
WORKER_METRICS: Dict[str, MetricDefinition] = {
    "worker_jobs_processed_total": MetricDefinition(
        name="worker_jobs_processed_total",
        type=MetricType.COUNTER,
        help_text="Total number of jobs processed by workers",
        labels=["worker_id", "status"],
    ),
    "worker_utilization": MetricDefinition(
        name="worker_utilization",
        type=MetricType.GAUGE,
        help_text="Worker utilization ratio (0-1)",
        labels=["worker_id"],
    ),
    "worker_active_jobs": MetricDefinition(
        name="worker_active_jobs",
        type=MetricType.GAUGE,
        help_text="Number of jobs currently being processed",
        labels=["worker_id"],
    ),
    "worker_memory_bytes": MetricDefinition(
        name="worker_memory_bytes",
        type=MetricType.GAUGE,
        help_text="Memory usage of worker process",
        labels=["worker_id"],
        unit="bytes",
    ),
}

# API metrics
API_METRICS: Dict[str, MetricDefinition] = {
    "http_requests_total": MetricDefinition(
        name="http_requests_total",
        type=MetricType.COUNTER,
        help_text="Total number of HTTP requests",
        labels=["method", "endpoint", "status_code"],
    ),
    "http_request_duration_seconds": MetricDefinition(
        name="http_request_duration_seconds",
        type=MetricType.HISTOGRAM,
        help_text="Duration of HTTP requests in seconds",
        labels=["method", "endpoint"],
        unit="seconds",
        buckets=DURATION_BUCKETS_SECONDS,
    ),
    "http_requests_in_progress": MetricDefinition(
        name="http_requests_in_progress",
        type=MetricType.GAUGE,
        help_text="Number of HTTP requests in progress",
        labels=["method"],
    ),
}

# Error metrics
ERROR_METRICS: Dict[str, MetricDefinition] = {
    "errors_total": MetricDefinition(
        name="errors_total",
        type=MetricType.COUNTER,
        help_text="Total number of errors",
        labels=["error_type", "error_category", "module"],
    ),
    "error_rate": MetricDefinition(
        name="error_rate",
        type=MetricType.GAUGE,
        help_text="Error rate over last window",
        labels=["window_seconds"],
    ),
}

# System metrics
SYSTEM_METRICS: Dict[str, MetricDefinition] = {
    "process_cpu_seconds_total": MetricDefinition(
        name="process_cpu_seconds_total",
        type=MetricType.COUNTER,
        help_text="Total CPU time used by process",
        labels=[],
        unit="seconds",
    ),
    "process_memory_bytes": MetricDefinition(
        name="process_memory_bytes",
        type=MetricType.GAUGE,
        help_text="Process memory usage",
        labels=["type"],
        unit="bytes",
    ),
    "process_open_fds": MetricDefinition(
        name="process_open_fds",
        type=MetricType.GAUGE,
        help_text="Number of open file descriptors",
        labels=[],
    ),
}


# All metric definitions
METRIC_DEFINITIONS: Dict[str, MetricDefinition] = {
    **WORKFLOW_METRICS,
    **NODE_METRICS,
    **QUEUE_METRICS,
    **WORKER_METRICS,
    **API_METRICS,
    **ERROR_METRICS,
    **SYSTEM_METRICS,
}


def get_metric_definition(name: str) -> Optional[MetricDefinition]:
    """Get metric definition by name."""
    return METRIC_DEFINITIONS.get(name)


def list_metrics() -> List[MetricDefinition]:
    """List all metric definitions."""
    return list(METRIC_DEFINITIONS.values())


def list_metrics_by_category() -> Dict[str, List[MetricDefinition]]:
    """List metrics grouped by category."""
    return {
        "workflow": list(WORKFLOW_METRICS.values()),
        "node": list(NODE_METRICS.values()),
        "queue": list(QUEUE_METRICS.values()),
        "worker": list(WORKER_METRICS.values()),
        "api": list(API_METRICS.values()),
        "error": list(ERROR_METRICS.values()),
        "system": list(SYSTEM_METRICS.values()),
    }
