"""
No-op Audit Provider

Minimal audit logging for Cloud mode.
Logs to standard logger only, no persistent storage.
"""

import logging
from typing import Any

from gateway.providers.base import AuditProvider

logger = logging.getLogger(__name__)


class NoopAuditProvider(AuditProvider):
    """
    No-op audit provider for Cloud mode.

    Simply logs audit events to the standard logger.
    Does not persist to database or storage.
    """

    def __init__(self):
        """Initialize noop audit provider."""
        self._enabled = True

    @property
    def name(self) -> str:
        return "noop"

    async def log(
        self,
        action: str,
        actor_id: str,
        resource_type: str = None,
        resource_id: str = None,
        result: str = "success",
        details: dict = None,
        **kwargs: Any
    ) -> None:
        """
        Log audit event.

        Simply logs to standard Python logger.
        No persistent storage in Cloud mode.

        Args:
            action: Action performed
            actor_id: Who performed the action
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            result: success or failure
            details: Additional details
        """
        if not self._enabled:
            return

        log_data = {
            "action": action,
            "actor_id": actor_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "result": result,
        }

        if details:
            log_data["details"] = details

        logger.info(f"Audit: {log_data}")

    async def get_recent(self, limit: int = 100) -> list:
        """
        Get recent audit entries.

        Returns empty list as noop provider doesn't store entries.
        """
        return []

    async def get_by_actor(self, actor_id: str, limit: int = 100) -> list:
        """
        Get audit entries by actor.

        Returns empty list as noop provider doesn't store entries.
        """
        return []

    def enable(self) -> None:
        """Enable audit logging."""
        self._enabled = True

    def disable(self) -> None:
        """Disable audit logging."""
        self._enabled = False

    async def query(
        self,
        filters: dict,
        limit: int = 100,
        offset: int = 0
    ) -> list:
        """
        Query audit logs.

        Returns empty list as noop provider doesn't store entries.

        Args:
            filters: Query filters (ignored)
            limit: Max results (ignored)
            offset: Pagination offset (ignored)

        Returns:
            Empty list
        """
        return []
