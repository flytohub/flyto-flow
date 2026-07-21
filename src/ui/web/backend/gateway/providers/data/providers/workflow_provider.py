"""
Workflow and Template Provider Interfaces
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, List

from gateway.providers.data.models import (
    WorkflowDTO,
    WorkflowCreateDTO,
    WorkflowUpdateDTO,
    TemplateDTO,
    TemplateCreateDTO,
    TemplateUpdateDTO,
    ExecutionDTO,
    PaginatedResponse,
)


class WorkflowProvider(ABC):
    """
    Workflow data provider interface.

    Deployment-specific implementations may use hosted, enterprise, or local
    persistence without exposing that storage choice to callers.
    """

    @abstractmethod
    async def list_user_workflows(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        enabled: bool = None,
    ) -> PaginatedResponse:
        """List workflows owned by user."""
        pass

    @abstractmethod
    async def get_workflow(
        self,
        user_id: str,
        workflow_id: str,
        include_graph: bool = True,
    ) -> Optional[WorkflowDTO]:
        """Get single workflow."""
        pass

    @abstractmethod
    async def create_workflow(
        self,
        user_id: str,
        data: WorkflowCreateDTO,
    ) -> WorkflowDTO:
        """Create new workflow."""
        pass

    @abstractmethod
    async def update_workflow(
        self,
        user_id: str,
        workflow_id: str,
        data: WorkflowUpdateDTO,
    ) -> Optional[WorkflowDTO]:
        """Update existing workflow."""
        pass

    @abstractmethod
    async def delete_workflow(
        self,
        user_id: str,
        workflow_id: str,
    ) -> bool:
        """Delete workflow."""
        pass

    @abstractmethod
    async def execute_workflow(
        self,
        user_id: str,
        workflow_id: str,
        params: dict = None,
    ) -> ExecutionDTO:
        """Execute workflow."""
        pass

    @abstractmethod
    async def list_executions(
        self,
        user_id: str,
        workflow_id: str,
        limit: int = 20,
    ) -> List[ExecutionDTO]:
        """List workflow execution history."""
        pass

    @abstractmethod
    async def get_execution(
        self,
        user_id: str,
        workflow_id: str,
        execution_id: str,
    ) -> Optional[ExecutionDTO]:
        """Get single execution."""
        pass

    @abstractmethod
    async def update_execution(
        self,
        user_id: str,
        workflow_id: str,
        execution_id: str,
        status: str,
        result_data: dict = None,
        error_message: str = None,
        finished_at: str = None,
        duration_ms: int = None,
    ) -> bool:
        """Update execution status and result."""
        pass


class TemplateNotFoundError(Exception):
    """Raised when a template does not exist."""

    def __init__(self, template_id: str):
        self.template_id = template_id
        super().__init__(f"Template {template_id} not found")


class TemplateOwnershipError(Exception):
    """Raised when the user is not the owner of the template."""

    def __init__(self, template_id: str, user_id: str):
        self.template_id = template_id
        self.user_id = user_id
        super().__init__(f"User {user_id} is not the owner of template {template_id}")


class TemplateRevisionConflictError(Exception):
    """Raised when optimistic locking detects a revision mismatch."""

    def __init__(self, template_id: str, expected: str, current: str):
        self.template_id = template_id
        self.expected_revision = expected
        self.current_revision = current
        super().__init__(
            f"Template {template_id} revision conflict: "
            f"expected={expected}, current={current}"
        )


class TemplateProvider(ABC):
    """
    Template data provider interface.

    Deployment-specific implementations may use hosted, enterprise, or local
    persistence without exposing that storage choice to callers.
    """

    @abstractmethod
    async def list_user_templates(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """List templates owned by user (my-templates)."""
        pass

    @abstractmethod
    async def list_public_templates(
        self,
        category: str = None,
        tags: List[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """List public/marketplace templates."""
        pass

    @abstractmethod
    async def get_template(
        self,
        template_id: str,
        user_id: str = None,
    ) -> Optional[TemplateDTO]:
        """Get single template."""
        pass

    async def get_template_internal(
        self,
        template_id: str,
    ) -> Optional[TemplateDTO]:
        """Get template without visibility enforcement.

        For trusted server-side use only (e.g. invite key redemption).
        Default implementation delegates to get_template without user_id.
        """
        return await self.get_template(template_id)

    async def find_template_by_id_prefix(self, code: str) -> Optional[TemplateDTO]:
        """Find a template by ID prefix (for collaboration invite code resolution).

        Default returns None. Hosted providers may override with an actual lookup.
        """
        return None

    async def user_has_library_access(self, user_id: str, template_id: str) -> bool:
        """Check if user has library access to a template (via invite key, install, purchase).

        Default returns False. Hosted providers may override with an actual library check.
        Enterprise overrides with True (access control delegated to backend).
        """
        return False

    async def get_library_entry(self, user_id: str, template_id: str) -> Optional[dict]:
        """Return a user's saved library entry for a template, if present."""
        return None

    async def update_library_item_settings(
        self,
        user_id: str,
        library_id: str,
        folder_id: Optional[str] = None,
        auto_update: Optional[str] = None,
    ) -> bool:
        """Update settings for a library, purchase, or fork item."""
        return False

    async def update_template_merge_settings(
        self,
        user_id: str,
        template_id: str,
        require_approval: bool,
        min_reviewers: int,
    ) -> bool:
        """Update merge-protection settings for a template."""
        return False

    async def sync_fork_with_upstream(
        self,
        user_id: str,
        fork_id: str,
        source_template: TemplateDTO,
    ) -> bool:
        """Sync a fork with an already authorized source template snapshot."""
        return False

    @abstractmethod
    async def create_template(
        self,
        user_id: str,
        data: TemplateCreateDTO,
    ) -> TemplateDTO:
        """Create new template."""
        pass

    @abstractmethod
    async def update_template(
        self,
        user_id: str,
        template_id: str,
        data: TemplateUpdateDTO,
    ) -> Optional[TemplateDTO]:
        """Update template."""
        pass

    @abstractmethod
    async def delete_template(
        self,
        user_id: str,
        template_id: str,
    ) -> bool:
        """Delete template."""
        pass

    @abstractmethod
    async def execute_template(
        self,
        user_id: str,
        template_id: str,
        params: dict = None,
    ) -> ExecutionDTO:
        """Execute template."""
        pass

    async def update_template_schemas(
        self,
        template_id: str,
        schemas: dict,
    ) -> bool:
        """Update computed schemas (output_schema, params_schema) on a template.

        Used after PR merge or other operations that change template content.
        Authorization must be verified by the caller.
        """
        return False

    async def update_marketplace_snapshot(
        self,
        user_id: str,
        template_id: str,
    ) -> bool:
        """
        Explicitly update marketplace snapshot from current live template.

        This syncs pending changes to the marketplace without requiring republish.
        Only applicable when the active provider supports marketplace snapshots.

        Returns:
            True if snapshot was updated, False otherwise.
        """
        # Default implementation for offline/enterprise modes
        return False

    async def list_auto_update_user_ids(self) -> list[str]:
        """List users with at least one purchased template auto-update enabled."""
        return []

    async def list_purchased_template_records(
        self,
        user_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """List raw purchased-template records for auto-update tasks."""
        return []

    async def get_template_update_source(self, template_id: str) -> Optional[dict[str, Any]]:
        """Return the latest raw template data used as an auto-update source."""
        return None

    async def get_latest_template_version_id(self, template_id: str) -> Optional[str]:
        """Return the latest version id for a template, if available."""
        return None

    async def update_purchased_template_record(
        self,
        user_id: str,
        purchase_id: str,
        updates: dict[str, Any],
    ) -> bool:
        """Apply provider-owned updates to a purchased-template record."""
        return False
