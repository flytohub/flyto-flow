"""
Versioning Service

Single responsibility: High-level version operations.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from services.versioning.differ import WorkflowDiff, WorkflowDiffer
from services.versioning.hasher import ContentHasher
from services.versioning.repository import WorkflowVersionRepository
from services.versioning.version import VersionSummary, WorkflowVersion

logger = logging.getLogger(__name__)


class VersioningService:
    """
    High-level workflow versioning operations.

    Orchestrates version creation, comparison, and rollback.
    """

    @staticmethod
    def create_version(
        workflow_id: str,
        definition: Dict[str, Any],
        workspace_id: str,
        change_summary: Optional[str] = None,
        version_tag: Optional[str] = None,
    ) -> WorkflowVersion:
        """
        Create a new version of a workflow.

        Args:
            workflow_id: Workflow ID
            definition: Workflow definition
            workspace_id: ID of user creating version
            change_summary: Optional description of changes
            version_tag: Optional version tag

        Returns:
            Created version
        """
        # Compute content hash
        content_hash = ContentHasher.hash_workflow(definition)

        # Check if identical version exists
        existing = WorkflowVersionRepository.get_by_hash(content_hash)
        if existing and existing.workflow_id == workflow_id:
            logger.info(f"Identical version exists: {existing.id}")
            return existing

        # Get next version number
        version_number = WorkflowVersionRepository.get_next_version_number(workflow_id)

        # Create version
        version = WorkflowVersion(
            id=str(uuid4()),
            workflow_id=workflow_id,
            version_number=version_number,
            definition=definition,
            content_hash=content_hash,
            created_by=workspace_id,
            change_summary=change_summary,
            version_tag=version_tag,
        )

        WorkflowVersionRepository.create(version)
        logger.info(f"Created version {version.id} for workflow {workflow_id}")

        return version

    @staticmethod
    def get_version(version_id: str) -> Optional[WorkflowVersion]:
        """Get a version by ID."""
        return WorkflowVersionRepository.get(version_id)

    @staticmethod
    def get_latest_version(workflow_id: str) -> Optional[WorkflowVersion]:
        """Get the latest version of a workflow."""
        return WorkflowVersionRepository.get_latest(workflow_id)

    @staticmethod
    def list_versions(
        workflow_id: str,
        limit: int = 100,
    ) -> List[VersionSummary]:
        """List versions for a workflow."""
        return WorkflowVersionRepository.list_versions(workflow_id, limit)

    @staticmethod
    def compare(
        version_id_1: str,
        version_id_2: str,
    ) -> Optional[WorkflowDiff]:
        """
        Compare two versions.

        Args:
            version_id_1: First version ID (older)
            version_id_2: Second version ID (newer)

        Returns:
            WorkflowDiff or None if versions not found
        """
        v1 = WorkflowVersionRepository.get(version_id_1)
        v2 = WorkflowVersionRepository.get(version_id_2)

        if not v1 or not v2:
            return None

        return WorkflowDiffer.diff(v1, v2)

    @staticmethod
    def rollback(
        workflow_id: str,
        version_id: str,
        workspace_id: str,
    ) -> Optional[WorkflowVersion]:
        """
        Rollback to a previous version.

        Creates a new version with the content from the target version.

        Args:
            workflow_id: Workflow ID
            version_id: Target version to rollback to
            workspace_id: ID of user performing rollback

        Returns:
            New version or None if target not found
        """
        target = WorkflowVersionRepository.get(version_id)
        if not target:
            logger.warning(f"Rollback target not found: {version_id}")
            return None

        if target.workflow_id != workflow_id:
            logger.warning(f"Version {version_id} belongs to different workflow")
            return None

        # Create new version with target's definition
        new_version = VersioningService.create_version(
            workflow_id=workflow_id,
            definition=target.definition,
            workspace_id=workspace_id,
            change_summary=f"Rollback to version {target.get_display_version()}",
        )

        logger.info(f"Rolled back workflow {workflow_id} to version {version_id}")
        return new_version

    @staticmethod
    def publish(version_id: str) -> bool:
        """Mark a version as published."""
        return WorkflowVersionRepository.publish(version_id)

    @staticmethod
    def promote(
        version_id: str,
        from_env: str,
        to_env: str,
    ) -> bool:
        """
        Promote a version from one environment to another.

        Args:
            version_id: Version ID
            from_env: Source environment
            to_env: Target environment

        Returns:
            True if promoted
        """
        version = WorkflowVersionRepository.get(version_id)
        if not version:
            return False

        # Verify source environment
        if from_env not in version.deployed_environments:
            logger.warning(f"Version not deployed to {from_env}")
            return False

        # Add target environment
        return WorkflowVersionRepository.add_deployment(version_id, to_env)

    @staticmethod
    def deploy(version_id: str, environment: str) -> bool:
        """
        Deploy a version to an environment.

        Args:
            version_id: Version ID
            environment: Target environment

        Returns:
            True if deployed
        """
        return WorkflowVersionRepository.add_deployment(version_id, environment)

    @staticmethod
    def tag_version(version_id: str, tag: str) -> bool:
        """
        Tag a version.

        Args:
            version_id: Version ID
            tag: Version tag (e.g., "v1.2.0")

        Returns:
            True if tagged
        """
        return WorkflowVersionRepository.update(version_id, version_tag=tag)
