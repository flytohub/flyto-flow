"""
Collaboration Service Base

Base class with shared state and broadcasting.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional, Set

from services.collaboration.sync.models import CollaborationSession

logger = logging.getLogger(__name__)


class CollaborationServiceBase:
    """Base class for collaboration service with shared state."""

    # Participant colors (cycling)
    PARTICIPANT_COLORS = [
        "#3b82f6",  # Blue
        "#10b981",  # Green
        "#f59e0b",  # Amber
        "#ef4444",  # Red
        "#8b5cf6",  # Purple
        "#ec4899",  # Pink
        "#06b6d4",  # Cyan
        "#f97316",  # Orange
    ]

    def __init__(self):
        """Initialize collaboration service."""
        self._sessions: Dict[str, CollaborationSession] = {}
        self._workflow_sessions: Dict[str, str] = {}  # workflow_id -> session_id
        self._participant_connections: Dict[str, Set[Any]] = {}  # participant_id -> websockets
        self._message_handlers: Dict[str, Callable] = {}
        self._color_index = 0
        self._lock = asyncio.Lock()

    def _get_next_color(self) -> str:
        """Get next participant color."""
        color = self.PARTICIPANT_COLORS[self._color_index % len(self.PARTICIPANT_COLORS)]
        self._color_index += 1
        return color

    def get_session(self, session_id: str) -> Optional[CollaborationSession]:
        """Get session by ID."""
        return self._sessions.get(session_id)

    def get_session_by_workflow(self, workflow_id: str) -> Optional[CollaborationSession]:
        """Get session by workflow ID."""
        session_id = self._workflow_sessions.get(workflow_id)
        return self._sessions.get(session_id) if session_id else None

    def register_connection(
        self,
        participant_id: str,
        websocket: Any,
    ) -> None:
        """Register WebSocket connection for participant."""
        if participant_id not in self._participant_connections:
            self._participant_connections[participant_id] = set()
        self._participant_connections[participant_id].add(websocket)

    def unregister_connection(
        self,
        participant_id: str,
        websocket: Any,
    ) -> None:
        """Unregister WebSocket connection."""
        connections = self._participant_connections.get(participant_id)
        if connections:
            connections.discard(websocket)
            if not connections:
                del self._participant_connections[participant_id]

    async def _broadcast(
        self,
        session_id: str,
        message: Dict[str, Any],
        exclude: Optional[Set[str]] = None,
    ) -> None:
        """Broadcast message to all participants in session."""
        session = self._sessions.get(session_id)
        if not session:
            return

        exclude = exclude or set()
        message_json = json.dumps(message)

        for participant_id in session.participants:
            if participant_id in exclude:
                continue

            connections = self._participant_connections.get(participant_id, set())
            for ws in list(connections):
                try:
                    await ws.send_text(message_json)
                except Exception as e:
                    logger.debug(f"Failed to send to {participant_id}: {e}")
                    connections.discard(ws)
