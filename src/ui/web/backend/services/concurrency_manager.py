"""
Concurrency Manager

Manages concurrent execution limits to prevent resource exhaustion.
Addresses RACE-3 from security audit.

Limits:
- Per-user concurrent executions
- Per-organization concurrent executions
- Global concurrent executions
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Dict, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class ConcurrencyLimits:
    """Configurable concurrency limits."""
    per_user: int = 50  # Max concurrent executions per user (increased for testing)
    per_org: int = 100  # Max concurrent executions per org
    global_max: int = 500  # Max total concurrent executions


@dataclass
class SlotAcquisitionResult:
    """Result of slot acquisition attempt."""
    success: bool
    error: Optional[str] = None
    error_code: Optional[str] = None
    retry_after_seconds: Optional[int] = None


class ConcurrencyManager:
    """
    Manages concurrent execution slots.

    Thread-safe implementation using asyncio locks.
    """

    def __init__(self, limits: Optional[ConcurrencyLimits] = None):
        """Initialize with concurrency limits and execution tracking sets."""
        self.limits = limits or ConcurrencyLimits()
        self._lock = asyncio.Lock()

        # Track active executions
        self._user_executions: Dict[str, Set[str]] = {}  # user_id -> set of execution_ids
        self._org_executions: Dict[str, Set[str]] = {}  # org_id -> set of execution_ids
        self._all_executions: Set[str] = set()  # All active execution_ids

    async def acquire_slot(
        self,
        execution_id: str,
        user_id: str,
        org_id: str,
        workflow_id: str,
    ) -> SlotAcquisitionResult:
        """
        Try to acquire an execution slot.

        Args:
            execution_id: Unique execution identifier
            user_id: User requesting execution
            org_id: Organization ID
            workflow_id: Workflow being executed

        Returns:
            SlotAcquisitionResult indicating success or reason for failure
        """
        async with self._lock:
            # Check global limit
            if len(self._all_executions) >= self.limits.global_max:
                logger.warning(
                    f"Global execution limit reached ({self.limits.global_max})"
                )
                return SlotAcquisitionResult(
                    success=False,
                    error="System is at maximum capacity",
                    error_code="GLOBAL_LIMIT_REACHED",
                    retry_after_seconds=30,
                )

            # Check per-org limit
            org_count = len(self._org_executions.get(org_id, set()))
            if org_count >= self.limits.per_org:
                logger.warning(
                    f"Org {org_id} execution limit reached ({self.limits.per_org})"
                )
                return SlotAcquisitionResult(
                    success=False,
                    error=f"Organization concurrent execution limit reached ({self.limits.per_org})",
                    error_code="ORG_LIMIT_REACHED",
                    retry_after_seconds=15,
                )

            # Check per-user limit
            user_count = len(self._user_executions.get(user_id, set()))
            if user_count >= self.limits.per_user:
                logger.warning(
                    f"User {user_id} execution limit reached ({self.limits.per_user})"
                )
                return SlotAcquisitionResult(
                    success=False,
                    error=f"User concurrent execution limit reached ({self.limits.per_user})",
                    error_code="USER_LIMIT_REACHED",
                    retry_after_seconds=10,
                )

            # Acquire slot
            if user_id not in self._user_executions:
                self._user_executions[user_id] = set()
            if org_id not in self._org_executions:
                self._org_executions[org_id] = set()

            self._user_executions[user_id].add(execution_id)
            self._org_executions[org_id].add(execution_id)
            self._all_executions.add(execution_id)

            logger.debug(
                f"Acquired slot for {execution_id}: "
                f"user={user_count + 1}/{self.limits.per_user}, "
                f"org={org_count + 1}/{self.limits.per_org}, "
                f"global={len(self._all_executions)}/{self.limits.global_max}"
            )

            return SlotAcquisitionResult(success=True)

    async def release_slot(
        self,
        execution_id: str,
        user_id: str,
        org_id: str,
    ) -> bool:
        """
        Release an execution slot.

        Args:
            execution_id: Execution to release
            user_id: User who owned the slot
            org_id: Organization ID

        Returns:
            True if slot was released, False if not found
        """
        async with self._lock:
            if execution_id not in self._all_executions:
                return False

            self._all_executions.discard(execution_id)

            if user_id in self._user_executions:
                self._user_executions[user_id].discard(execution_id)
                if not self._user_executions[user_id]:
                    del self._user_executions[user_id]

            if org_id in self._org_executions:
                self._org_executions[org_id].discard(execution_id)
                if not self._org_executions[org_id]:
                    del self._org_executions[org_id]

            logger.debug(f"Released slot for {execution_id}")
            return True

    async def get_stats(self) -> Dict:
        """Get current concurrency statistics."""
        async with self._lock:
            return {
                "global": {
                    "current": len(self._all_executions),
                    "limit": self.limits.global_max,
                },
                "users": {
                    user_id: len(execs)
                    for user_id, execs in self._user_executions.items()
                },
                "orgs": {
                    org_id: len(execs)
                    for org_id, execs in self._org_executions.items()
                },
            }


# Global singleton instance
_manager: Optional[ConcurrencyManager] = None
_manager_lock = asyncio.Lock()


async def get_concurrency_manager() -> ConcurrencyManager:
    """Get or create the global concurrency manager."""
    global _manager
    if _manager is None:
        async with _manager_lock:
            if _manager is None:
                _manager = ConcurrencyManager()
    return _manager


async def acquire_execution_slot(
    execution_id: str,
    user_id: str,
    org_id: str,
    workflow_id: str,
) -> SlotAcquisitionResult:
    """
    Convenience function to acquire an execution slot.

    This is the main entry point used by ExecutionService.
    """
    manager = await get_concurrency_manager()
    return await manager.acquire_slot(execution_id, user_id, org_id, workflow_id)


async def release_execution_slot(
    execution_id: str,
    user_id: str,
    org_id: str,
) -> bool:
    """Convenience function to release an execution slot."""
    manager = await get_concurrency_manager()
    return await manager.release_slot(execution_id, user_id, org_id)
