"""
Earnings Provider Interface
"""

from abc import ABC, abstractmethod

from gateway.providers.data.models import (
    EarningDTO,
    EarningsSummaryDTO,
    PayoutDTO,
    PaginatedResponse,
)


class EarningsProvider(ABC):
    """
    Earnings data provider interface.

    Handles creator earnings and payouts.
    """

    @abstractmethod
    async def get_earnings_summary(
        self,
        creator_id: str,
    ) -> EarningsSummaryDTO:
        """Get creator's earnings summary."""
        pass

    @abstractmethod
    async def list_earnings(
        self,
        creator_id: str,
        page: int = 1,
        page_size: int = 20,
        status: str = None,
    ) -> PaginatedResponse:
        """List creator's earnings."""
        pass

    @abstractmethod
    async def create_earning(
        self,
        creator_id: str,
        purchase_id: str,
        template_id: str,
        buyer_id: str,
        gross_amount: int,
        platform_fee_percent: float,
    ) -> EarningDTO:
        """Create an earning record."""
        pass

    @abstractmethod
    async def request_payout(
        self,
        creator_id: str,
        amount: int,
    ) -> PayoutDTO:
        """Request a payout."""
        pass

    @abstractmethod
    async def list_payouts(
        self,
        creator_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """List creator's payouts."""
        pass
