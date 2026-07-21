"""
Collaboration Sync Models

Enums and dataclasses for collaboration sessions.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from services.collaboration.crdt import CRDTDocument


class PresenceState(str, Enum):
    """Participant presence states."""
    ACTIVE = "active"
    IDLE = "idle"
    AWAY = "away"
    OFFLINE = "offline"


class MessageType(str, Enum):
    """WebSocket message types."""
    JOIN = "join"
    LEAVE = "leave"
    OPERATION = "operation"
    SYNC_REQUEST = "sync_request"
    SYNC_RESPONSE = "sync_response"
    PRESENCE = "presence"
    CURSOR = "cursor"
    SELECTION = "selection"
    ACK = "ack"
    ERROR = "error"


@dataclass
class CursorPosition:
    """Cursor position in document."""
    path: List[str]
    offset: int = 0
    line: int = 0
    column: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize cursor position to dictionary."""
        return {
            "path": self.path,
            "offset": self.offset,
            "line": self.line,
            "column": self.column,
        }


@dataclass
class Participant:
    """A collaboration session participant."""
    participant_id: str
    user_id: str
    display_name: str
    avatar_url: Optional[str] = None
    color: str = "#3b82f6"
    presence: PresenceState = PresenceState.ACTIVE
    cursor: Optional[CursorPosition] = None
    selection: Optional[Dict[str, Any]] = None
    joined_at: str = ""
    last_active: str = ""

    def __post_init__(self):
        """Set default joined_at and last_active timestamps."""
        if not self.joined_at:
            self.joined_at = datetime.now(timezone.utc).isoformat()
        if not self.last_active:
            self.last_active = self.joined_at

    def to_dict(self) -> Dict[str, Any]:
        """Serialize participant to dictionary."""
        return {
            "participant_id": self.participant_id,
            "user_id": self.user_id,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "color": self.color,
            "presence": self.presence.value,
            "cursor": self.cursor.to_dict() if self.cursor else None,
            "selection": self.selection,
            "joined_at": self.joined_at,
            "last_active": self.last_active,
        }


@dataclass
class CollaborationSession:
    """A collaboration session for a document."""
    session_id: str
    document_id: str
    workflow_id: str
    created_at: str = ""
    participants: Dict[str, Participant] = field(default_factory=dict)
    document: Optional[CRDTDocument] = None
    locks: Dict[str, str] = field(default_factory=dict)  # path -> participant_id

    def __post_init__(self):
        """Set default created_at and initialize CRDT document."""
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if self.document is None:
            self.document = CRDTDocument(document_id=self.document_id)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize collaboration session to dictionary."""
        return {
            "session_id": self.session_id,
            "document_id": self.document_id,
            "workflow_id": self.workflow_id,
            "created_at": self.created_at,
            "participants": {
                pid: p.to_dict() for pid, p in self.participants.items()
            },
            "participant_count": len(self.participants),
            "locks": self.locks,
        }
