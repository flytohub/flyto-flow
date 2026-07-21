"""Chat DTO Models"""

from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class MessageType(str, Enum):
    """Chat message types"""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"
    ORDER = "order"


class UserBriefDTO(BaseModel):
    """Brief user info for chat participants"""
    id: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class ConversationDTO(BaseModel):
    """Chat conversation"""
    id: str
    participant_ids: List[str]

    # Last message preview
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    last_sender_id: Optional[str] = None

    # Unread count per user
    unread_counts: Dict[str, int] = Field(default_factory=dict)

    # Metadata
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime

    # Enriched fields (populated by API layer)
    current_user_id: Optional[str] = None
    other_user: Optional[UserBriefDTO] = None
    participant_info: Dict[str, UserBriefDTO] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True)


class ConversationCreateDTO(BaseModel):
    """DTO for creating a conversation"""
    participant_ids: List[str]


class MessageDTO(BaseModel):
    """Chat message"""
    id: str
    conversation_id: str
    sender_id: str

    # Sender profile (enriched by API layer)
    sender_name: Optional[str] = None
    sender_avatar: Optional[str] = None

    # Content
    message_type: MessageType = MessageType.TEXT
    content: str

    # Attachments
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_size: Optional[int] = None

    # Order reference (for order messages)
    order_id: Optional[str] = None

    # Read status (list of user IDs who have read this message)
    read_by: List[str] = Field(default_factory=list)
    read_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime

    model_config = ConfigDict(use_enum_values=True)


class MessageCreateDTO(BaseModel):
    """DTO for creating a message"""
    conversation_id: str
    message_type: MessageType = MessageType.TEXT
    content: str
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_size: Optional[int] = None
    order_id: Optional[str] = None
