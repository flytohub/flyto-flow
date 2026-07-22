"""Process-local concurrency guard for CE workflow executions."""

import asyncio
from dataclasses import dataclass


@dataclass
class SlotAcquisitionResult:
    success: bool
    error: str | None = None
    error_code: str | None = None
    retry_after_seconds: int | None = None


class ConcurrencyManager:
    def __init__(self, maximum: int = 50):
        self.maximum = maximum
        self._active: set[str] = set()
        self._lock = asyncio.Lock()

    async def acquire_slot(self, execution_id: str) -> SlotAcquisitionResult:
        async with self._lock:
            if execution_id in self._active:
                return SlotAcquisitionResult(success=True)
            if len(self._active) >= self.maximum:
                return SlotAcquisitionResult(
                    success=False,
                    error="Local execution capacity reached",
                    error_code="LOCAL_CAPACITY_REACHED",
                    retry_after_seconds=10,
                )
            self._active.add(execution_id)
            return SlotAcquisitionResult(success=True)

    async def release_slot(self, execution_id: str) -> bool:
        async with self._lock:
            existed = execution_id in self._active
            self._active.discard(execution_id)
            return existed

    async def get_stats(self) -> dict:
        async with self._lock:
            return {"current": len(self._active), "limit": self.maximum}


_manager: ConcurrencyManager | None = None
_manager_lock = asyncio.Lock()


async def get_concurrency_manager() -> ConcurrencyManager:
    global _manager
    if _manager is None:
        async with _manager_lock:
            if _manager is None:
                _manager = ConcurrencyManager()
    return _manager


async def acquire_execution_slot(execution_id: str) -> SlotAcquisitionResult:
    return await (await get_concurrency_manager()).acquire_slot(execution_id)


async def release_execution_slot(execution_id: str) -> bool:
    return await (await get_concurrency_manager()).release_slot(execution_id)
