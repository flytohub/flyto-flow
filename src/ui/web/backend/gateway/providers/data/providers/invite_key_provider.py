"""
Invite Key Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from gateway.providers.data.models import (
    InviteKeyDTO,
    InviteKeyCreateDTO,
    InviteKeyBatchCreateDTO,
    InviteKeyStatsDTO,
    PaginatedResponse,
)


class InviteKeyProvider(ABC):
    """
    Invite key data provider interface.

    Handles invitation codes for early access.
    """

    @abstractmethod
    async def list_keys(
        self,
        creator_id: str = None,
        page: int = 1,
        page_size: int = 20,
        campaign: str = None,
    ) -> PaginatedResponse:
        """List invite keys."""
        pass

    @abstractmethod
    async def get_key(
        self,
        key_id: str,
    ) -> Optional[InviteKeyDTO]:
        """Get single key by ID."""
        pass

    @abstractmethod
    async def get_by_code(
        self,
        key: str,
    ) -> Optional[InviteKeyDTO]:
        """Get key by code string."""
        pass

    @abstractmethod
    async def create_key(
        self,
        creator_id: str,
        data: InviteKeyCreateDTO,
    ) -> InviteKeyDTO:
        """Create an invite key."""
        pass

    @abstractmethod
    async def create_batch(
        self,
        creator_id: str,
        data: InviteKeyBatchCreateDTO,
    ) -> List[InviteKeyDTO]:
        """Batch create invite keys."""
        pass

    @abstractmethod
    async def use_key(
        self,
        key: str,
        user_id: str,
    ) -> bool:
        """Use an invite key."""
        pass

    @abstractmethod
    async def revoke_key(
        self,
        key_id: str,
    ) -> bool:
        """Revoke an invite key."""
        pass

    @abstractmethod
    async def get_stats(
        self,
        campaign: str = None,
    ) -> InviteKeyStatsDTO:
        """Get invite key statistics."""
        pass

    async def deactivate_keys_for_template(
        self,
        template_id: str,
    ) -> int:
        """Deactivate all active invite keys for a template. Returns count of deactivated keys.

        Default returns 0. Firebase overrides with actual batch deactivation.
        """
        return 0
