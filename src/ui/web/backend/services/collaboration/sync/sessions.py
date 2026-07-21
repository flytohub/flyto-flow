"""
Collaboration Session Management

Session creation, joining, and leaving.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from services.collaboration.crdt import CRDTDocument
from services.collaboration.sync.models import (
    CollaborationSession,
    MessageType,
    Participant,
    PresenceState,
)

logger = logging.getLogger(__name__)


class SessionMixin:
    """Mixin for session management methods."""

    async def create_session(
        self,
        workflow_id: str,
        initial_state: Optional[Dict[str, Any]] = None,
    ) -> CollaborationSession:
        """
        Create a new collaboration session.

        Args:
            workflow_id: Associated workflow ID
            initial_state: Initial document state

        Returns:
            New CollaborationSession
        """
        async with self._lock:
            # Check for existing session
            if workflow_id in self._workflow_sessions:
                session_id = self._workflow_sessions[workflow_id]
                return self._sessions[session_id]

            # Create new session
            session_id = f"collab_{workflow_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            document = CRDTDocument(
                document_id=f"doc_{workflow_id}",
                initial_state=initial_state or {},
            )

            session = CollaborationSession(
                session_id=session_id,
                document_id=document.document_id,
                workflow_id=workflow_id,
                document=document,
            )

            self._sessions[session_id] = session
            self._workflow_sessions[workflow_id] = session_id

            logger.info(f"Created collaboration session {session_id} for workflow {workflow_id}")
            return session

    async def join_session(
        self,
        workflow_id: str,
        user_id: str,
        display_name: str,
        avatar_url: Optional[str] = None,
        initial_state: Optional[Dict[str, Any]] = None,
    ) -> Tuple[CollaborationSession, Participant]:
        """
        Join a collaboration session.

        Args:
            workflow_id: Workflow to collaborate on
            user_id: User identifier
            display_name: Display name for participant
            avatar_url: Avatar URL
            initial_state: Initial document state (if creating new)

        Returns:
            Tuple of (session, participant)
        """
        # Get or create session
        session = await self.create_session(workflow_id, initial_state)

        async with self._lock:
            # Check if user already in session
            for p in session.participants.values():
                if p.user_id == user_id:
                    p.presence = PresenceState.ACTIVE
                    p.last_active = datetime.now(timezone.utc).isoformat()
                    return session, p

            # Create new participant
            participant_id = f"p_{user_id}_{len(session.participants)}"
            participant = Participant(
                participant_id=participant_id,
                user_id=user_id,
                display_name=display_name,
                avatar_url=avatar_url,
                color=self._get_next_color(),
            )

            session.participants[participant_id] = participant

        # Broadcast join
        await self._broadcast(session.session_id, {
            "type": MessageType.JOIN.value,
            "participant": participant.to_dict(),
            "participant_count": len(session.participants),
        }, exclude={participant_id})

        logger.info(f"Participant {participant_id} joined session {session.session_id}")
        return session, participant

    async def leave_session(
        self,
        session_id: str,
        participant_id: str,
    ) -> bool:
        """
        Leave a collaboration session.

        Args:
            session_id: Session to leave
            participant_id: Participant leaving

        Returns:
            True if left successfully
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        async with self._lock:
            participant = session.participants.pop(participant_id, None)
            if not participant:
                return False

            # Release any locks held by participant
            locks_to_remove = [
                path for path, pid in session.locks.items()
                if pid == participant_id
            ]
            for path in locks_to_remove:
                del session.locks[path]

            # Remove connections
            self._participant_connections.pop(participant_id, None)

        # Broadcast leave
        await self._broadcast(session_id, {
            "type": MessageType.LEAVE.value,
            "participant_id": participant_id,
            "participant_count": len(session.participants),
            "released_locks": locks_to_remove,
        })

        # Clean up empty sessions
        if not session.participants:
            await self._cleanup_session(session_id)

        logger.info(f"Participant {participant_id} left session {session_id}")
        return True

    async def _cleanup_session(self, session_id: str) -> None:
        """Clean up empty session."""
        async with self._lock:
            session = self._sessions.pop(session_id, None)
            if session:
                self._workflow_sessions.pop(session.workflow_id, None)
        logger.info(f"Cleaned up empty session {session_id}")
