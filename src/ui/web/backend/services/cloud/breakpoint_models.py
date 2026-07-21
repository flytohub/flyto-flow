"""
Cloud Breakpoint Models

Standalone enums and dataclasses for cloud-mode breakpoints.
No dependency on flyto-core — these mirror core.engine.breakpoints.models
but are self-contained for the cloud API.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class BreakpointStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ApprovalMode(str, Enum):
    SINGLE = "single"
    ALL = "all"
    MAJORITY = "majority"
    FIRST = "first"


@dataclass
class BreakpointRequest:
    breakpoint_id: str
    execution_id: str
    step_id: str
    workflow_id: Optional[str] = None
    title: str = "Approval Required"
    description: str = ""
    required_approvers: List[str] = field(default_factory=list)
    approval_mode: ApprovalMode = ApprovalMode.SINGLE
    timeout_seconds: Optional[int] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    context_snapshot: Dict[str, Any] = field(default_factory=dict)
    custom_fields: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.timeout_seconds and not self.expires_at:
            self.expires_at = self.created_at + timedelta(seconds=self.timeout_seconds)

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "breakpoint_id": self.breakpoint_id,
            "execution_id": self.execution_id,
            "step_id": self.step_id,
            "workflow_id": self.workflow_id,
            "title": self.title,
            "description": self.description,
            "required_approvers": self.required_approvers,
            "approval_mode": self.approval_mode.value,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_expired": self.is_expired,
            "context_snapshot": self.context_snapshot,
            "custom_fields": self.custom_fields,
            "metadata": self.metadata,
        }


@dataclass
class ApprovalResponse:
    breakpoint_id: str
    approved: bool
    user_id: str
    comment: Optional[str] = None
    custom_inputs: Dict[str, Any] = field(default_factory=dict)
    responded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "breakpoint_id": self.breakpoint_id,
            "approved": self.approved,
            "user_id": self.user_id,
            "comment": self.comment,
            "custom_inputs": self.custom_inputs,
            "responded_at": self.responded_at.isoformat(),
        }


@dataclass
class BreakpointResult:
    breakpoint_id: str
    status: BreakpointStatus
    responses: List[ApprovalResponse] = field(default_factory=list)
    resolved_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    final_inputs: Dict[str, Any] = field(default_factory=dict)

    @property
    def approved(self) -> bool:
        return self.status == BreakpointStatus.APPROVED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "breakpoint_id": self.breakpoint_id,
            "status": self.status.value,
            "approved": self.approved,
            "responses": [r.to_dict() for r in self.responses],
            "resolved_at": self.resolved_at.isoformat(),
            "final_inputs": self.final_inputs,
        }
