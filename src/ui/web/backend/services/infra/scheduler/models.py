"""
Scheduler Models

Enums and data classes for scheduled workflow execution.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4


class ScheduleStatus(str, Enum):
    """Schedule status."""

    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"


@dataclass
class Schedule:
    """
    Scheduled workflow execution.

    Supports cron expressions and interval-based scheduling.
    """

    id: str
    name: str
    workflow_id: str
    workflow_name: str = ""

    # Schedule expression
    cron_expression: Optional[str] = None  # e.g., "0 9 * * *"
    interval_seconds: Optional[int] = None  # Alternative to cron

    # Configuration
    timezone: str = "UTC"
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    inputs: Dict[str, Any] = field(default_factory=dict)

    # Execution limits
    max_concurrent: int = 1
    timeout_ms: int = 300000  # 5 minutes
    retry_on_failure: bool = False

    # Ownership
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    project_id: Optional[str] = None
    workspace_id: Optional[str] = None  # For Cloud Functions routing

    # Polling trigger fields
    poll_url: Optional[str] = None
    poll_config: Optional[str] = None  # JSON: {poll_method, poll_headers, poll_body, dedup_key}
    last_poll_hash: Optional[str] = None  # Hash of last polled data for dedup
    last_poll_data: Optional[str] = None  # Last polled response (JSON)

    # Tracking
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    run_count: int = 0
    failure_count: int = 0

    # Metadata
    description: Optional[str] = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert schedule to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "cron_expression": self.cron_expression,
            "interval_seconds": self.interval_seconds,
            "timezone": self.timezone,
            "status": self.status.value,
            "inputs": self.inputs,
            "max_concurrent": self.max_concurrent,
            "timeout_ms": self.timeout_ms,
            "retry_on_failure": self.retry_on_failure,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "project_id": self.project_id,
            "workspace_id": self.workspace_id,
            "poll_url": self.poll_url,
            "poll_config": self.poll_config,
            "last_poll_hash": self.last_poll_hash,
            "last_run_at": self.last_run_at,
            "next_run_at": self.next_run_at,
            "run_count": self.run_count,
            "failure_count": self.failure_count,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Schedule":
        """Create a Schedule instance from a dictionary."""
        return cls(
            id=data.get("id", str(uuid4())),
            name=data["name"],
            workflow_id=data["workflow_id"],
            workflow_name=data.get("workflow_name", ""),
            cron_expression=data.get("cron_expression"),
            interval_seconds=data.get("interval_seconds"),
            timezone=data.get("timezone", "UTC"),
            status=ScheduleStatus(data.get("status", "active")),
            inputs=data.get("inputs", {}),
            max_concurrent=data.get("max_concurrent", 1),
            timeout_ms=data.get("timeout_ms", 300000),
            retry_on_failure=data.get("retry_on_failure", False),
            user_id=data.get("user_id"),
            organization_id=data.get("organization_id"),
            project_id=data.get("project_id"),
            workspace_id=data.get("workspace_id"),
            poll_url=data.get("poll_url"),
            poll_config=data.get("poll_config"),
            last_poll_hash=data.get("last_poll_hash"),
            last_poll_data=data.get("last_poll_data"),
            last_run_at=data.get("last_run_at"),
            next_run_at=data.get("next_run_at"),
            run_count=data.get("run_count", 0),
            failure_count=data.get("failure_count", 0),
            description=data.get("description"),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
        )
