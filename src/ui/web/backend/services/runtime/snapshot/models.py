"""
Snapshot Data Models

Dataclasses for execution snapshots and artifacts.
"""

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WorkflowSnapshot:
    """Immutable workflow definition snapshot."""

    id: str
    name: str
    version: str
    content_hash: str
    definition: Dict[str, Any]


@dataclass
class ModuleVersionInfo:
    """Module version information."""

    module_id: str
    version: str
    content_hash: str


@dataclass
class EnvironmentSnapshot:
    """Execution environment snapshot."""

    os_name: str
    os_version: str
    python_version: str
    flyto_version: str
    hostname: str
    working_directory: str


@dataclass
class SecretRef:
    """Reference to a secret (no values stored)."""

    name: str
    scope: str
    version: Optional[str] = None


@dataclass
class ExecutionSnapshot:
    """Complete execution snapshot for reproducibility."""

    exec_id: str
    workflow: WorkflowSnapshot
    modules: List[ModuleVersionInfo]
    input_params: Dict[str, Any]
    env: EnvironmentSnapshot
    dependencies_lock: Dict[str, Dict[str, str]]
    secrets_refs: List[SecretRef]
    artifacts: List[Dict[str, Any]]
    trigger: Dict[str, Any]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "exec_id": self.exec_id,
            "workflow": asdict(self.workflow),
            "modules": [asdict(m) for m in self.modules],
            "input_params": self.input_params,
            "env": asdict(self.env),
            "dependencies_lock": self.dependencies_lock,
            "secrets_refs": [asdict(s) for s in self.secrets_refs],
            "artifacts": self.artifacts,
            "trigger": self.trigger,
            "created_at": self.created_at,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


@dataclass
class ArtifactInfo:
    """Information about a stored artifact."""

    id: str
    name: str
    mime_type: str
    size: int
    path: str
    checksum: str
    created_at: str
    node_id: Optional[str] = None
    step_index: Optional[int] = None
