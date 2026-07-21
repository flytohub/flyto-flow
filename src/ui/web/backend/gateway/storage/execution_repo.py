"""
Execution Repository

CRUD operations for execution records in SQLite.

Split into focused modules:
- execution_read.py  — read operations (get, list, search, statistics)
- execution_write.py — write operations (create, update, delete, steps)
"""

from gateway.storage.execution_read import ExecutionReadMixin
from gateway.storage.execution_write import ExecutionWriteMixin, _utc_now  # noqa: F401


class ExecutionRepository(ExecutionWriteMixin, ExecutionReadMixin):
    """Repository for execution record operations."""
    pass
