"""
Template Issue Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict

from gateway.providers.data.models import (
    TemplateIssueDTO,
    TemplateIssueCreateDTO,
    TemplateIssueCommentDTO,
    TemplateIssueCommentCreateDTO,
    PaginatedResponse,
)


class TemplateIssueProvider(ABC):
    """
    Template issue data provider interface.

    Handles issues scoped to individual templates (bug reports, feature requests, questions).
    """

    @abstractmethod
    async def list_issues(
        self,
        template_id: str,
        status: Optional[str] = None,
        issue_type: Optional[str] = None,
        sort: str = "newest",
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """List issues for a template."""
        pass

    @abstractmethod
    async def get_issue(self, issue_id: str) -> Optional[TemplateIssueDTO]:
        """Get a single issue."""
        pass

    @abstractmethod
    async def create_issue(
        self,
        template_id: str,
        author_id: str,
        author_name: str,
        author_avatar: Optional[str],
        data: TemplateIssueCreateDTO,
    ) -> TemplateIssueDTO:
        """Create an issue on a template."""
        pass

    @abstractmethod
    async def update_issue(
        self,
        issue_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        labels: Optional[list] = None,
    ) -> Optional[TemplateIssueDTO]:
        """Update an issue."""
        pass

    @abstractmethod
    async def close_issue(
        self,
        issue_id: str,
        closed_by: str,
    ) -> Optional[TemplateIssueDTO]:
        """Close an issue."""
        pass

    @abstractmethod
    async def reopen_issue(self, issue_id: str) -> Optional[TemplateIssueDTO]:
        """Reopen a closed issue."""
        pass

    @abstractmethod
    async def toggle_upvote(self, issue_id: str, user_id: str) -> Optional[TemplateIssueDTO]:
        """Toggle upvote on an issue."""
        pass

    @abstractmethod
    async def list_comments(
        self,
        issue_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedResponse:
        """List comments for an issue."""
        pass

    @abstractmethod
    async def create_comment(
        self,
        issue_id: str,
        author_id: str,
        author_name: str,
        author_avatar: Optional[str],
        data: TemplateIssueCommentCreateDTO,
    ) -> TemplateIssueCommentDTO:
        """Create a comment on an issue."""
        pass

    @abstractmethod
    async def update_comment(
        self,
        issue_id: str,
        comment_id: str,
        content: str,
    ) -> Optional[TemplateIssueCommentDTO]:
        """Update a comment on an issue."""
        pass

    @abstractmethod
    async def delete_comment(self, issue_id: str, comment_id: str) -> bool:
        """Delete a comment on an issue."""
        pass

    @abstractmethod
    async def toggle_reaction(
        self,
        target_id: str,
        user_id: str,
        reaction_type: str,
        comment_id: Optional[str] = None,
    ) -> Dict[str, List[str]]:
        """Toggle a reaction on an issue or issue comment."""
        pass

    @abstractmethod
    async def update_assignees(
        self,
        issue_id: str,
        assignees: List[Dict[str, str]],
    ) -> Optional[TemplateIssueDTO]:
        """Update assignees on an issue."""
        pass

    @abstractmethod
    async def link_pr(self, issue_id: str, pr_id: str) -> Optional[TemplateIssueDTO]:
        """Link a PR to an issue."""
        pass
