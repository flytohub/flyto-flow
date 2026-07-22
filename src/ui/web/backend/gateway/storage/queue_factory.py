"""Factory for CE's bundled local SQLite execution queue."""

from gateway.storage.queue_interface import QueueInterface


_queue_instance: QueueInterface | None = None


def get_queue_backend() -> str:
    return "sqlite"


def create_queue(backend: str | None = None) -> QueueInterface:
    if backend not in (None, "sqlite"):
        raise ValueError("Flyto2 Flow supports only the local SQLite queue")
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
    except Exception as error:
        return {"healthy": False, "error": str(error)}
