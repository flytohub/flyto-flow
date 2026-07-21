"""
Collaboration Sync Package

Real-time collaboration session management.
"""

from services.collaboration.sync.models import (
    PresenceState,
    MessageType,
    CursorPosition,
    Participant,
    CollaborationSession,
)
from services.collaboration.sync.base import CollaborationServiceBase
from services.collaboration.sync.sessions import SessionMixin
from services.collaboration.sync.operations import OperationsMixin
from services.collaboration.sync.presence import PresenceMixin
from services.collaboration.sync.service import CollaborationService, get_collaboration_service

__all__ = [
    # Models
    "PresenceState",
    "MessageType",
    "CursorPosition",
    "Participant",
    "CollaborationSession",
    # Base
    "CollaborationServiceBase",
    # Mixins
    "SessionMixin",
    "OperationsMixin",
    "PresenceMixin",
    # Service
    "CollaborationService",
    "get_collaboration_service",
]
