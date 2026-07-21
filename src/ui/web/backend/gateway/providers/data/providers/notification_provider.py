"""
Notification Provider Interface
"""

from abc import ABC, abstractmethod

from gateway.providers.data.models import (
    NotificationDTO,
    NotificationCreateDTO,
    PaginatedResponse,
)


class NotificationProvider(ABC):
    """
    Notification data provider interface.

    Deployment-specific implementations may use hosted, enterprise, or local
    persistence without exposing that storage choice to callers.
    """

    @abstractmethod
    async def list_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """List user's notifications."""
        pass

    @abstractmethod
    async def create_notification(
        self,
        data: NotificationCreateDTO,
    ) -> NotificationDTO:
        """Create notification."""
        pass

    @abstractmethod
    async def mark_as_read(
        self,
        user_id: str,
        notification_id: str,
    ) -> bool:
        """Mark notification as read."""
        pass

    @abstractmethod
    async def mark_all_as_read(
        self,
        user_id: str,
    ) -> int:
        """Mark all notifications as read. Returns count."""
        pass

    @abstractmethod
    async def delete_notification(
        self,
        user_id: str,
        notification_id: str,
    ) -> bool:
        """Delete notification."""
        pass

    @abstractmethod
    async def get_unread_count(
        self,
        user_id: str,
    ) -> int:
        """Get unread notification count."""
        pass
