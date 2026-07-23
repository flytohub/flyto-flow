"""Queue composition root with a safe external provider seam."""

import os

from gateway.providers.loading import load_provider_factory
from gateway.storage.queue_interface import QueueInterface


_queue_instance: QueueInterface | None = None


def get_queue_backend() -> str:
    return os.environ.get("QUEUE_BACKEND", "sqlite").strip().lower()


def _create_external_queue(spec: str) -> QueueInterface:
    factory = load_provider_factory(
        spec,
        setting_name="FLYTO_QUEUE_FACTORY",
    )
    queue = factory()
    if not isinstance(queue, QueueInterface):
        raise TypeError("Queue provider must implement QueueInterface")
    return queue


def create_queue(backend: str | None = None) -> QueueInterface:
    selected = backend or get_queue_backend()
    if selected != "sqlite":
        spec = os.environ.get("FLYTO_QUEUE_FACTORY", "").strip()
        if not spec:
            raise ValueError(
                f"QUEUE_BACKEND={selected!r} requires an allowlisted FLYTO_QUEUE_FACTORY"
            )
        return _create_external_queue(spec)
    from gateway.storage.sqlite_queue import SQLiteQueue

    return SQLiteQueue()


def get_queue() -> QueueInterface:
    global _queue_instance
    if _queue_instance is None:
        _queue_instance = create_queue()
    return _queue_instance


def reset_queue() -> None:
    global _queue_instance
    _queue_instance = None


async def get_queue_health() -> dict:
    try:
        return await get_queue().health_check()
    except Exception:
        return {"healthy": False, "error": "queue_health_check_failed"}
