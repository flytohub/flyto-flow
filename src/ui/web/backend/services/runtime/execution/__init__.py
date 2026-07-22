"""
Execution Service Package

Manages workflow execution lifecycle:
- Start/run workflows
- Track execution status
- Cancel running workflows

Storage:
- In-memory: Active/recent executions for fast access
- SQLite: All execution history for persistence
- SQLite: execution state, summaries, and evidence references

Phase 0 Features:
- Execution snapshots for reproducibility
- Runs directory with manifest/steps/result files
- Step-level tracking with hooks
- Outcome classification with error fingerprinting

Phase 1 Features:
- Queue-based execution with worker pool
- Bounded concurrency
- Job persistence and retry
- Graceful cancellation via CancellationToken
"""

# Enums
from services.runtime.execution.enums import ExecutionStatus

# Models
from services.runtime.execution.models import ExecutionInfo

# Main service
from services.runtime.execution.service import ExecutionManager, get_execution_manager

# Queue integration (Phase 1)
from services.runtime.execution.queue_integration import (
    USE_QUEUE,
    start_worker_pool,
    stop_worker_pool,
    get_queue_stats,
)

# Utility functions
from services.runtime.execution.utils import utc_now, ensure_sqlite_initialized

# Persistence functions (for direct access if needed)
from services.runtime.execution.persistence import (
    get_execution_status,
    get_execution_history,
    cleanup_old_executions,
)

__all__ = [
    # Enums
    "ExecutionStatus",
    # Models
    "ExecutionInfo",
    # Main service
    "ExecutionManager",
    "get_execution_manager",
    # Queue integration
    "USE_QUEUE",
    "start_worker_pool",
    "stop_worker_pool",
    "get_queue_stats",
    # Utilities
    "utc_now",
    "ensure_sqlite_initialized",
    # Persistence
    "get_execution_status",
    "get_execution_history",
    "cleanup_old_executions",
]
