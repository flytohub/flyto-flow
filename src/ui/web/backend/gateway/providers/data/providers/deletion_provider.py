"""
Deletion Request Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Optional

from gateway.providers.data.models import (
    DeletionRequestDTO,
    DeletionRequestCreateDTO,
    PaginatedResponse,
)


class DeletionRequestProvider(ABC):
    """
    Deletion request data provider interface.

    Handles GDPR-compliant account deletion with 30-day buffer.
    """

    @abstractmethod
    async def create_request(
        self,
        user_id: str,
        email: str,
        data: DeletionRequestCreateDTO,
    ) -> DeletionRequestDTO:
        """Create a deletion request."""
        pass

    @abstractmethod
    async def get_request(
        self,
        user_id: str,
    ) -> Optional[DeletionRequestDTO]:
        """Get user's pending deletion request."""
        pass

    @abstractmethod
    async def cancel_request(
        self,
        user_id: str,
    ) -> bool:
        """Cancel a pending deletion request."""
        pass

    @abstractmethod
    async def list_pending_requests(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """List all pending deletion requests (admin)."""
        pass

    @abstractmethod
    async def process_due_deletions(self) -> int:
        """Process deletions that have passed the 30-day buffer. Returns count."""
        pass

    @abstractmethod
    async def complete_request(
        self,
        request_id: str,
    ) -> bool:
        """Mark a deletion request as completed."""
        pass
