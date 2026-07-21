"""
CollaborationManager — manages collaboration rooms, connections, presence,
locking, and CRDT state.

Split into focused modules:
- presence.py  — presence tracking, cursor updates
- locking.py   — node lock acquire/release/expiry
- message_handler.py — message dispatch and processing
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import WebSocket

from websocket.collaboration.models import (
    EMPTY_ROOM_TIMEOUT_SECONDS,
    OWNER_GRACE_PERIOD_SECONDS,
    MessageType,
)
from websocket.collaboration.room import (
    CollaborationRoom,
    UserPresence,
)

from websocket.collaboration.presence import PresenceMixin
from websocket.collaboration.locking import LockingMixin
from websocket.collaboration.message_handler import MessageHandlerMixin

logger = logging.getLogger(__name__)


class CollaborationManager(PresenceMixin, LockingMixin, MessageHandlerMixin):
    """Manages collaboration rooms."""

    def __init__(self):
        """Initialize the collaboration manager with empty room registry."""
        self.rooms: Dict[str, CollaborationRoom] = {}  # workflow_id -> room
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

    @staticmethod
    def _msg(msg_type: str, **fields) -> Dict[str, Any]:
        """Build a typed message dict."""
        return {"type": msg_type, **fields}

    async def _send_error(self, websocket: WebSocket, message: str, code: str = None) -> None:
        """Send error message over WebSocket."""
        payload = {"type": MessageType.ERROR.value, "message": message}
        if code:
            payload["code"] = code
        await websocket.send_json(payload)

    async def start_cleanup_task(self):
        """Start background task for room cleanup."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def stop_cleanup_task(self):
        """Stop the cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _periodic_cleanup(self):
        """Periodically clean up empty rooms."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self.cleanup_empty_rooms()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")

    async def cleanup_empty_rooms(self):
        """Remove rooms that have been empty for too long."""
        async with self._lock:
            now = datetime.now(timezone.utc)
            rooms_to_remove = []

            for room_id, room in self.rooms.items():
                if len(room.connections) == 0:
                    elapsed = (now - room.last_activity).total_seconds()
                    if elapsed > EMPTY_ROOM_TIMEOUT_SECONDS:
                        rooms_to_remove.append(room_id)

            for room_id in rooms_to_remove:
                del self.rooms[room_id]
                logger.info(f"Cleaned up empty room: {room_id}")

    async def cleanup_session_firestore(self, workflow_id: str) -> None:
        """Delete invite codes and clear collaboration_members via cloud API."""
        try:
            from services.cloud_client import cloud_post
            await cloud_post(
                f"collaboration/cleanup/{workflow_id}",
            )
        except Exception as e:
            logger.warning(f"Failed to clean up session data for {workflow_id}: {e}")

    async def terminate_room(self, workflow_id: str, reason: str = "The owner disconnected. Session ended automatically.") -> None:
        """Terminate a collaboration room: broadcast, close connections, clean up Firestore."""
        room = self.rooms.get(workflow_id)
        if not room:
            return
        # Cancel pending grace timer
        if room._owner_disconnect_task and not room._owner_disconnect_task.done():
            room._owner_disconnect_task.cancel()
        # Broadcast session.terminated
        await self.broadcast_to_room(room, self._msg("session.terminated", message=reason))
        # Close all WebSocket connections
        for uid, ws in list(room.connections.items()):
            try:
                await ws.close(code=1000, reason="Session terminated")
            except Exception:
                pass
        # Remove room
        self.rooms.pop(workflow_id, None)
        # Firestore cleanup (invite codes + members)
        await self.cleanup_session_firestore(workflow_id)
        logger.info(f"Terminated collaboration room: {workflow_id}")

    async def get_or_create_room(self, workflow_id: str, organization_id: str) -> CollaborationRoom:
        """Get or create a collaboration room."""
        async with self._lock:
            if workflow_id not in self.rooms:
                self.rooms[workflow_id] = CollaborationRoom(
                    workflow_id=workflow_id,
                    organization_id=organization_id,
                )
            return self.rooms[workflow_id]

    async def join_room(
        self,
        workflow_id: str,
        organization_id: str,
        user_id: str,
        user_name: str,
        websocket: WebSocket,
        user_avatar: Optional[str] = None,
    ) -> CollaborationRoom:
        """Join a collaboration room."""
        room = await self.get_or_create_room(workflow_id, organization_id)

        # Update room activity
        room.last_activity = datetime.now(timezone.utc)

        # Owner reconnecting -> cancel grace period
        if room.owner_id and user_id == room.owner_id:
            if room._owner_disconnect_task and not room._owner_disconnect_task.done():
                room._owner_disconnect_task.cancel()
                room._owner_disconnect_task = None
                logger.info(f"Owner {user_id} reconnected, cancelled grace period for {workflow_id}")

        # Add connection
        room.connections[user_id] = websocket

        # Create presence
        room.presence[user_id] = UserPresence(
            user_id=user_id,
            user_name=user_name,
            user_avatar=user_avatar,
            color=room.get_next_color(),
        )

        # Track multi-user collaboration for billing
        # If there are now 2+ users, mark all of them as having experienced collaboration
        if len(room.presence) > 1:
            for uid in room.presence.keys():
                room.users_with_collaboration.add(uid)

        # Notify others
        await self.broadcast_to_room(
            room,
            self._msg(MessageType.JOIN.value, user=room.presence[user_id].to_dict()),
            exclude_user=user_id,
        )

        # Send current presence list and active locks to the new user
        await self.send_to_user(
            room,
            user_id,
            self._msg(
                MessageType.PRESENCE_LIST.value,
                session_id=workflow_id,
                users=[p.to_dict() for p in room.presence.values()],
                locks=room.get_all_locks(),
            ),
        )

        # Send CRDT state if available
        if room.yjs_state:
            await self.send_to_user(
                room,
                user_id,
                self._msg(MessageType.YJS_SYNC.value, state=list(room.yjs_state)),
            )

        return room

    async def leave_room(self, workflow_id: str, user_id: str) -> None:
        """Leave a collaboration room."""
        if workflow_id not in self.rooms:
            return

        room = self.rooms[workflow_id]

        # Release all locks held by this user
        await self.release_all_user_locks(room, user_id)

        # Remove connection and presence
        if user_id in room.connections:
            del room.connections[user_id]
        if user_id in room.presence:
            del room.presence[user_id]

        # Clean up rate limiting data for this user
        if user_id in room.last_cursor_update:
            del room.last_cursor_update[user_id]

        # Update last activity for empty room cleanup tracking
        room.last_activity = datetime.now(timezone.utc)

        # Owner left with others still connected -> start grace period
        if room.owner_id and user_id == room.owner_id and len(room.connections) > 0:
            async def _owner_grace_timer():
                try:
                    await asyncio.sleep(OWNER_GRACE_PERIOD_SECONDS)
                    await self.terminate_room(workflow_id, "The owner disconnected. Session ended automatically.")
                except asyncio.CancelledError:
                    pass  # Owner reconnected, timer cancelled

            if room._owner_disconnect_task and not room._owner_disconnect_task.done():
                room._owner_disconnect_task.cancel()
            room._owner_disconnect_task = asyncio.create_task(_owner_grace_timer())
            return  # Don't broadcast "leave" -- owner may reconnect

        # Non-owner -> normal broadcast leave
        await self.broadcast_to_room(
            room,
            self._msg(MessageType.LEAVE.value, user_id=user_id),
        )

        # Note: We don't immediately delete empty rooms
        # The periodic cleanup will handle it after EMPTY_ROOM_TIMEOUT_SECONDS

    async def broadcast_to_room(
        self,
        room: CollaborationRoom,
        message: Dict[str, Any],
        exclude_user: Optional[str] = None,
    ) -> None:
        """Broadcast message to all users in room."""
        disconnected = []

        for user_id, websocket in room.connections.items():
            if exclude_user and user_id == exclude_user:
                continue

            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to {user_id}: {e}")
                disconnected.append(user_id)

        # Clean up disconnected users
        for user_id in disconnected:
            await self.leave_room(room.workflow_id, user_id)

    async def send_to_user(
        self,
        room: CollaborationRoom,
        user_id: str,
        message: Dict[str, Any],
    ) -> None:
        """Send message to specific user."""
        if user_id not in room.connections:
            return

        try:
            await room.connections[user_id].send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send to {user_id}: {e}")

    # =========================================================================
    # CRDT State Management (Phase 2)
    # =========================================================================

    def apply_yjs_update(self, room: CollaborationRoom, update: bytes) -> None:
        """Apply a Yjs update to the room's CRDT state."""
        if room.yjs_state is None:
            room.yjs_state = update
        else:
            # In a real implementation, you'd merge the states
            # For now, just keep the latest update
            room.yjs_state = update

    def get_yjs_state(self, room: CollaborationRoom) -> Optional[bytes]:
        """Get the current CRDT state for sync."""
        return room.yjs_state


# Global manager instance
collaboration_manager = CollaborationManager()

# Re-export handler functions from extracted module for backward compatibility
from websocket.collaboration.websocket_handler import (  # noqa: E402, F401
    check_collaboration_access,
    handle_collaboration_websocket,
    collaboration_websocket_endpoint,
)
