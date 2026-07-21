"""Issue DTO Models"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, ConfigDict


class IssueType(str, Enum):
    """Issue types"""
    BUG = "bug"
    FEATURE = "feature"
    QUESTION = "question"


class IssueStatus(str, Enum):
    """Issue status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class IssuePriority(str, Enum):
    """Issue priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IssueDTO(BaseModel):
    """Public issue"""
    id: str
    author_id: str
    author_name: str
    author_avatar: Optional[str] = None
    title: str
    description: str
    type: IssueType = IssueType.BUG
    status: IssueStatus = IssueStatus.OPEN
    priority: IssuePriority = IssuePriority.MEDIUM
    labels: List[str] = []
    images: List[str] = []
    comment_count: int = 0
    upvotes: int = 0
    upvoters: List[str] = []
    closed_by: Optional[str] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(use_enum_values=True)


class IssueCreateDTO(BaseModel):
    """DTO for creating an issue"""
    title: str
    description: str
    type: IssueType = IssueType.BUG
    priority: IssuePriority = IssuePriority.MEDIUM
    labels: List[str] = []
    images: List[str] = []


class IssueUpdateDTO(BaseModel):
    """DTO for updating an issue"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[IssueStatus] = None
    priority: Optional[IssuePriority] = None
    labels: Optional[List[str]] = None


class IssueCommentDTO(BaseModel):
    """Issue comment"""
    id: str
    issue_id: str
    author_id: str
    author_name: str
    author_avatar: Optional[str] = None
    content: str
    images: List[str] = []
    created_at: datetime
    updated_at: Optional[datetime] = None


class IssueCommentCreateDTO(BaseModel):
    """DTO for creating an issue comment"""
    content: str
    images: List[str] = []
