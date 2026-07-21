"""
Payment Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from gateway.providers.data.models import (
    CheckoutSessionDTO,
    PaginatedResponse,
    PayoutSettingsDTO,
)


class PaymentProviderError(RuntimeError):
    """External payment provider rejected or could not complete an operation."""


class PaymentProvider(ABC):
    """
    Payment data provider interface.

    Handles checkout, purchase, refund, and payout operations without exposing
    a deployment-specific payment SDK to callers.
    """

    @abstractmethod
    async def create_checkout_session(
        self,
        user_id: str,
        template_id: str,
        success_url: str,
        cancel_url: str,
    ) -> CheckoutSessionDTO:
        """Create a hosted checkout session."""
        pass

    @abstractmethod
    async def create_credit_topup_session(
        self,
        *,
        user_id: str,
        credits: int,
        price_cents: int,
        success_url: str,
        cancel_url: str,
    ) -> dict[str, Any]:
        """Create a hosted checkout session for a credit top-up."""
        pass

    @abstractmethod
    async def create_subscription_checkout(
        self,
        *,
        user_id: str,
        email: Optional[str],
        display_name: Optional[str],
        customer_id: Optional[str],
        plan_id: str,
        billing_cycle: str,
        price_cents: int,
        cached_price_id: Optional[str],
        success_url: str,
        cancel_url: str,
    ) -> dict[str, Any]:
        """Create a recurring plan checkout without exposing a vendor SDK."""
        pass

    @abstractmethod
    async def create_product_subscription_checkout(
        self,
        *,
        user_id: str,
        email: Optional[str],
        display_name: Optional[str],
        customer_id: Optional[str],
        org_id: str,
        sku_id: str,
        success_url: str,
        cancel_url: str,
    ) -> dict[str, Any]:
        """Create a product/add-on subscription checkout."""
        pass

    @abstractmethod
    async def get_payout_settings(
        self,
        user_id: str,
    ) -> PayoutSettingsDTO:
        """Get user's payout settings."""
        pass

    @abstractmethod
    async def create_connect_account(
        self,
        user_id: str,
        country: str,
        return_url: Optional[str] = None,
        refresh_url: Optional[str] = None,
    ) -> str:
        """Create a payout account and return its onboarding URL."""
        pass

    @abstractmethod
    async def update_connect_account_status(
        self,
        user_id: str,
        stripe_account_id: str,
    ) -> PayoutSettingsDTO:
        """Refresh the external payout account status."""
        pass

    @abstractmethod
    async def process_refund(
        self,
        purchase_id: str,
        buyer_id: str,
        reason: Optional[str] = None,
    ) -> dict:
        """Initiate a Stripe refund for a purchase and revoke library access."""
        pass

    @abstractmethod
    async def list_purchase_history(
        self,
        buyer_id: str,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        refund_window_days: int = 30,
    ) -> PaginatedResponse:
        """List purchase history records for a buyer."""
        pass

    @abstractmethod
    async def check_refund_eligibility(
        self,
        purchase_id: str,
        buyer_id: str,
        refund_window_days: int = 30,
    ) -> dict[str, Any]:
        """Check whether a buyer's purchase is eligible for refund."""
        pass

    @abstractmethod
    async def process_webhook(
        self,
        payload: bytes,
        signature: str,
    ) -> dict:
        """Process a payment-provider webhook."""
        pass
