"""
Collaboration Service

Combined service class with all collaboration functionality.
"""

from typing import Optional

from services.collaboration.sync.base import CollaborationServiceBase
from services.collaboration.sync.operations import OperationsMixin
from services.collaboration.sync.presence import PresenceMixin
from services.collaboration.sync.sessions import SessionMixin


class CollaborationService(
    SessionMixin,
    OperationsMixin,
    PresenceMixin,
    CollaborationServiceBase,
):
    """
    Service for managing real-time collaboration.

    Usage:
        service = CollaborationService()

        # Create or join session
        session = await service.join_session(
            workflow_id="wf_123",
            user_id="user_1",
            display_name="John Doe",
        )

        # Apply operation
        op = service.create_operation(
            session_id=session.session_id,
            participant_id=participant.participant_id,
            operation_type=OperationType.SET,
            path=["steps", 0, "name"],
            value="New Name",
        )
        await service.apply_operation(session.session_id, op)

        # Leave session
        await service.leave_session(session.session_id, participant.participant_id)
    """
    pass


# Global instance
_service: Optional[CollaborationService] = None


def get_collaboration_service() -> CollaborationService:
    """Get or create global collaboration service."""
    global _service
    if _service is None:
        _service = CollaborationService()
    return _service
