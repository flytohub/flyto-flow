"""
Audit Entry

Single responsibility: Audit entry data model.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ActorType(str, Enum):
    """Type of actor performing an action."""

    USER = "user"
    SYSTEM = "system"
    WEBHOOK = "webhook"
    SCHEDULER = "scheduler"
    API = "api"


class AuditAction(str, Enum):
    """Types of auditable actions."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    IMPORT = "import"
    PUBLISH = "publish"
    DEPLOY = "deploy"
    ROLLBACK = "rollback"


@dataclass
class AuditEntry:
    """
    Immutable audit log entry.

    Each entry is linked to the previous via hash chain
    to ensure tamper-evidence.
    """

    # Required fields (no defaults) must come first
    id: str
    sequence_number: int  # Monotonic, gap-free per organization
    organization_id: str

    # Actor information (required)
    actor_id: str
    actor_type: ActorType

    # Action information (required)
    action: AuditAction
    resource_type: str  # workflow, template, credential, execution
    resource_id: str

    # Optional fields (with defaults) come after required fields
    actor_ip: Optional[str] = None
    actor_user_agent: Optional[str] = None

    # Change information
    old_value_hash: Optional[str] = None  # Hash of previous state
    new_value_hash: Optional[str] = None  # Hash of new state
    change_summary: Optional[str] = None

    # Integrity fields
    timestamp: Optional[str] = None
    prev_entry_hash: str = ""  # Hash chain link
    entry_hash: str = ""  # SHA-256(sequence + data + prev_hash)

    # Context
    trace_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Default timestamp to current UTC and metadata to empty dict."""
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "sequence_number": self.sequence_number,
            "organization_id": self.organization_id,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type.value if isinstance(self.actor_type, ActorType) else self.actor_type,
            "actor_ip": self.actor_ip,
            "actor_user_agent": self.actor_user_agent,
            "action": self.action.value if isinstance(self.action, AuditAction) else self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "old_value_hash": self.old_value_hash,
            "new_value_hash": self.new_value_hash,
            "change_summary": self.change_summary,
            "timestamp": self.timestamp,
            "prev_entry_hash": self.prev_entry_hash,
            "entry_hash": self.entry_hash,
            "trace_id": self.trace_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEntry":
        """Create from dictionary."""
        actor_type = data.get("actor_type", "user")
        if isinstance(actor_type, str):
            actor_type = ActorType(actor_type)

        action = data.get("action", "read")
        if isinstance(action, str):
            action = AuditAction(action)

        return cls(
            id=data["id"],
            sequence_number=data["sequence_number"],
            organization_id=data["organization_id"],
            actor_id=data["actor_id"],
            actor_type=actor_type,
            actor_ip=data.get("actor_ip"),
            actor_user_agent=data.get("actor_user_agent"),
            action=action,
            resource_type=data["resource_type"],
            resource_id=data["resource_id"],
            old_value_hash=data.get("old_value_hash"),
            new_value_hash=data.get("new_value_hash"),
            change_summary=data.get("change_summary"),
            timestamp=data.get("timestamp"),
            prev_entry_hash=data.get("prev_entry_hash", ""),
            entry_hash=data.get("entry_hash", ""),
            trace_id=data.get("trace_id"),
            metadata=data.get("metadata", {}),
        )

    def get_hashable_content(self) -> str:
        """Get content used for hash computation."""
        parts = [
            str(self.sequence_number),
            self.organization_id,
            self.actor_id,
            self.actor_type.value if isinstance(self.actor_type, ActorType) else self.actor_type,
            self.action.value if isinstance(self.action, AuditAction) else self.action,
            self.resource_type,
            self.resource_id,
            self.timestamp or "",
            self.prev_entry_hash,
        ]

        if self.old_value_hash:
            parts.append(self.old_value_hash)
        if self.new_value_hash:
            parts.append(self.new_value_hash)

        return "|".join(parts)


@dataclass
class AuditQuery:
    """Query parameters for audit log search."""

    organization_id: str
    actor_id: Optional[str] = None
    action: Optional[AuditAction] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    limit: int = 100
    offset: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "organization_id": self.organization_id,
            "limit": self.limit,
            "offset": self.offset,
        }

        if self.actor_id:
            result["actor_id"] = self.actor_id
        if self.action:
            result["action"] = self.action.value if isinstance(self.action, AuditAction) else self.action
        if self.resource_type:
            result["resource_type"] = self.resource_type
        if self.resource_id:
            result["resource_id"] = self.resource_id
        if self.start_time:
            result["start_time"] = self.start_time
        if self.end_time:
            result["end_time"] = self.end_time

        return result
