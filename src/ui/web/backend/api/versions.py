"""
Versions API

REST endpoints for workflow versioning.

NOTE: This is an Enterprise-only feature (Phase 9).
Requires VERSIONING_WORKFLOW capability.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from capabilities import Feature, require_feature
from services.versioning.service import VersioningService
from services.versioning.version import VersionSummary

logger = logging.getLogger(__name__)

# All endpoints in this router require LOCAL_VERSIONING feature
router = APIRouter(
    prefix="/workflows",
    tags=["versions"],
    dependencies=[Depends(require_feature(Feature.LOCAL_VERSIONING))],
)


# Request/Response Models

class CreateVersionRequest(BaseModel):
    """Request model for creating a version."""

    definition: Dict[str, Any] = Field(..., description="Workflow definition")
    change_summary: Optional[str] = Field(None, description="Description of changes")
    version_tag: Optional[str] = Field(None, description="Version tag (e.g., v1.2.0)")


class TagVersionRequest(BaseModel):
    """Request model for tagging a version."""

    tag: str = Field(..., description="Version tag")


class DeployVersionRequest(BaseModel):
    """Request model for deploying a version."""

    environment: str = Field(..., description="Target environment")


class PromoteVersionRequest(BaseModel):
    """Request model for promoting a version."""

    from_env: str = Field(..., description="Source environment")
    to_env: str = Field(..., description="Target environment")


class VersionResponse(BaseModel):
    """Response model for a version."""

    id: str
    workflow_id: str
    version_number: int
    version_tag: Optional[str]
    content_hash: str
    definition: Dict[str, Any]
    change_summary: Optional[str]
    created_by: str
    created_at: str
    is_published: bool
    deployed_environments: List[str]


class VersionSummaryResponse(BaseModel):
    """Response model for version summary."""

    id: str
    version_number: int
    version_tag: Optional[str]
    content_hash: str
    change_summary: Optional[str]
    created_by: str
    created_at: str
    is_published: bool
    deployed_environments: List[str]


class DiffResponse(BaseModel):
    """Response model for version diff."""

    version_from: str
    version_to: str
    has_changes: bool
    summary: str
    added_nodes: List[Dict[str, Any]]
    removed_nodes: List[Dict[str, Any]]
    modified_nodes: List[Dict[str, Any]]
    added_edges: List[Dict[str, Any]]
    removed_edges: List[Dict[str, Any]]
    config_changes: List[Dict[str, Any]]


# Endpoints

@router.get("/{workflow_id}/versions", response_model=List[VersionSummaryResponse])
async def list_versions(
    workflow_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum versions to return"),
):
    """List versions for a workflow."""
    versions = VersioningService.list_versions(workflow_id, limit)

    return [
        VersionSummaryResponse(
            id=v.id,
            version_number=v.version_number,
            version_tag=v.version_tag,
            content_hash=v.content_hash,
            change_summary=v.change_summary,
            created_by=v.created_by,
            created_at=v.created_at,
            is_published=v.is_published,
            deployed_environments=v.deployed_environments,
        )
        for v in versions
    ]


@router.get("/{workflow_id}/versions/latest", response_model=VersionResponse)
async def get_latest_version(workflow_id: str):
    """Get the latest version of a workflow."""
    version = VersioningService.get_latest_version(workflow_id)
    if not version:
        raise HTTPException(status_code=404, detail="No versions found")

    return VersionResponse(
        id=version.id,
        workflow_id=version.workflow_id,
        version_number=version.version_number,
        version_tag=version.version_tag,
        content_hash=version.content_hash,
        definition=version.definition,
        change_summary=version.change_summary,
        created_by=version.created_by,
        created_at=version.created_at,
        is_published=version.is_published,
        deployed_environments=version.deployed_environments,
    )


@router.get("/{workflow_id}/versions/{version_id}", response_model=VersionResponse)
async def get_version(workflow_id: str, version_id: str):
    """Get a specific version."""
    version = VersioningService.get_version(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    if version.workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="Version not found for workflow")

    return VersionResponse(
        id=version.id,
        workflow_id=version.workflow_id,
        version_number=version.version_number,
        version_tag=version.version_tag,
        content_hash=version.content_hash,
        definition=version.definition,
        change_summary=version.change_summary,
        created_by=version.created_by,
        created_at=version.created_at,
        is_published=version.is_published,
        deployed_environments=version.deployed_environments,
    )


@router.post("/{workflow_id}/versions", response_model=VersionResponse)
async def create_version(
    workflow_id: str,
    request: CreateVersionRequest,
    user_id: str = Query(..., description="User ID creating the version"),
):
    """Create a new version of a workflow."""
    version = VersioningService.create_version(
        workflow_id=workflow_id,
        definition=request.definition,
        user_id=user_id,
        change_summary=request.change_summary,
        version_tag=request.version_tag,
    )

    return VersionResponse(
        id=version.id,
        workflow_id=version.workflow_id,
        version_number=version.version_number,
        version_tag=version.version_tag,
        content_hash=version.content_hash,
        definition=version.definition,
        change_summary=version.change_summary,
        created_by=version.created_by,
        created_at=version.created_at,
        is_published=version.is_published,
        deployed_environments=version.deployed_environments,
    )


@router.get(
    "/{workflow_id}/versions/{v1}/diff/{v2}",
    response_model=DiffResponse,
)
async def compare_versions(workflow_id: str, v1: str, v2: str):
    """Compare two versions."""
    diff = VersioningService.compare(v1, v2)
    if not diff:
        raise HTTPException(status_code=404, detail="One or both versions not found")

    return DiffResponse(
        version_from=diff.version_from,
        version_to=diff.version_to,
        has_changes=diff.has_changes,
        summary=diff.get_summary(),
        added_nodes=[n.to_dict() for n in diff.added_nodes],
        removed_nodes=[n.to_dict() for n in diff.removed_nodes],
        modified_nodes=[n.to_dict() for n in diff.modified_nodes],
        added_edges=[e.to_dict() for e in diff.added_edges],
        removed_edges=[e.to_dict() for e in diff.removed_edges],
        config_changes=[c.to_dict() for c in diff.config_changes],
    )


@router.post("/{workflow_id}/versions/{version_id}/rollback", response_model=VersionResponse)
async def rollback_version(
    workflow_id: str,
    version_id: str,
    user_id: str = Query(..., description="User ID performing rollback"),
):
    """Rollback to a previous version."""
    version = VersioningService.rollback(
        workflow_id=workflow_id,
        version_id=version_id,
        user_id=user_id,
    )

    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    return VersionResponse(
        id=version.id,
        workflow_id=version.workflow_id,
        version_number=version.version_number,
        version_tag=version.version_tag,
        content_hash=version.content_hash,
        definition=version.definition,
        change_summary=version.change_summary,
        created_by=version.created_by,
        created_at=version.created_at,
        is_published=version.is_published,
        deployed_environments=version.deployed_environments,
    )


@router.post("/{workflow_id}/versions/{version_id}/publish")
async def publish_version(workflow_id: str, version_id: str):
    """Mark a version as published."""
    version = VersioningService.get_version(version_id)
    if not version or version.workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="Version not found")

    success = VersioningService.publish(version_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to publish version")

    return {"ok": True, "message": "Version published"}


@router.post("/{workflow_id}/versions/{version_id}/tag")
async def tag_version(workflow_id: str, version_id: str, request: TagVersionRequest):
    """Tag a version."""
    version = VersioningService.get_version(version_id)
    if not version or version.workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="Version not found")

    success = VersioningService.tag_version(version_id, request.tag)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to tag version")

    return {"ok": True, "message": f"Version tagged as {request.tag}"}


@router.post("/{workflow_id}/versions/{version_id}/deploy")
async def deploy_version(
    workflow_id: str,
    version_id: str,
    request: DeployVersionRequest,
):
    """Deploy a version to an environment."""
    version = VersioningService.get_version(version_id)
    if not version or version.workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="Version not found")

    success = VersioningService.deploy(version_id, request.environment)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to deploy version")

    return {"ok": True, "message": f"Version deployed to {request.environment}"}


@router.post("/{workflow_id}/versions/{version_id}/promote")
async def promote_version(
    workflow_id: str,
    version_id: str,
    request: PromoteVersionRequest,
):
    """Promote a version from one environment to another."""
    version = VersioningService.get_version(version_id)
    if not version or version.workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="Version not found")

    success = VersioningService.promote(
        version_id=version_id,
        from_env=request.from_env,
        to_env=request.to_env,
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Version not deployed to {request.from_env}",
        )

    return {
        "ok": True,
        "message": f"Version promoted from {request.from_env} to {request.to_env}",
    }
