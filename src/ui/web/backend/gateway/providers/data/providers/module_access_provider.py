"""Module access provider interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Set

from gateway.providers.data.models.module_access import AccessType, ModuleAccessDTO


class ModuleAccessProvider(ABC):
    """Provider interface for module access lookups."""

    @abstractmethod
    async def list_user_access(
        self,
        user_id: str,
        access_type: Optional[AccessType] = None,
        include_expired: bool = False,
    ) -> List[ModuleAccessDTO]:
        """List module access records for a user."""
        pass

    @abstractmethod
    async def get_user_module_ids(
        self,
        user_id: str,
        include_expired: bool = False,
    ) -> Set[str]:
        """Return module IDs directly available to a user."""
        pass

    @abstractmethod
    async def get_org_module_ids(
        self,
        organization_id: str,
        include_expired: bool = False,
    ) -> Set[str]:
        """Return module IDs shared with an organization."""
        pass
