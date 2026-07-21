"""
Presence tracking and cursor updates for collaboration rooms.
"""

import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from websocket.collaboration.models import MIN_CURSOR_UPDATE_INTERVAL, MessageType
from websocket.collaboration.room import CollaborationRoom


class PresenceMixin:
    """Mixin for presence tracking and cursor updates."""

    def can_send_cursor_update(self, room: CollaborationRoom, user_id: str) -> bool:
        """Check if user can send cursor update (rate limiting)."""
        now = time.time()
        last_update = room.last_cursor_update.get(user_id, 0)

        if now - last_update < MIN_CURSOR_UPDATE_INTERVAL:
            return False

        room.last_cursor_update[user_id] = now
        return True

    async def update_presence(
        self,
        room: CollaborationRoom,
        user_id: str,
        cursor_x: Optional[float] = None,
        cursor_y: Optional[float] = None,
        selected_node: Optional[str] = None,
        editing_node: Optional[str] = None,
    ) -> None:
        """Update user presence."""
        if user_id not in room.presence:
            return

        presence = room.presence[user_id]
        if cursor_x is not None:
            presence.cursor_x = cursor_x
        if cursor_y is not None:
            presence.cursor_y = cursor_y
        if selected_node is not None:
            presence.selected_node = selected_node
        if editing_node is not None:
            presence.editing_node = editing_node
        presence.last_seen = datetime.now(timezone.utc)

        # Broadcast presence update
        await self.broadcast_to_room(
            room,
            self._msg(MessageType.PRESENCE_UPDATE.value, user=presence.to_dict()),
            exclude_user=user_id,
        )
