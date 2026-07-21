"""
Collaboration Operations

Operation creation, application, sync, undo/redo.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.collaboration.crdt import CRDTOperation, OperationType, VectorClock
from services.collaboration.sync.models import MessageType

logger = logging.getLogger(__name__)


class OperationsMixin:
    """Mixin for operation management methods."""

    def create_operation(
        self,
        session_id: str,
        participant_id: str,
        operation_type: OperationType,
        path: List[str],
        value: Any = None,
    ) -> Optional[CRDTOperation]:
        """
        Create an operation for a session.

        Args:
            session_id: Session ID
            participant_id: Participant creating operation
            operation_type: Type of operation
            path: JSON path
            value: New value

        Returns:
            CRDTOperation or None
        """
        session = self._sessions.get(session_id)
        if not session or not session.document:
            return None

        return session.document.create_operation(
            operation_type=operation_type,
            path=path,
            value=value,
            participant_id=participant_id,
        )

    async def apply_operation(
        self,
        session_id: str,
        operation: CRDTOperation,
    ) -> bool:
        """
        Apply an operation and broadcast to other participants.

        Args:
            session_id: Session ID
            operation: Operation to apply

        Returns:
            True if applied successfully
        """
        session = self._sessions.get(session_id)
        if not session or not session.document:
            return False

        # Check lock
        path_str = ".".join(str(p) for p in operation.path)
        for locked_path, lock_holder in session.locks.items():
            if path_str.startswith(locked_path) and lock_holder != operation.participant_id:
                logger.warning(f"Operation blocked: path {path_str} locked by {lock_holder}")
                return False

        # Apply operation
        success = session.document.apply_operation(operation)

        if success:
            # Update participant activity
            participant = session.participants.get(operation.participant_id)
            if participant:
                participant.last_active = datetime.now(timezone.utc).isoformat()

            # Broadcast to others
            await self._broadcast(session_id, {
                "type": MessageType.OPERATION.value,
                "operation": operation.to_dict(),
            }, exclude={operation.participant_id})

        return success

    async def sync_document(
        self,
        session_id: str,
        participant_id: str,
        since_clock: Optional[Dict[str, int]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get document state and operations for sync.

        Args:
            session_id: Session ID
            participant_id: Requesting participant
            since_clock: Vector clock to sync from

        Returns:
            Sync response with state and operations
        """
        session = self._sessions.get(session_id)
        if not session or not session.document:
            return None

        clock = VectorClock.from_dict(since_clock) if since_clock else None
        operations = session.document.get_operations(since_clock=clock)

        return {
            "type": MessageType.SYNC_RESPONSE.value,
            "state": session.document.get_state(),
            "vector_clock": session.document.get_vector_clock().to_dict(),
            "operations": [op.to_dict() for op in operations],
            "participants": {
                pid: p.to_dict() for pid, p in session.participants.items()
            },
            "locks": session.locks,
        }

    async def undo(
        self,
        session_id: str,
        participant_id: str,
    ) -> Optional[CRDTOperation]:
        """Undo last operation by participant."""
        session = self._sessions.get(session_id)
        if not session or not session.document:
            return None

        inverse = session.document.undo(participant_id)
        if inverse:
            await self._broadcast(session_id, {
                "type": MessageType.OPERATION.value,
                "operation": inverse.to_dict(),
                "is_undo": True,
            })

        return inverse

    async def redo(
        self,
        session_id: str,
        participant_id: str,
    ) -> Optional[CRDTOperation]:
        """Redo last undone operation by participant."""
        session = self._sessions.get(session_id)
        if not session or not session.document:
            return None

        op = session.document.redo(participant_id)
        if op:
            await self._broadcast(session_id, {
                "type": MessageType.OPERATION.value,
                "operation": op.to_dict(),
                "is_redo": True,
            })

        return op
