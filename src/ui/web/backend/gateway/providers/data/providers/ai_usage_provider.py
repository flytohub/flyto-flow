"""
AI Usage Provider Interface
"""

from abc import ABC, abstractmethod

from gateway.providers.data.models import (
    AIUsageDTO,
    AIUsageRecordDTO,
    PaginatedResponse,
)


class AIUsageProvider(ABC):
    """
    AI Usage data provider interface.

    Tracks AI token usage per user.
    """

    @abstractmethod
    async def get_usage(
        self,
        user_id: str,
        year: int = None,
        month: int = None,
    ) -> AIUsageDTO:
        """Get user's AI usage for a month."""
        pass

    @abstractmethod
    async def record_usage(
        self,
        data: AIUsageRecordDTO,
    ) -> AIUsageDTO:
        """Record AI usage."""
        pass

    @abstractmethod
    async def check_quota(
        self,
        user_id: str,
        tokens_needed: int,
    ) -> bool:
        """Check if user has enough quota."""
        pass

    @abstractmethod
    async def reset_monthly_usage(
        self,
        user_id: str,
    ) -> AIUsageDTO:
        """Reset user's monthly usage (for new month)."""
        pass

    @abstractmethod
    async def get_usage_stats(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """Get usage statistics (admin)."""
        pass
