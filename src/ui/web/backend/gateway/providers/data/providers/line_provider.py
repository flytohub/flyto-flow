"""LINE data provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class LineProvider(ABC):
    """Provider interface for LINE message queue and conversation state."""

    @abstractmethod
    async def list_pending_messages(
        self,
        *,
        user_id: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Return pending LINE messages for desktop processing."""
        pass

    @abstractmethod
    async def claim_message(self, message_id: str, device_id: str) -> dict[str, Any]:
        """Claim a pending LINE message for a desktop device."""
        pass

    @abstractmethod
    async def complete_message(self, message_id: str) -> dict[str, Any]:
        """Mark a LINE message as completed."""
        pass

    @abstractmethod
    async def get_conversation_state(self, user_id: str) -> dict[str, Any]:
        """Return conversation state for a LINE user."""
        pass

    @abstractmethod
    async def update_conversation_state(
        self,
        user_id: str,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        """Persist conversation state for a LINE user."""
        pass

    @abstractmethod
    async def store_incoming_message(
        self,
        *,
        user_id: str,
        message: dict[str, Any],
        user_update: dict[str, Any],
    ) -> str:
        """Store an incoming LINE message and update user activity metadata."""
        pass
