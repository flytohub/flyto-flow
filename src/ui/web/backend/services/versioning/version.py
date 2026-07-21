"""
Workflow Version

Single responsibility: Version data model.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class WorkflowVersion:
    """
    Represents a version of a workflow.

    Each version captures the complete state of a workflow
    at a point in time.
    """

    id: str
    workflow_id: str
    version_number: int  # Auto-increment per workflow
    definition: Dict[str, Any]  # Full workflow JSON
    content_hash: str  # SHA-256 of definition
    created_by: str
    created_at: Optional[str] = None
    version_tag: Optional[str] = None  # e.g., "v1.2.0"
    change_summary: Optional[str] = None
    is_published: bool = False
    deployed_environments: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if self.deployed_environments is None:
            self.deployed_environments = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "version_number": self.version_number,
            "version_tag": self.version_tag,
            "content_hash": self.content_hash,
            "definition": self.definition,
            "change_summary": self.change_summary,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "is_published": self.is_published,
            "deployed_environments": self.deployed_environments,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowVersion":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            workflow_id=data["workflow_id"],
            version_number=data["version_number"],
            version_tag=data.get("version_tag"),
            content_hash=data["content_hash"],
            definition=data["definition"],
            change_summary=data.get("change_summary"),
            created_by=data["created_by"],
            created_at=data.get("created_at"),
            is_published=data.get("is_published", False),
            deployed_environments=data.get("deployed_environments", []),
        )

    def get_display_version(self) -> str:
        """Get display version string."""
        if self.version_tag:
            return self.version_tag
        return f"v{self.version_number}"


@dataclass
class VersionSummary:
    """Summary of a version for listing."""

    id: str
    version_number: int
    version_tag: Optional[str]
    content_hash: str
    change_summary: Optional[str]
    created_by: str
    created_at: str
    is_published: bool
    deployed_environments: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "version_number": self.version_number,
            "version_tag": self.version_tag,
            "content_hash": self.content_hash,
            "change_summary": self.change_summary,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "is_published": self.is_published,
            "deployed_environments": self.deployed_environments,
        }

    @classmethod
    def from_version(cls, version: WorkflowVersion) -> "VersionSummary":
        """Create summary from full version."""
        return cls(
            id=version.id,
            version_number=version.version_number,
            version_tag=version.version_tag,
            content_hash=version.content_hash,
            change_summary=version.change_summary,
            created_by=version.created_by,
            created_at=version.created_at,
            is_published=version.is_published,
            deployed_environments=version.deployed_environments,
        )
