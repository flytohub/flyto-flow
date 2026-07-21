"""
Pydantic validation models and MessageType enum for collaboration WebSocket.
"""

import logging
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration Constants
# ============================================================================

# Lock timeout in seconds (2 minutes)
LOCK_TIMEOUT_SECONDS = 120

# Rate limiting for cursor updates (minimum interval in seconds)
MIN_CURSOR_UPDATE_INTERVAL = 0.05  # 50ms

# Empty room cleanup timeout (5 minutes)
EMPTY_ROOM_TIMEOUT_SECONDS = 300

# Owner grace period: wait before terminating session after owner disconnects
OWNER_GRACE_PERIOD_SECONDS = 20

# Lock expiry check interval (30 seconds)
LOCK_EXPIRY_CHECK_INTERVAL = 30


# ============================================================================
# Message Validation Models (Pydantic)
# ============================================================================


class CursorPosition(BaseModel):
    """Validated cursor position."""
    x: float = Field(..., ge=-10000, le=50000)
    y: float = Field(..., ge=-10000, le=50000)


class CursorMoveMessage(BaseModel):
    """Validated cursor move message."""
    type: str = Field(default="cursor.move")
    x: float = Field(..., ge=-10000, le=50000)
    y: float = Field(..., ge=-10000, le=50000)


class NodeSelectMessage(BaseModel):
    """Validated node select message."""
    type: str = Field(default="node.select")
    node_id: Optional[str] = Field(None, max_length=100)


class NodeEditingMessage(BaseModel):
    """Validated node editing message."""
    type: str = Field(default="node.editing")
    node_id: Optional[str] = Field(None, max_length=100)


class NodeUpdatedMessage(BaseModel):
    """Validated node updated message."""
    type: str = Field(default="node.updated")
    node_id: str = Field(..., max_length=100)
    changes: Optional[dict] = None


class WorkflowUpdatedMessage(BaseModel):
    """Validated workflow updated message."""
    type: str = Field(default="workflow.updated")
    changes: Optional[dict] = None


class LockAcquireMessage(BaseModel):
    """Validated lock acquire message."""
    type: str = Field(default="lock.acquire")
    node_id: str = Field(..., min_length=1, max_length=100)


class LockReleaseMessage(BaseModel):
    """Validated lock release message."""
    type: str = Field(default="lock.release")
    node_id: str = Field(..., min_length=1, max_length=100)


class YjsUpdateMessage(BaseModel):
    """Validated Yjs update message."""
    type: str = Field(default="yjs.update")
    update: List[int] = Field(..., max_length=1000000)  # Max 1MB update


class CommentAddedMessage(BaseModel):
    """Validated comment added message."""
    type: str = Field(default="comment.added")
    comment: dict


def validate_message(msg_type: str, data: dict) -> Optional[BaseModel]:
    """
    Validate incoming WebSocket message based on type.

    Returns validated message model or None if validation fails.
    """
    validators = {
        "cursor.move": CursorMoveMessage,
        "node.select": NodeSelectMessage,
        "node.editing": NodeEditingMessage,
        "node.updated": NodeUpdatedMessage,
        "workflow.updated": WorkflowUpdatedMessage,
        "lock.acquire": LockAcquireMessage,
        "lock.release": LockReleaseMessage,
        "yjs.update": YjsUpdateMessage,
        "comment.added": CommentAddedMessage,
    }

    validator_class = validators.get(msg_type)
    if not validator_class:
        # No validation needed for ping/pong/join/leave
        return None

    try:
        return validator_class(**data)
    except Exception as e:
        logger.warning(f"Message validation failed for {msg_type}: {e}")
        raise ValueError(f"Invalid message format: {e}")


# ============================================================================
# Message Types
# ============================================================================


class MessageType(str, Enum):
    """WebSocket message types."""
    # Connection
    JOIN = "join"
    LEAVE = "leave"
    PING = "ping"
    PONG = "pong"

    # Presence
    PRESENCE_UPDATE = "presence.update"
    PRESENCE_LIST = "presence.list"
    CURSOR_MOVE = "cursor.move"

    # Collaboration
    NODE_SELECT = "node.select"
    NODE_EDITING = "node.editing"
    NODE_UPDATED = "node.updated"
    WORKFLOW_UPDATED = "workflow.updated"

    # Node Locking (CRDT Phase 1)
    LOCK_ACQUIRE = "lock.acquire"
    LOCK_GRANTED = "lock.granted"
    LOCK_DENIED = "lock.denied"
    LOCK_RELEASE = "lock.release"
    LOCK_EXPIRED = "lock.expired"

    # CRDT Sync (Phase 2)
    YJS_UPDATE = "yjs.update"
    YJS_SYNC = "yjs.sync"

    # Chat
    CHAT_MESSAGE = "chat.message"

    # Comments
    COMMENT_ADDED = "comment.added"
    COMMENT_RESOLVED = "comment.resolved"

    # Notifications
    NOTIFICATION = "notification"
    ERROR = "error"
