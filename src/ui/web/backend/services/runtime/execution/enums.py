"""
Execution Status Enums

Defines the possible states of a workflow execution.
"""

from enum import Enum


class ExecutionStatus(str, Enum):
    """
    Execution status enum.

    Lifecycle:
        PENDING -> QUEUED -> RUNNING -> COMPLETED/FAILED/CANCELLED/TIMED_OUT
                                    -> PAUSED -> RUNNING (resumed)
    """
    PENDING = "pending"      # Created, not yet started
    QUEUED = "queued"        # In queue, waiting for worker
    RUNNING = "running"      # Actively executing
    PAUSED = "paused"        # Paused at breakpoint or by user
    COMPLETED = "completed"  # Successfully finished
    FAILED = "failed"        # Execution error
    CANCELLED = "cancelled"  # User cancelled
    TIMED_OUT = "timed_out"  # Exceeded time limit
