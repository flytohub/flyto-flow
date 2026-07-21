"""
Execution Job Models

Data classes for the Firestore-based job queue that bridges
mobile app -> Cloud API -> Desktop device execution.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class JobStatus(str, Enum):
    """Possible states of an execution job."""
    PENDING = "pending"
    CLAIMED = "claimed"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionMode(str, Enum):
    """How steps are dispatched to the device."""
    BATCH = "batch"          # All steps sent to device (existing behavior)
    STREAMING = "streaming"  # Steps sent one at a time (locked templates)


@dataclass
class ExecutionJob:
    """A Firestore-backed execution job dispatched to a desktop device."""
    id: str
    template_id: str
    template_name: str
    device_id: str
    user_id: str

    status: JobStatus = JobStatus.PENDING
    input_params: Dict[str, Any] = field(default_factory=dict)
    steps: List[Dict[str, Any]] = field(default_factory=list)

    # Execution mode
    execution_mode: ExecutionMode = ExecutionMode.BATCH

    # Step streaming (only used when execution_mode == STREAMING)
    # Private: never sent to device; cloud holds these for step-by-step dispatch
    streaming_steps: List[Dict[str, Any]] = field(default_factory=list)
    streaming_context: Dict[str, Any] = field(default_factory=dict)

    # Progress tracking
    current_step_index: int = 0
    total_steps: int = 0
    current_node_id: Optional[str] = None
    error_message: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None

    # Timestamps
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    claimed_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize job to dictionary for Firestore storage."""
        d = {
            "id": self.id,
            "template_id": self.template_id,
            "template_name": self.template_name,
            "device_id": self.device_id,
            "user_id": self.user_id,
            "status": self.status.value,
            "input_params": self.input_params,
            "steps": self.steps,
            "execution_mode": self.execution_mode.value,
            "streaming_steps": self.streaming_steps,
            "streaming_context": self.streaming_context,
            "current_step_index": self.current_step_index,
            "total_steps": self.total_steps,
            "current_node_id": self.current_node_id,
            "error_message": self.error_message,
            "variables": self.variables,
            "created_at": self.created_at,
            "claimed_at": self.claimed_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }
        return d

    def to_device_dict(self) -> Dict[str, Any]:
        """Dict safe to send to the device — strips private streaming data."""
        d = self.to_dict()
        d.pop("streaming_steps", None)
        d.pop("streaming_context", None)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionJob":
        """Deserialize job from a Firestore document dictionary."""
        mode_val = data.get("execution_mode", "batch")
        try:
            mode = ExecutionMode(mode_val)
        except ValueError:
            mode = ExecutionMode.BATCH

        return cls(
            id=data.get("id", ""),
            template_id=data.get("template_id", ""),
            template_name=data.get("template_name", ""),
            device_id=data.get("device_id", ""),
            user_id=data.get("user_id", ""),
            status=JobStatus(data.get("status", "pending")),
            input_params=data.get("input_params", {}),
            steps=data.get("steps", []),
            execution_mode=mode,
            streaming_steps=data.get("streaming_steps", []),
            streaming_context=data.get("streaming_context", {}),
            current_step_index=data.get("current_step_index", 0),
            total_steps=data.get("total_steps", 0),
            current_node_id=data.get("current_node_id"),
            error_message=data.get("error_message"),
            variables=data.get("variables"),
            created_at=data.get("created_at", ""),
            claimed_at=data.get("claimed_at"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
        )
