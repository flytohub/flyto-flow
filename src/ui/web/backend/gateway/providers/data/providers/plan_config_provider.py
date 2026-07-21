"""Plan config provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class PlanConfigProvider(ABC):
    """Provider interface for plan limit configuration."""

    @abstractmethod
    async def get_plan_limits(self) -> Dict[str, Dict[str, Any]]:
        """Return raw planLimits configuration."""
        pass

    @abstractmethod
    async def get_admin_pricing(self) -> Dict[str, Dict[str, Any]]:
        """Return raw admin-managed plan pricing configuration."""
        pass
