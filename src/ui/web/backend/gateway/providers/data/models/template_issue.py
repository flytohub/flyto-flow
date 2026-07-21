"""Template Issue DTO Models for Template Collaboration"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class TemplateIssueType(str, Enum):
    """Type of template issue."""
    BUG = "bug"
    FEATURE = "feature"
    QUESTION = "question"


class TemplateIssueStatus(str, Enum):
    """Status of a template issue."""
    OPEN = "open"
    CLOSED = "closed"


class TemplateIssueDTO(BaseModel):
    """Full template issue representation."""
    id: str
    template_id: str
    author_id: str
    author_name: str
    author_avatar: Optional[str] = None
    title: str
    description: str = ""
    type: TemplateIssueType = TemplateIssueType.BUG
    status: TemplateIssueStatus = TemplateIssueStatus.OPEN
    labels: List[str] = Field(default_factory=list)
    comment_count: int = 0
    upvotes: int = 0
    upvoters: List[str] = Field(default_factory=list)
    assignees: List[Dict[str, str]] = Field(default_factory=list)
    # [{ user_id, user_name, avatar }]
    linked_pr_ids: List[str] = Field(default_factory=list)
    reactions: Dict[str, List[str]] = Field(default_factory=dict)
    closed_by: Optional[str] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class TemplateIssueCreateDTO(BaseModel):
    """DTO for creating a template issue."""
    title: str
    description: str = ""
    type: TemplateIssueType = TemplateIssueType.BUG
    labels: List[str] = Field(default_factory=list)


class TemplateIssueCommentDTO(BaseModel):
    """Comment on a template issue."""
    id: str
    issue_id: str
    author_id: str
    author_name: str
    author_avatar: Optional[str] = None
    content: str
    reactions: Dict[str, List[str]] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None


class TemplateIssueCommentCreateDTO(BaseModel):
    """DTO for creating a comment on a template issue."""
    content: str
