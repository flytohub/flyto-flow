"""
Chat Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from gateway.providers.data.models import (
    ConversationDTO,
    ConversationCreateDTO,
    MessageDTO,
    MessageCreateDTO,
    PaginatedResponse,
)


class ChatProvider(ABC):
    """
    Chat data provider interface.

    Deployment-specific implementations may use hosted, enterprise, or local
    persistence without exposing that storage choice to callers.
    """

    @abstractmethod
    async def list_conversations(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """List user's conversations."""
        pass

    @abstractmethod
    async def get_conversation(
        self,
        user_id: str,
        conversation_id: str,
    ) -> Optional[ConversationDTO]:
        """Get single conversation."""
        pass

    @abstractmethod
    async def create_conversation(
        self,
        user_id: str,
        data: ConversationCreateDTO,
    ) -> ConversationDTO:
        """Create new conversation."""
        pass

    @abstractmethod
    async def delete_conversation(
        self,
        user_id: str,
        conversation_id: str,
    ) -> bool:
        """Delete conversation."""
        pass

    @abstractmethod
    async def list_messages(
        self,
        user_id: str,
        conversation_id: str,
        before: str = None,
        limit: int = 50,
    ) -> List[MessageDTO]:
        """List messages in conversation."""
        pass

    @abstractmethod
    async def send_message(
        self,
        user_id: str,
        data: MessageCreateDTO,
        sender_id: Optional[str] = None,
        room_participants: Optional[List[str]] = None,
    ) -> MessageDTO:
        """Send message.

        ``sender_id`` / ``room_participants`` are optional and used only for
        trusted server-to-server collaboration writes, where the real author and
        the full participant set are known from the authenticated session.
        """
        pass

    @abstractmethod
    async def delete_message(
        self,
        user_id: str,
        message_id: str,
    ) -> bool:
        """Delete message."""
        pass

    @abstractmethod
    async def mark_as_read(
        self,
        user_id: str,
        conversation_id: str,
    ) -> bool:
        """Mark all messages in conversation as read."""
        pass
