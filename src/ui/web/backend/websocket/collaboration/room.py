"""
Data models for collaboration rooms: UserPresence, NodeLock, CollaborationRoom.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import WebSocket


@dataclass
class UserPresence:
    """User presence information."""
    user_id: str
    user_name: str
    user_avatar: Optional[str] = None
    color: str = "#3B82F6"  # User's assigned color
    cursor_x: Optional[float] = None
    cursor_y: Optional[float] = None
    selected_node: Optional[str] = None
    editing_node: Optional[str] = None
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize user presence to a dictionary."""
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_avatar": self.user_avatar,
            "color": self.color,
            "cursor_x": self.cursor_x,
            "cursor_y": self.cursor_y,
            "selected_node": self.selected_node,
            "editing_node": self.editing_node,
            "last_seen": self.last_seen.isoformat(),
        }


@dataclass
class NodeLock:
    """Lock information for a node."""
    node_id: str
    user_id: str
    user_name: str
    acquired_at: datetime
    last_activity: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Serialize node lock info to a dictionary."""
        return {
            "node_id": self.node_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "acquired_at": self.acquired_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
        }


@dataclass
class CollaborationRoom:
    """A collaboration room for a workflow."""
    workflow_id: str
    organization_id: str
    connections: Dict[str, WebSocket] = field(default_factory=dict)  # user_id -> websocket
    presence: Dict[str, UserPresence] = field(default_factory=dict)  # user_id -> presence
    node_locks: Dict[str, NodeLock] = field(default_factory=dict)  # node_id -> NodeLock
    yjs_state: Optional[bytes] = None  # CRDT state for late joiners
    user_colors: List[str] = field(default_factory=lambda: [
        "#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6",
        "#EC4899", "#06B6D4", "#F97316", "#6366F1", "#14B8A6",
    ])
    color_index: int = 0
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_cursor_update: Dict[str, float] = field(default_factory=dict)  # user_id -> timestamp
    last_lock_expiry_check: float = field(default_factory=time.time)
    owner_id: Optional[str] = None  # Template owner — can override locks
    # Track users who experienced multi-user collaboration (for billing)
    users_with_collaboration: set = field(default_factory=set)  # user_ids who had >1 users in room
    _owner_disconnect_task: Optional[asyncio.Task] = field(default=None, repr=False)

    def get_next_color(self) -> str:
        """Get next available color for a user."""
        color = self.user_colors[self.color_index % len(self.user_colors)]
        self.color_index += 1
        return color

    def get_all_locks(self) -> List[Dict[str, Any]]:
        """Get all current locks as dictionaries."""
        return [lock.to_dict() for lock in self.node_locks.values()]
