"""
Webhook Models

Enums and data classes for webhook configuration and results.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class WebhookStatus(str, Enum):
    """Webhook status."""

    ACTIVE = "active"
    DISABLED = "disabled"


@dataclass
class Webhook:
    """
    Webhook configuration for triggering workflows.

    Each webhook has a unique secret for signature verification.
    """

    id: str
    name: str
    workflow_id: str
    workflow_name: str = ""
    secret: str = ""  # For HMAC signature

    # Configuration
    status: WebhookStatus = WebhookStatus.ACTIVE
    inputs_mapping: Dict[str, str] = field(default_factory=dict)

    # Security
    require_signature: bool = True
    allowed_ips: List[str] = field(default_factory=list)  # Empty = all allowed
    timestamp_tolerance_seconds: int = 300  # 5 minutes

    # Ownership
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    project_id: Optional[str] = None
    workspace_id: Optional[str] = None  # For Cloud Functions routing

    # Provider (for signature verification)
    provider: Optional[str] = None  # github, stripe, generic

    # Tracking
    trigger_count: int = 0
    last_triggered_at: Optional[str] = None

    # Metadata
    description: Optional[str] = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Webhook":
        """Create a Webhook instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            workflow_id=data.get("workflow_id", ""),
            workflow_name=data.get("workflow_name", ""),
            secret=data.get("secret", ""),
            status=WebhookStatus(data.get("status", "active")),
            inputs_mapping=data.get("inputs_mapping", {}),
            require_signature=data.get("require_signature", True),
            allowed_ips=data.get("allowed_ips", []),
            timestamp_tolerance_seconds=data.get("timestamp_tolerance_seconds", 300),
            user_id=data.get("user_id"),
            organization_id=data.get("organization_id"),
            project_id=data.get("project_id"),
            workspace_id=data.get("workspace_id"),
            provider=data.get("provider"),
            trigger_count=data.get("trigger_count", 0),
            last_triggered_at=data.get("last_triggered_at"),
            description=data.get("description"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )

    def to_dict(self, include_secret: bool = False) -> Dict[str, Any]:
        """Convert webhook to dictionary, optionally including the secret."""
        data = {
            "id": self.id,
            "name": self.name,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "status": self.status.value,
            "inputs_mapping": self.inputs_mapping,
            "require_signature": self.require_signature,
            "allowed_ips": self.allowed_ips,
            "timestamp_tolerance_seconds": self.timestamp_tolerance_seconds,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "project_id": self.project_id,
            "workspace_id": self.workspace_id,
            "provider": self.provider,
            "trigger_count": self.trigger_count,
            "last_triggered_at": self.last_triggered_at,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if include_secret:
            data["secret"] = self.secret
        return data


@dataclass
class WebhookTriggerResult:
    """Result of webhook trigger."""

    success: bool
    execution_id: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert trigger result to dictionary."""
        return {
            "success": self.success,
            "execution_id": self.execution_id,
            "error": self.error,
            "error_code": self.error_code,
        }
