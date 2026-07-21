"""
Worker Configuration

Configuration dataclass for the job queue worker.
"""

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class WorkerConfig:
    """Worker configuration."""

    worker_id: str = field(default_factory=lambda: f"worker-{uuid4().hex[:8]}")
    poll_interval_seconds: float = 1.0
    heartbeat_interval_seconds: float = 10.0
    lease_duration_seconds: int = 300
    max_concurrent_jobs: int = 1
    max_memory_mb: int = 512  # Per-job memory cap (MB) — prevents memory bombs
    max_execution_time_ms: int = 180_000  # Per-job timeout: 3 minutes
