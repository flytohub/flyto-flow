"""
Execution Manager Service

DEPRECATED: This file is maintained for backwards compatibility.
Please import from services.execution instead:

    from services.runtime.execution import (
        ExecutionManager,
        get_execution_manager,
        ExecutionStatus,
        ExecutionInfo,
    )

All functionality has been split into:
- services/execution/enums.py - ExecutionStatus enum
- services/execution/models.py - ExecutionInfo class
- services/execution/utils.py - Helper functions
- services/execution/hooks_setup.py - Hook configuration
- services/execution/persistence.py - local SQLite persistence
- services/execution/queue_integration.py - Worker pool (Phase 1)
- services/execution/service.py - Main ExecutionManager class
"""

# Re-export everything for backwards compatibility
from services.runtime.execution import (
    # Enums
    ExecutionStatus,
    # Models
    ExecutionInfo,
    # Main service
    ExecutionManager,
    get_execution_manager,
    # Queue integration
    USE_QUEUE,
    start_worker_pool,
    stop_worker_pool,
    get_queue_stats,
)

# Private helpers for backwards compatibility
def _utc_now():
    """Deprecated: Use utc_now from services.execution"""
    from services.runtime.execution import utc_now
    return utc_now()

def _ensure_sqlite_initialized():
    """Deprecated: Use ensure_sqlite_initialized from services.execution"""
    from services.runtime.execution import ensure_sqlite_initialized
    ensure_sqlite_initialized()

__all__ = [
    "ExecutionStatus",
    "ExecutionInfo",
    "ExecutionManager",
    "get_execution_manager",
    "USE_QUEUE",
    "start_worker_pool",
    "stop_worker_pool",
    "get_queue_stats",
]
