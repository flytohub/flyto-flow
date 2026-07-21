"""
API Key Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from gateway.providers.data.models import (
    ApiKeyDTO,
    ApiKeyCreateDTO,
    ApiKeyVerifyResult,
    PaginatedResponse,
)


class ApiKeyProvider(ABC):
    """
    API key data provider interface.

    Handles user API keys for programmatic access.
    """

    @abstractmethod
    async def list_user_keys(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """List user's API keys."""
        pass

    @abstractmethod
    async def get_key(
        self,
        user_id: str,
        key_id: str,
    ) -> Dict[str, Any]:
        """Get single key by ID."""
        pass

    @abstractmethod
    async def create_key(
        self,
        user_id: str,
        key_data: Dict[str, Any],
        raw_key: str,
    ) -> Dict[str, Any]:
        """Create an API key."""
        pass

    @abstractmethod
    async def verify_key(
        self,
        api_key: str,
    ) -> ApiKeyVerifyResult:
        """Verify an API key and return associated user info."""
        pass

    @abstractmethod
    async def revoke_key(
        self,
        user_id: str,
        key_id: str,
    ) -> Dict[str, Any]:
        """Revoke an API key."""
        pass

    @abstractmethod
    async def delete_key(
        self,
        user_id: str,
        key_id: str,
    ) -> Dict[str, Any]:
        """Delete an API key."""
        pass

    @abstractmethod
    async def update_last_used(
        self,
        key_id: str,
    ) -> None:
        """Update last_used_at timestamp."""
        pass
