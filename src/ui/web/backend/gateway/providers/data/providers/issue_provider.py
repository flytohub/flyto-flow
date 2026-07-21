"""
Issue Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from gateway.providers.data.models import (
    IssueDTO,
    IssueCreateDTO,
    IssueUpdateDTO,
    IssueCommentDTO,
    IssueCommentCreateDTO,
    PaginatedResponse,
)


class IssueProvider(ABC):
    """
    Issue data provider interface.

    Handles public issues (bug reports, feature requests, questions).
    """

    @abstractmethod
    async def list_issues(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str = None,
        issue_type: str = None,
        sort: str = "newest",
    ) -> PaginatedResponse:
        """List issues with optional filters."""
        pass

    @abstractmethod
    async def get_issue(self, issue_id: str) -> Optional[IssueDTO]:
        """Get single issue."""
        pass

    @abstractmethod
    async def create_issue(
        self,
        author_id: str,
        author_name: str,
        author_avatar: Optional[str],
        data: IssueCreateDTO,
    ) -> IssueDTO:
        """Create an issue."""
        pass

    @abstractmethod
    async def update_issue(
        self,
        issue_id: str,
        data: IssueUpdateDTO,
        closed_by: Optional[str] = None,
    ) -> Optional[IssueDTO]:
        """Update an issue."""
        pass

    @abstractmethod
    async def delete_issue(self, issue_id: str) -> bool:
        """Delete an issue."""
        pass

    @abstractmethod
    async def toggle_upvote(self, issue_id: str, user_id: str) -> Optional[IssueDTO]:
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
        data: IssueCommentCreateDTO,
    ) -> IssueCommentDTO:
        """Create a comment on an issue."""
        pass

    @abstractmethod
    async def delete_comment(self, issue_id: str, comment_id: str) -> bool:
        """Delete a comment."""
        pass
