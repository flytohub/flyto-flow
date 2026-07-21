"""
Module Versioning API Routes

Provides REST endpoints for module version management:
- List available versions for a module
- Get latest version
- Set/remove version locks for workflows
- Get workflow locks

Module versions are managed per-workflow to ensure reproducible executions.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# DEPRECATED: Not used by frontend. Retained for potential future use.
router = APIRouter()


# =============================================================================
# Status Endpoint
# =============================================================================


@router.get("/")
async def versioning_status():
    """Get versioning system status."""
    return {
        "ok": True,
        "status": "active",
        "service": "versioning",
        "features": ["version_locks", "module_versions", "update_checks"],
    }


# Storage paths
LOCKS_PATH = Path("./version_locks")
MODULES_PATH = Path("./modules")


def get_locks_path() -> Path:
    """Get locks storage path"""
    import os
    custom_path = os.getenv("FLYTO_LOCKS_PATH")
    if custom_path:
        return Path(custom_path)
    return LOCKS_PATH


def get_modules_path() -> Path:
    """Get modules path"""
    import os
    custom_path = os.getenv("FLYTO_MODULES_PATH")
    if custom_path:
        return Path(custom_path)
    return MODULES_PATH


# =============================================================================
# Response Models
# =============================================================================

class ModuleVersion(BaseModel):
    """Module version info"""
    version: str
    released_at: str
    changelog: Optional[str] = None
    is_stable: bool = True
    dependencies: Dict[str, str] = {}


class VersionLock(BaseModel):
    """Version lock for a module in a workflow"""
    module_id: str
    version: str
    locked_at: str
    locked_by: Optional[str] = None


# =============================================================================
# In-memory storage (would be database in production)
# =============================================================================

# Simulated module versions registry
# In production, this would come from a module registry service
_module_versions: Dict[str, List[Dict[str, Any]]] = {}

# Workflow locks storage
_workflow_locks: Dict[str, Dict[str, str]] = {}


def _load_locks():
    """Load locks from disk"""
    global _workflow_locks
    locks_file = get_locks_path() / "locks.json"
    if locks_file.exists():
        try:
            with open(locks_file, 'r') as f:
                _workflow_locks = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load locks: {e}")
            _workflow_locks = {}


def _save_locks():
    """Save locks to disk"""
    locks_path = get_locks_path()
    locks_path.mkdir(parents=True, exist_ok=True)
    locks_file = locks_path / "locks.json"
    try:
        with open(locks_file, 'w') as f:
            json.dump(_workflow_locks, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save locks: {e}")


def _get_module_versions(module_id: str) -> List[Dict[str, Any]]:
    """Get versions for a module (simulated)"""
    # In production, this would query a module registry
    # For now, return simulated versions based on module ID
    if module_id not in _module_versions:
        # Generate some fake versions for demo
        now = datetime.now(timezone.utc)
        _module_versions[module_id] = [
            {
                "version": "1.0.0",
                "released_at": (now.replace(day=1)).isoformat(),
                "changelog": "Initial release",
                "is_stable": True,
            },
            {
                "version": "1.1.0",
                "released_at": (now.replace(day=10)).isoformat(),
                "changelog": "Added new features",
                "is_stable": True,
            },
            {
                "version": "1.2.0",
                "released_at": now.isoformat(),
                "changelog": "Latest improvements",
                "is_stable": True,
            },
        ]
    return _module_versions[module_id]


# Initialize locks on module load
_load_locks()


# =============================================================================
# Module Version Endpoints
# =============================================================================

@router.get("/modules/{module_id}/versions")
async def list_module_versions(
    module_id: str,
    include_unstable: bool = Query(default=False),
) -> Dict[str, Any]:
    """
    List all versions of a module.

    Returns versions sorted by release date (newest first).
    """
    versions = _get_module_versions(module_id)

    if not include_unstable:
        versions = [v for v in versions if v.get("is_stable", True)]

    # Sort by version (newest first)
    versions = sorted(versions, key=lambda v: v["version"], reverse=True)

    return {
        "module_id": module_id,
        "versions": versions,
        "total": len(versions),
    }


@router.get("/modules/{module_id}/latest")
async def get_latest_version(
    module_id: str,
) -> Dict[str, Any]:
    """
    Get latest stable version of a module.
    """
    versions = _get_module_versions(module_id)
    stable = [v for v in versions if v.get("is_stable", True)]

    if not stable:
        raise HTTPException(status_code=404, detail="No stable versions found")

    # Get latest (highest version number)
    latest = sorted(stable, key=lambda v: v["version"], reverse=True)[0]

    return {
        "module_id": module_id,
        "version": latest["version"],
        "released_at": latest["released_at"],
        "changelog": latest.get("changelog"),
    }


@router.get("/modules/{module_id}/resolve")
async def resolve_version(
    module_id: str,
    constraint: str = Query(..., description="Version constraint (e.g., ^1.0.0, ~1.2.0, >=1.0.0)"),
) -> Dict[str, Any]:
    """
    Resolve a version constraint to a specific version.

    Supports constraints like:
    - ^1.0.0 (compatible with 1.x.x)
    - ~1.2.0 (compatible with 1.2.x)
    - >=1.0.0 (greater than or equal)
    - 1.2.3 (exact version)
    """
    versions = _get_module_versions(module_id)

    # Simple constraint resolution (in production, use a proper semver library)
    if constraint.startswith("^"):
        major = constraint[1:].split(".")[0]
        matching = [v for v in versions if v["version"].startswith(f"{major}.")]
    elif constraint.startswith("~"):
        parts = constraint[1:].split(".")
        prefix = f"{parts[0]}.{parts[1]}."
        matching = [v for v in versions if v["version"].startswith(prefix)]
    elif constraint.startswith(">="):
        target = constraint[2:]
        matching = [v for v in versions if v["version"] >= target]
    else:
        # Exact version
        matching = [v for v in versions if v["version"] == constraint]

    if not matching:
        raise HTTPException(
            status_code=404,
            detail=f"No version matching constraint '{constraint}' found"
        )

    # Return highest matching version
    resolved = sorted(matching, key=lambda v: v["version"], reverse=True)[0]

    return {
        "module_id": module_id,
        "constraint": constraint,
        "resolved_version": resolved["version"],
        "released_at": resolved["released_at"],
    }


@router.get("/modules/{module_id}/versions/{version}/metadata")
async def get_version_metadata(
    module_id: str,
    version: str,
) -> Dict[str, Any]:
    """
    Get metadata for a specific module version.
    """
    versions = _get_module_versions(module_id)
    target = next((v for v in versions if v["version"] == version), None)

    if not target:
        raise HTTPException(status_code=404, detail="Version not found")

    return {
        "module_id": module_id,
        **target,
    }


# =============================================================================
# Workflow Lock Endpoints
# =============================================================================

@router.get("/workflows/{workflow_id}/locks")
async def get_workflow_locks(
    workflow_id: str,
) -> Dict[str, Any]:
    """
    Get all version locks for a workflow.
    """
    locks = _workflow_locks.get(workflow_id, {})

    return {
        "workflow_id": workflow_id,
        "locks": locks,
        "lock_count": len(locks),
    }


@router.post("/workflows/{workflow_id}/locks")
async def set_workflow_lock(
    workflow_id: str,
    module_id: str,
    version: str,
) -> Dict[str, Any]:
    """
    Set a version lock for a module in a workflow.
    """
    # Verify version exists
    versions = _get_module_versions(module_id)
    if not any(v["version"] == version for v in versions):
        raise HTTPException(status_code=404, detail="Version not found")

    # Set lock
    if workflow_id not in _workflow_locks:
        _workflow_locks[workflow_id] = {}

    _workflow_locks[workflow_id][module_id] = version
    _save_locks()

    return {
        "ok": True,
        "workflow_id": workflow_id,
        "module_id": module_id,
        "locked_version": version,
    }


@router.delete("/workflows/{workflow_id}/locks/{module_id}")
async def remove_workflow_lock(
    workflow_id: str,
    module_id: str,
) -> Dict[str, Any]:
    """
    Remove a version lock for a module.
    """
    if workflow_id not in _workflow_locks:
        raise HTTPException(status_code=404, detail="Workflow has no locks")

    if module_id not in _workflow_locks[workflow_id]:
        raise HTTPException(status_code=404, detail="Module is not locked")

    del _workflow_locks[workflow_id][module_id]
    _save_locks()

    return {
        "ok": True,
        "workflow_id": workflow_id,
        "unlocked_module": module_id,
    }


@router.get("/workflows/{workflow_id}/updates")
async def check_updates(
    workflow_id: str,
) -> Dict[str, Any]:
    """
    Check for available updates for locked modules.
    """
    locks = _workflow_locks.get(workflow_id, {})
    updates = []

    for module_id, locked_version in locks.items():
        versions = _get_module_versions(module_id)
        latest = sorted(versions, key=lambda v: v["version"], reverse=True)[0]

        if latest["version"] != locked_version:
            updates.append({
                "module_id": module_id,
                "current_version": locked_version,
                "latest_version": latest["version"],
                "changelog": latest.get("changelog"),
            })

    return {
        "workflow_id": workflow_id,
        "has_updates": len(updates) > 0,
        "updates": updates,
    }
