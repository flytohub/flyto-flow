"""
Real-time Collaboration WebSocket

Enables real-time collaboration features:
- Presence (who's viewing/editing)
- Live cursor positions
- Real-time updates
- Typing indicators

Re-exports for backward compatibility — external code can continue to use:
    from websocket.collaboration import CollaborationManager
    from websocket.collaboration import collaboration_manager
    from websocket.collaboration import collaboration_websocket_endpoint
"""

from websocket.collaboration.models import (
    MessageType,
    CursorPosition,
    CursorMoveMessage,
    NodeSelectMessage,
    NodeEditingMessage,
    NodeUpdatedMessage,
    WorkflowUpdatedMessage,
    LockAcquireMessage,
    LockReleaseMessage,
    YjsUpdateMessage,
    CommentAddedMessage,
    validate_message,
    LOCK_TIMEOUT_SECONDS,
    MIN_CURSOR_UPDATE_INTERVAL,
    EMPTY_ROOM_TIMEOUT_SECONDS,
    OWNER_GRACE_PERIOD_SECONDS,
    LOCK_EXPIRY_CHECK_INTERVAL,
)

from websocket.collaboration.room import (
    UserPresence,
    NodeLock,
    CollaborationRoom,
)

from websocket.collaboration.manager import (
    CollaborationManager,
    collaboration_manager,
    check_collaboration_access,
    handle_collaboration_websocket,
    collaboration_websocket_endpoint,
)

__all__ = [
    # Constants
    "LOCK_TIMEOUT_SECONDS",
    "MIN_CURSOR_UPDATE_INTERVAL",
    "EMPTY_ROOM_TIMEOUT_SECONDS",
    "OWNER_GRACE_PERIOD_SECONDS",
    "LOCK_EXPIRY_CHECK_INTERVAL",
    # Pydantic models
    "CursorPosition",
    "CursorMoveMessage",
    "NodeSelectMessage",
    "NodeEditingMessage",
    "NodeUpdatedMessage",
    "WorkflowUpdatedMessage",
    "LockAcquireMessage",
    "LockReleaseMessage",
    "YjsUpdateMessage",
    "CommentAddedMessage",
    "validate_message",
    # Enum
    "MessageType",
    # Data models
    "UserPresence",
    "NodeLock",
    "CollaborationRoom",
    # Manager
    "CollaborationManager",
    "collaboration_manager",
    # WebSocket handlers
    "check_collaboration_access",
    "handle_collaboration_websocket",
    "collaboration_websocket_endpoint",
]
