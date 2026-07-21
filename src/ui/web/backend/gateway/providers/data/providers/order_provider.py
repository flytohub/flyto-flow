"""
Order Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Optional

from gateway.providers.data.models import (
    OrderDTO,
    OrderCreateDTO,
    OrderUpdateDTO,
    PaginatedResponse,
)


class OrderProvider(ABC):
    """
    Order data provider interface.

    Handles custom orders between buyers and sellers.
    """

    @abstractmethod
    async def list_orders(
        self,
        user_id: str,
        role: str = "buyer",
        status: str = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """List user's orders."""
        pass

    @abstractmethod
    async def get_order(
        self,
        user_id: str,
        order_id: str,
    ) -> Optional[OrderDTO]:
        """Get single order."""
        pass

    @abstractmethod
    async def create_order(
        self,
        buyer_id: str,
        data: OrderCreateDTO,
    ) -> OrderDTO:
        """Create an order."""
        pass

    @abstractmethod
    async def update_order(
        self,
        user_id: str,
        order_id: str,
        data: OrderUpdateDTO,
    ) -> Optional[OrderDTO]:
        """Update an order."""
        pass

    @abstractmethod
    async def accept_order(
        self,
        seller_id: str,
        order_id: str,
    ) -> Optional[OrderDTO]:
        """Seller accepts an order."""
        pass

    @abstractmethod
    async def deliver_order(
        self,
        seller_id: str,
        order_id: str,
        deliverable_url: str,
        deliverable_notes: str = None,
    ) -> Optional[OrderDTO]:
        """Seller delivers an order."""
        pass

    @abstractmethod
    async def complete_order(
        self,
        buyer_id: str,
        order_id: str,
    ) -> Optional[OrderDTO]:
        """Buyer marks order as completed."""
        pass

    @abstractmethod
    async def cancel_order(
        self,
        user_id: str,
        order_id: str,
        reason: str = None,
    ) -> Optional[OrderDTO]:
        """Cancel an order."""
        pass

    @abstractmethod
    async def list_all_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str = None,
    ) -> PaginatedResponse:
        """List all orders (admin)."""
        pass

    @abstractmethod
    async def get_stats(self) -> dict:
        """Get order statistics (admin)."""
        pass
