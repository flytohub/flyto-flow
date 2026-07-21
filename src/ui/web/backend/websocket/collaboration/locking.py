"""
Node lock acquire/release/expiry for collaboration rooms.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from websocket.collaboration.models import LOCK_TIMEOUT_SECONDS, MessageType
from websocket.collaboration.room import CollaborationRoom, NodeLock

logger = logging.getLogger(__name__)


class LockingMixin:
    """Mixin for node locking operations."""

    async def acquire_lock(
        self,
        room: CollaborationRoom,
        node_id: str,
        user_id: str,
    ) -> bool:
        """
        Attempt to acquire a lock on a node.

        Returns True if lock was granted, False if denied.
        """
        now = datetime.now(timezone.utc)
        is_room_owner = (room.owner_id and user_id == room.owner_id)

        if node_id in room.node_locks:
            existing_lock = room.node_locks[node_id]

            # Same user already owns the lock - refresh it
            if existing_lock.user_id == user_id:
                existing_lock.last_activity = now
                return True

            # Owner can override any lock
            if is_room_owner:
                logger.info(f"Owner {user_id} overriding lock on {node_id} held by {existing_lock.user_id}")
                await self.broadcast_to_room(
                    room, self._msg(MessageType.LOCK_RELEASE.value, node_id=node_id),
                )
            elif (now - existing_lock.last_activity).total_seconds() >= LOCK_TIMEOUT_SECONDS:
                # Lock expired, take over
                logger.info(f"Lock on {node_id} expired, granting to {user_id}")
            else:
                # Lock is held by another active user — deny
                await self.send_to_user(
                    room, user_id,
                    self._msg(
                        MessageType.LOCK_DENIED.value,
                        node_id=node_id,
                        owner_id=existing_lock.user_id,
                        owner_name=existing_lock.user_name,
                    ),
                )
                return False

        # Grant the lock
        user_name = room.presence[user_id].user_name if user_id in room.presence else "Unknown"

        room.node_locks[node_id] = NodeLock(
            node_id=node_id,
            user_id=user_id,
            user_name=user_name,
            acquired_at=now,
            last_activity=now,
        )

        await self.broadcast_to_room(
            room,
            self._msg(
                MessageType.LOCK_GRANTED.value,
                node_id=node_id,
                user_id=user_id,
                user_name=user_name,
            ),
        )

        return True

    async def release_lock(
        self,
        room: CollaborationRoom,
        node_id: str,
        user_id: str,
    ) -> bool:
        """
        Release a lock on a node.

        Only the lock owner can release it (or it expires automatically).
        Returns True if lock was released.
        """
        if node_id not in room.node_locks:
            return False

        lock = room.node_locks[node_id]
        if lock.user_id != user_id:
            # Not the owner
            return False

        # Remove the lock
        del room.node_locks[node_id]

        # Broadcast lock release to all users
        await self.broadcast_to_room(
            room,
            self._msg(MessageType.LOCK_RELEASE.value, node_id=node_id, user_id=user_id),
        )

        return True

    async def release_all_user_locks(
        self,
        room: CollaborationRoom,
        user_id: str,
    ) -> None:
        """Release all locks held by a user (called on disconnect)."""
        locks_to_release = [
            node_id for node_id, lock in room.node_locks.items()
            if lock.user_id == user_id
        ]

        for node_id in locks_to_release:
            del room.node_locks[node_id]
            await self.broadcast_to_room(
                room,
                self._msg(MessageType.LOCK_RELEASE.value, node_id=node_id, user_id=user_id),
            )

    async def refresh_lock(
        self,
        room: CollaborationRoom,
        node_id: str,
        user_id: str,
    ) -> bool:
        """Refresh a lock's last_activity timestamp."""
        if node_id not in room.node_locks:
            return False

        lock = room.node_locks[node_id]
        if lock.user_id != user_id:
            return False

        lock.last_activity = datetime.now(timezone.utc)
        return True

    async def expire_stale_locks(self, room: CollaborationRoom) -> None:
        """Check and expire stale locks in a room."""
        now = datetime.now(timezone.utc)
        expired = []

        for node_id, lock in room.node_locks.items():
            elapsed = (now - lock.last_activity).total_seconds()
            if elapsed >= LOCK_TIMEOUT_SECONDS:
                expired.append((node_id, lock.user_id))

        for node_id, user_id in expired:
            del room.node_locks[node_id]
            await self.broadcast_to_room(
                room,
                self._msg(MessageType.LOCK_EXPIRED.value, node_id=node_id, user_id=user_id),
            )
            logger.info(f"Lock on {node_id} by {user_id} expired")
