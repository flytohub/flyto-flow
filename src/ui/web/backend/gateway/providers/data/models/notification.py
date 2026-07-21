"""Notification DTO Models"""

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict


class NotificationType(str, Enum):
    """Notification types"""
    FOLLOW = "follow"
    LIKE = "like"
    COMMENT = "comment"
    PURCHASE = "purchase"
    SYSTEM = "system"
    MESSAGE = "message"
    # Collaboration
    PR_CREATED = "pr_created"
    PR_REVIEWED = "pr_reviewed"
    PR_MERGED = "pr_merged"
    PR_COMMENTED = "pr_commented"
    ISSUE_COMMENTED = "issue_commented"
    ISSUE_CLOSED = "issue_closed"
    # Collaboration requests
    COLLAB_REQUESTED = "collab_requested"
    COLLAB_APPROVED = "collab_approved"
    COLLAB_REJECTED = "collab_rejected"
    # Execution
    EXECUTION_FAILED = "execution_failed"


class NotificationDTO(BaseModel):
    """User notification"""
    id: str
    user_id: str

    # Content
    notification_type: NotificationType
    title: str
    message: str

    # Reference
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None

    # Actor (who triggered the notification)
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    actor_avatar: Optional[str] = None

    # Status
    is_read: bool = False
    read_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime

    model_config = ConfigDict(use_enum_values=True)


class NotificationCreateDTO(BaseModel):
    """DTO for creating a notification"""
    user_id: str
    notification_type: NotificationType
    title: str
    message: str
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    actor_id: Optional[str] = None
