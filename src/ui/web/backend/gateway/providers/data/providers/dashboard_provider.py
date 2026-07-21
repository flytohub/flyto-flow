"""
Dashboard Provider Interface
"""

from abc import ABC, abstractmethod


class DashboardProvider(ABC):
    """
    Dashboard data provider interface.

    Deployment-specific implementations may use hosted, enterprise, or local
    persistence without exposing that storage choice to callers.
    """

    @abstractmethod
    async def get_stats(
        self,
        user_id: str,
    ) -> dict:
        """Get dashboard statistics."""
        pass

    @abstractmethod
    async def get_sales_trend(
        self,
        user_id: str,
        days: int = 7,
    ) -> dict:
        """Get sales trend data."""
        pass

    @abstractmethod
    async def get_recent_activity(
        self,
        user_id: str,
        limit: int = 10,
    ) -> dict:
        """Get recent activity."""
        pass

    @abstractmethod
    async def get_my_purchases(
        self,
        user_id: str,
        limit: int = 10,
    ) -> dict:
        """Get user's purchase history."""
        pass
