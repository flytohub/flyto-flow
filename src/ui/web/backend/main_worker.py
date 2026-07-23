"""Standalone worker process for externally shared queue providers."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import signal

from gateway.storage.queue_factory import get_queue
from services.runtime.worker import Worker, WorkerConfig


async def _run(worker_id: str | None, concurrency: int) -> None:
    from gateway.storage.database import init_db
    from gateway.storage.offline_db import init_offline_db
    from services.connections.runtime import configure_connection_runtime
    from services.extensions.runtime import verify_configured_extensions

    init_db()
    init_offline_db()
    extensions = verify_configured_extensions()
    configure_connection_runtime(extensions)
    queue = get_queue()
    health = await queue.health_check()
    if not health.get("healthy"):
        raise RuntimeError(f"Queue health check failed: {health}")
    if os.environ.get("FLYTO_KEY_BACKEND", "local").strip().lower() != "local":
        from services.credentials.encryption import EncryptionKey

        EncryptionKey.initialize()

    config = WorkerConfig(max_concurrent_jobs=concurrency)
    if worker_id:
        config.worker_id = worker_id
    worker = Worker(config)
    stop_requested = asyncio.Event()
    loop = asyncio.get_running_loop()
    for name in ("SIGINT", "SIGTERM"):
        selected = getattr(signal, name, None)
        if selected is not None:
            loop.add_signal_handler(selected, stop_requested.set)
    worker_task = asyncio.create_task(worker.start(), name="flyto-worker")
    stop_task = asyncio.create_task(stop_requested.wait(), name="worker-stop-signal")
    try:
        done, _pending = await asyncio.wait(
            (worker_task, stop_task),
            return_when=asyncio.FIRST_COMPLETED,
        )
        if worker_task in done:
            await worker_task
    finally:
        await worker.stop()
        stop_task.cancel()
        await asyncio.gather(worker_task, stop_task, return_exceptions=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Flyto2 Flow execution worker")
    parser.add_argument("--worker-id")
    parser.add_argument("--concurrency", type=int, default=1)
    args = parser.parse_args()
    if args.concurrency < 1:
        parser.error("--concurrency must be at least 1")
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run(args.worker_id, args.concurrency))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
