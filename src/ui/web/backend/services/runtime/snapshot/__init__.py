"""
Execution Snapshot Package

Creates immutable snapshots of execution context for reproducibility.
Captures workflow definition, module versions, environment, and dependencies.
"""

from services.runtime.snapshot.models import (
    WorkflowSnapshot,
    ModuleVersionInfo,
    EnvironmentSnapshot,
    SecretRef,
    ExecutionSnapshot,
    ArtifactInfo,
)
from services.runtime.snapshot.environment import (
    get_environment_snapshot,
    collect_dependencies,
)
from services.runtime.snapshot.service import SnapshotService
from services.runtime.snapshot.artifacts import ArtifactCollector, ARTIFACT_STORAGE_PATH

__all__ = [
    # Models
    "WorkflowSnapshot",
    "ModuleVersionInfo",
    "EnvironmentSnapshot",
    "SecretRef",
    "ExecutionSnapshot",
    "ArtifactInfo",
    # Environment
    "get_environment_snapshot",
    "collect_dependencies",
    # Service
    "SnapshotService",
    # Artifacts
    "ArtifactCollector",
    "ARTIFACT_STORAGE_PATH",
]
