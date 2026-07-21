"""
Subscription Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from gateway.providers.data.models import (
    SubscriptionDTO,
    SubscriptionCreateDTO,
    SubscriptionPlan,
    PaginatedResponse,
)


class SubscriptionProvider(ABC):
    """
    Subscription data provider interface.

    Handles user subscription management.
    """

    @abstractmethod
    async def get_subscription(
        self,
        user_id: str,
    ) -> Optional[SubscriptionDTO]:
        """Get user's current subscription."""
        pass

    @abstractmethod
    async def create_subscription(
        self,
        user_id: str,
        data: SubscriptionCreateDTO,
    ) -> SubscriptionDTO:
        """Create a subscription."""
        pass

    @abstractmethod
    async def update_subscription(
        self,
        user_id: str,
        stripe_subscription_id: str,
        status: str,
        cancel_at_period_end: bool = False,
    ) -> Optional[SubscriptionDTO]:
        """Update subscription status."""
        pass

    @abstractmethod
    async def cancel_subscription(
        self,
        user_id: str,
        at_period_end: bool = True,
    ) -> bool:
        """Cancel subscription."""
        pass

    @abstractmethod
    async def list_subscriptions(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str = None,
    ) -> PaginatedResponse:
        """List all subscriptions (admin)."""
        pass

    @abstractmethod
    async def grant_permanent_subscription(
        self,
        user_id: str,
        plan: SubscriptionPlan = SubscriptionPlan.PRO,
        granted_by: str = "admin",
    ) -> SubscriptionDTO:
        """Grant permanent subscription to a user (admin)."""
        pass

    @abstractmethod
    async def list_lifecycle_subscription_candidates(self, limit: int) -> list[dict[str, Any]]:
        """List active/trialing subscription records for lifecycle expiry checks."""
        pass

    @abstractmethod
    async def expire_lifecycle_subscription(
        self,
        subscription_id: str,
        user_id: str | None,
        status: str,
        now_iso: str,
    ) -> None:
        """Mark a subscription expired/cancelled and sync the user's entitlement status."""
        pass

    @abstractmethod
    async def list_trial_expiry_candidates(
        self,
        cutoff_iso: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """List user records whose cloud trial started before the cutoff."""
        pass

    @abstractmethod
    async def flag_trial_expired(self, user_id: str, now_iso: str) -> None:
        """Mark a user's trial as expired for faster future checks."""
        pass

    @abstractmethod
    async def get_user_billing_profile(self, user_id: str) -> dict[str, Any] | None:
        """Get user profile fields needed to create Stripe billing sessions."""
        pass

    @abstractmethod
    async def set_user_stripe_customer_id(self, user_id: str, customer_id: str) -> None:
        """Persist the Stripe customer id for future billing sessions."""
        pass

    @abstractmethod
    async def get_stripe_price_id(self, lookup_key: str) -> str | None:
        """Get a cached Stripe price id by lookup key."""
        pass

    @abstractmethod
    async def set_stripe_price_id(self, lookup_key: str, price_id: str) -> None:
        """Cache a Stripe price id by lookup key."""
        pass

    @abstractmethod
    async def record_flyto_code_pending_checkout(
        self,
        session_id: str,
        session_url: str,
        user_id: str,
        org_id: str,
        sku_id: str,
    ) -> None:
        """Record a pending Flyto2 Code checkout session."""
        pass
