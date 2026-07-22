"""
Local SQLite Storage

Stores execution records and logs locally.
CE stores workflow definitions and execution history in local SQLite files.
"""

from gateway.storage.database import get_db, init_db, close_db
from gateway.storage.models import Execution, ExecutionStep
from gateway.storage.execution_repo import ExecutionRepository

__all__ = [
    "get_db",
    "init_db",
    "close_db",
    "Execution",
    "ExecutionStep",
    "ExecutionRepository",
]
