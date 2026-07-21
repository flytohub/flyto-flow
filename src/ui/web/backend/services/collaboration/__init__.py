"""
Collaboration Services

Real-time collaboration features for workflow editing:
- CRDT-based synchronization
- Presence awareness
- Change tracking
- Conflict resolution
"""

from services.collaboration.crdt import (
    CRDTDocument,
    CRDTOperation,
    OperationType,
    VectorClock,
)

from services.collaboration.sync import (
    CollaborationService,
    CollaborationSession,
    Participant,
    PresenceState,
    get_collaboration_service,
)

from services.collaboration.change_tracker import (
    ChangeTracker,
    Change,
    ChangeType,
    get_change_tracker,
)

__all__ = [
    # CRDT
    "CRDTDocument",
    "CRDTOperation",
    "OperationType",
    "VectorClock",
    # Sync Service
    "CollaborationService",
    "CollaborationSession",
    "Participant",
    "PresenceState",
    "get_collaboration_service",
    # Change Tracker
    "ChangeTracker",
    "Change",
    "ChangeType",
    "get_change_tracker",
]
