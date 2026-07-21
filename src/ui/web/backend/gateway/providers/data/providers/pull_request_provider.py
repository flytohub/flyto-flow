"""
Pull Request Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from gateway.providers.data.models import (
    PullRequestDTO,
    PullRequestSummaryDTO,
    PRCommentDTO,
    PRCommentCreateDTO,
    PaginatedResponse,
)


class PullRequestProvider(ABC):
    """
    Pull request data provider interface.

    Handles template pull requests for collaboration (fork → PR → review → merge).
    """

    @abstractmethod
    async def create_pull_request(
        self,
        template_id: str,
        fork_id: str,
        author_id: str,
        author_name: str,
        author_avatar: Optional[str],
        title: str,
        description: str,
        proposed_workflow: Dict[str, Any],
        base_steps: List[Dict],
        base_version_number: int,
        is_draft: bool = False,
        linked_issue_ids: Optional[List[str]] = None,
    ) -> PullRequestDTO:
        """Create a pull request from a fork."""
        pass

    @abstractmethod
    async def get_pull_request(self, pr_id: str) -> Optional[PullRequestDTO]:
        """Get a single pull request."""
        pass

    @abstractmethod
    async def list_pull_requests(
        self,
        template_id: str,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """List pull requests for a template."""
        pass

    @abstractmethod
    async def review_pull_request(
        self,
        pr_id: str,
        action: str,
        reviewer_id: str,
        reviewer_name: str,
        reviewer_avatar: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> Optional[PullRequestDTO]:
        """Review a pull request (approve or reject)."""
        pass

    @abstractmethod
    async def merge_pull_request(
        self,
        pr_id: str,
        merger_id: str,
        merger_name: str,
        template_versions_provider,
    ) -> Optional[Dict[str, Any]]:
        """Merge a pull request into the target template."""
        pass

    @abstractmethod
    async def close_pull_request(
        self, pr_id: str, actor_id: str = "", actor_name: str = "",
    ) -> Optional[PullRequestDTO]:
        """Close a pull request without merging."""
        pass

    @abstractmethod
    async def reopen_pull_request(
        self, pr_id: str, actor_id: str = "", actor_name: str = "",
    ) -> Optional[PullRequestDTO]:
        """Reopen a closed/rejected pull request."""
        pass

    @abstractmethod
    async def mark_pr_ready(self, pr_id: str) -> Optional[PullRequestDTO]:
        """Mark a draft PR as ready for review."""
        pass

    @abstractmethod
    async def update_pr_labels(self, pr_id: str, labels: List[str]) -> Optional[PullRequestDTO]:
        """Update labels on a PR."""
        pass

    @abstractmethod
    async def list_comments(
        self,
        pr_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedResponse:
        """List comments on a PR."""
        pass

    @abstractmethod
    async def create_comment(
        self,
        pr_id: str,
        author_id: str,
        author_name: str,
        author_avatar: Optional[str],
        data: PRCommentCreateDTO,
    ) -> PRCommentDTO:
        """Create a comment on a PR."""
        pass

    @abstractmethod
    async def update_comment(
        self,
        pr_id: str,
        comment_id: str,
        content: str,
    ) -> Optional[PRCommentDTO]:
        """Update a comment on a PR."""
        pass

    @abstractmethod
    async def delete_comment(self, pr_id: str, comment_id: str) -> bool:
        """Delete a comment on a PR."""
        pass

    @abstractmethod
    async def toggle_reaction(
        self,
        target_id: str,
        user_id: str,
        reaction_type: str,
        comment_id: Optional[str] = None,
    ) -> Dict[str, List[str]]:
        """Toggle a reaction on a PR or PR comment."""
        pass

    @abstractmethod
    async def link_issue(self, pr_id: str, issue_id: str) -> Optional[PullRequestDTO]:
        """Link an issue to a PR."""
        pass
