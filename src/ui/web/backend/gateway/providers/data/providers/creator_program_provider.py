"""Creator program data provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class CreatorProgramProvider(ABC):
    """Provider interface for creator applications and creator profile flags."""

    @abstractmethod
    async def count_approved_campaign(self, campaign: str) -> int:
        """Count approved creator applications for a campaign."""
        pass

    @abstractmethod
    async def get_user_application(self, user_id: str) -> Optional[dict[str, Any]]:
        """Return the first creator application for a user."""
        pass

    @abstractmethod
    async def save_application(
        self,
        application_data: dict[str, Any],
        *,
        application_id: Optional[str] = None,
    ) -> str:
        """Create or replace a creator application and return its id."""
        pass

    @abstractmethod
    async def set_creator_flag(self, user_id: str, is_creator: bool = True) -> None:
        """Set the creator flag on a user profile."""
        pass

    @abstractmethod
    async def list_applications(
        self,
        *,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """List creator applications with pagination metadata."""
        pass

    @abstractmethod
    async def get_application(self, application_id: str) -> Optional[dict[str, Any]]:
        """Return a creator application by id."""
        pass

    @abstractmethod
    async def update_application(
        self,
        application_id: str,
        update_data: dict[str, Any],
    ) -> None:
        """Update fields on a creator application."""
        pass
