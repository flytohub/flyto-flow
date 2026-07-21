"""Pull Request DTO Models for Template Collaboration"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PRStatus(str, Enum):
    OPEN = "open"
    MERGED = "merged"
    REJECTED = "rejected"
    CLOSED = "closed"


class PullRequestDTO(BaseModel):
    """Full pull request representation."""
    id: str
    template_id: str
    fork_id: str
    author_id: str
    author_name: str
    author_avatar: Optional[str] = None
    title: str
    description: str = ""
    status: PRStatus = PRStatus.OPEN

    # Draft PR
    is_draft: bool = False

    # Labels
    labels: List[str] = Field(default_factory=list)

    # The fork's complete workflow_data snapshot at PR creation time
    proposed_workflow: Dict[str, Any] = Field(default_factory=dict)

    # Base version the fork was based on
    base_version_number: int = 1

    # Diff summary (computed at creation)
    diff_summary: Dict[str, Any] = Field(default_factory=lambda: {
        "added_steps": [],
        "removed_steps": [],
        "modified_steps": [],
    })

    # Review (legacy single reviewer — kept for backward compatibility)
    reviewed_by: Optional[str] = None
    reviewer_name: Optional[str] = None
    review_comment: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    merged_at: Optional[datetime] = None

    # Multi-reviewer
    reviews: List[Dict[str, Any]] = Field(default_factory=list)
    # [{ reviewer_id, reviewer_name, reviewer_avatar, action, comment, reviewed_at }]

    # Activity timeline
    activity: List[Dict[str, Any]] = Field(default_factory=list)
    # [{ type, actor_id, actor_name, data, created_at }]

    # Comments count
    comment_count: int = 0

    # Linked issues
    linked_issue_ids: List[str] = Field(default_factory=list)

    # Reactions (inline map like upvoters)
    reactions: Dict[str, List[str]] = Field(default_factory=dict)

    created_at: datetime
    updated_at: datetime


class PullRequestCreateDTO(BaseModel):
    """DTO for creating a pull request."""
    fork_id: str
    title: str
    description: str = ""
    is_draft: bool = False
    linked_issue_ids: List[str] = Field(default_factory=list)


class PullRequestSummaryDTO(BaseModel):
    """Lightweight PR for list views."""
    id: str
    template_id: str
    author_id: str
    author_name: str
    author_avatar: Optional[str] = None
    title: str
    status: PRStatus
    is_draft: bool = False
    labels: List[str] = Field(default_factory=list)
    comment_count: int = 0
    diff_summary: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class PRCommentDTO(BaseModel):
    """Comment on a pull request."""
    id: str
    pr_id: str
    author_id: str
    author_name: str
    author_avatar: Optional[str] = None
    content: str
    reactions: Dict[str, List[str]] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None


class PRCommentCreateDTO(BaseModel):
    """DTO for creating a PR comment."""
    content: str
