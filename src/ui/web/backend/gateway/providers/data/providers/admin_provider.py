"""
Admin Provider Interface
"""

from abc import ABC, abstractmethod


class AdminProvider(ABC):
    """
    Admin data provider interface.

    Deployment-specific implementations may use hosted, enterprise, or local
    identity and persistence services without exposing them to callers.
    """

    @abstractmethod
    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str = None,
        role: str = None,
        tier: str = None,
    ) -> dict:
        """List all users (admin only)."""
        pass

    @abstractmethod
    async def get_user(
        self,
        user_id: str,
    ) -> dict:
        """Get user details (admin only)."""
        pass

    @abstractmethod
    async def update_user(
        self,
        user_id: str,
        data: dict,
    ) -> dict:
        """Update user (admin only)."""
        pass

    @abstractmethod
    async def sync_auth_users(self) -> dict:
        """Create missing user profiles from the configured identity source."""
        pass

    @abstractmethod
    async def get_config(self) -> dict:
        """Get system configuration."""
        pass

    @abstractmethod
    async def update_config(self, data: dict) -> dict:
        """Update system configuration."""
        pass

    @abstractmethod
    async def get_stats(self) -> dict:
        """Get system-wide statistics."""
        pass

    @abstractmethod
    async def list_templates(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str = None,
    ) -> dict:
        """List all templates (admin view)."""
        pass

    @abstractmethod
    async def update_template(
        self,
        template_id: str,
        data: dict,
    ) -> dict:
        """Update template (admin only)."""
        pass

    @abstractmethod
    async def delete_template(
        self,
        template_id: str,
    ) -> bool:
        """Delete template (admin only)."""
        pass

    @abstractmethod
    async def list_reports(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str = None,
    ) -> dict:
        """List content reports."""
        pass

    @abstractmethod
    async def update_report(
        self,
        report_id: str,
        data: dict,
    ) -> dict:
        """Update report status."""
        pass

    @abstractmethod
    async def list_transactions(
        self,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """List all transactions."""
        pass

    @abstractmethod
    async def list_creators(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """List creators with Stripe Connect status."""
        pass

    @abstractmethod
    async def get_revenue_stats(
        self,
        period: str = "7d",
    ) -> dict:
        """Get revenue statistics for chart."""
        pass

    @abstractmethod
    async def get_recent_activity(
        self,
        limit: int = 10,
    ) -> dict:
        """Get recent admin activity."""
        pass

    @abstractmethod
    async def get_pricing(self) -> dict:
        """Get pricing configuration."""
        pass

    @abstractmethod
    async def update_pricing(self, plans: list) -> dict:
        """Update pricing configuration."""
        pass
