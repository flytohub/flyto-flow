"""
Collaboration Presence Management

Presence, cursor, selection, and lock management.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from services.collaboration.sync.models import CursorPosition, MessageType, PresenceState

logger = logging.getLogger(__name__)


class PresenceMixin:
    """Mixin for presence and lock management methods."""

    async def update_presence(
        self,
        session_id: str,
        participant_id: str,
        presence: PresenceState,
    ) -> None:
        """Update participant presence."""
        session = self._sessions.get(session_id)
        if not session:
            return

        participant = session.participants.get(participant_id)
        if participant:
            participant.presence = presence
            participant.last_active = datetime.now(timezone.utc).isoformat()

            await self._broadcast(session_id, {
                "type": MessageType.PRESENCE.value,
                "participant_id": participant_id,
                "presence": presence.value,
            }, exclude={participant_id})

    async def update_cursor(
        self,
        session_id: str,
        participant_id: str,
        cursor: CursorPosition,
    ) -> None:
        """Update participant cursor position."""
        session = self._sessions.get(session_id)
        if not session:
            return

        participant = session.participants.get(participant_id)
        if participant:
            participant.cursor = cursor
            participant.last_active = datetime.now(timezone.utc).isoformat()

            await self._broadcast(session_id, {
                "type": MessageType.CURSOR.value,
                "participant_id": participant_id,
                "cursor": cursor.to_dict(),
            }, exclude={participant_id})

    async def update_selection(
        self,
        session_id: str,
        participant_id: str,
        selection: Dict[str, Any],
    ) -> None:
        """Update participant selection."""
        session = self._sessions.get(session_id)
        if not session:
            return

        participant = session.participants.get(participant_id)
        if participant:
            participant.selection = selection

            await self._broadcast(session_id, {
                "type": MessageType.SELECTION.value,
                "participant_id": participant_id,
                "selection": selection,
            }, exclude={participant_id})

    async def acquire_lock(
        self,
        session_id: str,
        participant_id: str,
        path: str,
    ) -> bool:
        """
        Acquire edit lock on a path.

        Args:
            session_id: Session ID
            participant_id: Participant requesting lock
            path: Path to lock

        Returns:
            True if lock acquired
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        async with self._lock:
            # Check for existing lock
            existing = session.locks.get(path)
            if existing and existing != participant_id:
                return False

            session.locks[path] = participant_id

        await self._broadcast(session_id, {
            "type": "lock_acquired",
            "participant_id": participant_id,
            "path": path,
        })

        return True

    async def release_lock(
        self,
        session_id: str,
        participant_id: str,
        path: str,
    ) -> bool:
        """Release edit lock."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        async with self._lock:
            if session.locks.get(path) == participant_id:
                del session.locks[path]

        await self._broadcast(session_id, {
            "type": "lock_released",
            "participant_id": participant_id,
            "path": path,
        })

        return True
