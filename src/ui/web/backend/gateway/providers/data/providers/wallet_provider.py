"""
Wallet Provider Interface

Abstract interface for credit wallet operations.
"""

from abc import ABC, abstractmethod
from typing import Optional

from gateway.providers.data.models.wallet import CreditTransactionType
from gateway.providers.data.models.common import PaginatedResponse


class WalletProvider(ABC):
    """Abstract wallet/credits provider."""

    @abstractmethod
    async def get_balance(self, user_id: str) -> int:
        """Get user's credit balance."""
        pass

    @abstractmethod
    async def add_credits(
        self,
        user_id: str,
        amount: int,
        txn_type: CreditTransactionType,
        template_id: Optional[str] = None,
        template_name: Optional[str] = None,
        note: Optional[str] = None,
    ) -> dict:
        """Add credits to user's balance."""
        pass

    @abstractmethod
    async def deduct_credits(
        self,
        user_id: str,
        amount: int,
        template_id: Optional[str] = None,
        template_name: Optional[str] = None,
    ) -> dict:
        """Deduct credits from user's balance."""
        pass

    @abstractmethod
    async def get_transaction_history(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """Get paginated credit transaction history."""
        pass

    @abstractmethod
    async def record_topup(
        self,
        user_id: str,
        amount: int,
        stripe_session_id: str,
    ) -> dict:
        """Record a credit topup from Stripe."""
        pass
