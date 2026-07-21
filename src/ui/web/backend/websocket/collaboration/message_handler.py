"""
Message dispatch and processing for collaboration WebSocket.
"""

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import WebSocket

from websocket.collaboration.models import (
    LOCK_EXPIRY_CHECK_INTERVAL,
    MessageType,
    validate_message,
)
from websocket.collaboration.room import CollaborationRoom

logger = logging.getLogger(__name__)


class MessageHandlerMixin:
    """Mixin for WebSocket message dispatch and processing."""

    # =========================================================================
    # Message Handlers (dispatched from run_message_loop)
    # =========================================================================

    async def _handle_ping(
        self,
        websocket: WebSocket,
        room: CollaborationRoom,
        user_id: str,
        data: Dict[str, Any],
        **kwargs,
    ) -> None:
        """Handle ping message."""
        await websocket.send_json(self._msg(MessageType.PONG.value))

    async def _handle_cursor_move(
        self,
        websocket: WebSocket,
        room: CollaborationRoom,
        user_id: str,
        data: Dict[str, Any],
        **kwargs,
    ) -> None:
        """Handle cursor move with rate limiting."""
        if not self.can_send_cursor_update(room, user_id):
            return

        await self.update_presence(
            room,
            user_id,
            cursor_x=data.get("x"),
            cursor_y=data.get("y"),
        )

    async def _handle_node_select(
        self,
        websocket: WebSocket,
        room: CollaborationRoom,
        user_id: str,
        data: Dict[str, Any],
        **kwargs,
    ) -> None:
        """Handle node selection."""
        await self.update_presence(
            room,
            user_id,
            selected_node=data.get("node_id"),
        )

    async def _handle_node_editing(
        self,
        websocket: WebSocket,
        room: CollaborationRoom,
        user_id: str,
        data: Dict[str, Any],
        **kwargs,
    ) -> None:
        """Handle node editing."""
        await self.update_presence(
            room,
            user_id,
            editing_node=data.get("node_id"),
        )

    async def _handle_node_updated(
        self,
        websocket: WebSocket,
        room: CollaborationRoom,
        user_id: str,
        data: Dict[str, Any],
        **kwargs,
    ) -> None:
        """Broadcast node update to others."""
        await self.broadcast_to_room(
            room,
            self._msg(
                MessageType.NODE_UPDATED.value,
                node_id=data.get("node_id"),
                changes=data.get("changes"),
                user_id=user_id,
            ),
            exclude_user=user_id,
        )

    async def _handle_workflow_updated(
        self,
        websocket: WebSocket,
        room: CollaborationRoom,
        user_id: str,
        data: Dict[str, Any],
        **kwargs,
    ) -> None:
        """Broadcast workflow update to others."""
        await self.broadcast_to_room(
            room,
            self._msg(
                MessageType.WORKFLOW_UPDATED.value,
                changes=data.get("changes"),
                user_id=user_id,
            ),
            exclude_user=user_id,
        )

    async def _handle_comment_added(
        self,
        websocket: WebSocket,
        room: CollaborationRoom,
        user_id: str,
        data: Dict[str, Any],
        **kwargs,
    ) -> None:
        """Broadcast new comment."""
        await self.broadcast_to_room(
            room,
            self._msg(
                MessageType.COMMENT_ADDED.value,
                comment=data.get("comment"),
                user_id=user_id,
            ),
        )

    async def _handle_chat_message(
        self,
        websocket: WebSocket,
        room: CollaborationRoom,
        user_id: str,
        data: Dict[str, Any],
        user_name: str = "",
        user_avatar: Optional[str] = None,
        workflow_id: str = "",
        **kwargs,
    ) -> None:
        """Handle persistent chat message."""
        content = (data.get("content") or "").strip()
        if not content or len(content) > 2000:
            return

        # Get sender info from presence
        presence = room.presence.get(user_id)
        sender_name = presence.user_name if presence else user_name
        sender_avatar = presence.user_avatar if presence else user_avatar

        # Persist to Firestore via chat provider.
        # The WebSocket session already authenticated this user, so pass the
        # real sender_id (not the device-owner's captured token) and the full
        # room participant set. Otherwise the cloud endpoint would attribute
        # every message to the device owner and reject guests on history load.
        msg_id = None
        created_at = datetime.now(timezone.utc).isoformat()
        try:
            from services.cloud_client import cloud_post

            conv_id = f"collab_{workflow_id}"
            participant_ids = list(room.presence.keys()) if room.presence else [user_id]
            if user_id not in participant_ids:
                participant_ids.append(user_id)
            result = await cloud_post(
                "chat/messages",
                json={
                    "conversation_id": conv_id,
                    "content": content,
                    "message_type": "text",
                    "sender_id": user_id,
                    "participants": participant_ids,
                },
            )
            if result:
                msg_id = result.get("id") or result.get("message_id")
                created_at = result.get("created_at", created_at)
        except Exception as e:
            logger.error(f"Failed to persist chat message: {e}")
            msg_id = str(uuid.uuid4())

        await self.broadcast_to_room(
            room,
            self._msg(
                MessageType.CHAT_MESSAGE.value,
                message_id=msg_id,
                sender_id=user_id,
                sender_name=sender_name,
                sender_avatar=sender_avatar,
                content=content,
                created_at=created_at,
            ),
        )

    async def _handle_lock_acquire(
        self,
        websocket: WebSocket,
        room: CollaborationRoom,
        user_id: str,
        data: Dict[str, Any],
        **kwargs,
    ) -> None:
        """Handle lock acquisition request."""
        node_id = data.get("node_id")
        if node_id:
            await self.acquire_lock(room, node_id, user_id)

    async def _handle_lock_release(
        self,
        websocket: WebSocket,
        room: CollaborationRoom,
        user_id: str,
        data: Dict[str, Any],
        **kwargs,
    ) -> None:
        """Handle lock release request."""
        node_id = data.get("node_id")
        if node_id:
            await self.release_lock(room, node_id, user_id)

    async def _handle_yjs_update(
        self,
        websocket: WebSocket,
        room: CollaborationRoom,
        user_id: str,
        data: Dict[str, Any],
        **kwargs,
    ) -> None:
        """Handle CRDT (Yjs) update."""
        update_data = data.get("update")
        if not update_data:
            return

        update_bytes = bytes(update_data)
        self.apply_yjs_update(room, update_bytes)
        await self.broadcast_to_room(
            room,
            self._msg(MessageType.YJS_UPDATE.value, update=list(update_bytes)),
            exclude_user=user_id,
        )

    def _get_handler(self, msg_type: str):
        """Return the handler method for a given message type, or None."""
        dispatch = {
            MessageType.PING.value: self._handle_ping,
            MessageType.CURSOR_MOVE.value: self._handle_cursor_move,
            MessageType.NODE_SELECT.value: self._handle_node_select,
            MessageType.NODE_EDITING.value: self._handle_node_editing,
            MessageType.NODE_UPDATED.value: self._handle_node_updated,
            MessageType.WORKFLOW_UPDATED.value: self._handle_workflow_updated,
            MessageType.COMMENT_ADDED.value: self._handle_comment_added,
            MessageType.CHAT_MESSAGE.value: self._handle_chat_message,
            MessageType.LOCK_ACQUIRE.value: self._handle_lock_acquire,
            MessageType.LOCK_RELEASE.value: self._handle_lock_release,
            MessageType.YJS_UPDATE.value: self._handle_yjs_update,
        }
        return dispatch.get(msg_type)

    # =========================================================================
    # Message Loop
    # =========================================================================

    async def run_message_loop(
        self,
        websocket: WebSocket,
        room: CollaborationRoom,
        user_id: str,
        user_name: str,
        user_avatar: Optional[str],
        workflow_id: str,
    ) -> None:
        """Receive, validate, and dispatch WebSocket messages until disconnect."""
        while True:
            try:
                data = await websocket.receive_json()
            except json.JSONDecodeError:
                await self._send_error(websocket, "Invalid JSON format")
                continue

            msg_type = data.get("type")
            if not msg_type:
                await self._send_error(websocket, "Missing message type")
                continue

            # Periodically check for stale locks
            now = time.time()
            if now - room.last_lock_expiry_check >= LOCK_EXPIRY_CHECK_INTERVAL:
                room.last_lock_expiry_check = now
                await self.expire_stale_locks(room)

            room.last_activity = datetime.now(timezone.utc)

            # Validate message
            try:
                validate_message(msg_type, data)
            except ValueError as e:
                await self._send_error(websocket, str(e))
                continue

            # Dispatch to handler
            handler = self._get_handler(msg_type)
            if handler:
                await handler(
                    websocket=websocket,
                    room=room,
                    user_id=user_id,
                    data=data,
                    user_name=user_name,
                    user_avatar=user_avatar,
                    workflow_id=workflow_id,
                )
