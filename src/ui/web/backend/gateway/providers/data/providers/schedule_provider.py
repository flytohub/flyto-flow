"""Schedule Provider Interface"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ScheduleProvider(ABC):
    """
    Schedule data provider interface.

    Implementations may use hosted or self-managed persistence without exposing
    that storage choice to callers.
    """

    @abstractmethod
    async def create(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a schedule. Returns created schedule dict with generated ID."""
        ...

    @abstractmethod
    async def get(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Get schedule by ID."""
        ...

    @abstractmethod
    async def list_schedules(
        self, user_id: str, workflow_id: Optional[str] = None, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List schedules for a user."""
        ...

    @abstractmethod
    async def get_due_schedules(self) -> List[Dict[str, Any]]:
        """Get all active schedules where next_run_at <= now."""
        ...

    @abstractmethod
    async def update(self, schedule_id: str, **kwargs) -> bool:
        """Update schedule fields."""
        ...

    @abstractmethod
    async def delete(self, schedule_id: str) -> bool:
        """Delete a schedule."""
        ...

    @abstractmethod
    async def record_run(self, schedule_id: str, success: bool, next_run_at: Optional[str] = None) -> None:
        """Record a schedule run and update next_run_at."""
        ...

    async def import_legacy(
        self,
        schedule_id: str,
        schedule_data: Dict[str, Any],
        dry_run: bool = False,
    ) -> bool:
        """Import one legacy schedule if the provider supports store migration."""
        raise NotImplementedError("Legacy schedule import is not supported by this provider")
