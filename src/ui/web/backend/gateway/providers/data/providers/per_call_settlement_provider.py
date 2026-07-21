"""Per-call settlement provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class PerCallSettlementProvider(ABC):
    """Provider interface for per-call execution settlement side effects."""

    @abstractmethod
    async def record_earning(
        self,
        creator_id: str,
        buyer_id: str,
        template_id: str,
        template_name: str,
        call_price: int,
        status: str = "pending",
        execution_id: str | None = None,
        credit_transaction_id: str | None = None,
    ) -> dict[str, Any]:
        """Record the initial per-call earning for a template execution."""
        pass

    @abstractmethod
    async def settle_execution(
        self,
        execution_id: str,
        outcome: str,
        execution_status: str,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        """Settle a per-call execution and return the service result payload."""
        pass
