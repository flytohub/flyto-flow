#!/usr/bin/env python3
"""Repeatable queue and HTTP load probes for Flyto2 Flow."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path
from time import perf_counter
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "src/ui/web/backend"
sys.path.insert(0, str(BACKEND))


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int((len(ordered) - 1) * percentile))
    return ordered[index]


def _summary(
    *,
    operation: str,
    total: int,
    errors: int,
    elapsed_seconds: float,
    latencies_ms: list[float],
) -> dict[str, Any]:
    return {
        "schema": "flyto.load-result.v1",
        "operation": operation,
        "total": total,
        "errors": errors,
        "error_rate": errors / total if total else 0.0,
        "elapsed_seconds": round(elapsed_seconds, 4),
        "throughput_per_second": round(total / elapsed_seconds, 2)
        if elapsed_seconds
        else 0.0,
        "latency_ms": {
            "p50": round(_percentile(latencies_ms, 0.50), 3),
            "p95": round(_percentile(latencies_ms, 0.95), 3),
            "p99": round(_percentile(latencies_ms, 0.99), 3),
            "max": round(max(latencies_ms, default=0.0), 3),
        },
    }


async def _queue_probe(args: argparse.Namespace) -> dict[str, Any]:
    from gateway.storage.database import close_db, init_db, transaction
    from gateway.storage.sqlite_queue import SQLiteQueue

    with tempfile.TemporaryDirectory(prefix="flyto-load-") as temporary:
        os.environ["FLYTO_EXECUTION_DB_PATH"] = str(
            Path(temporary) / "executions.db"
        )
        close_db()
        init_db()
        with transaction(immediate=True) as connection:
            connection.executemany(
                """
                INSERT INTO executions
                    (id, workflow_id, workspace_id, started_at)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (
                        f"load-execution-{index}",
                        "load-workflow",
                        "local-workspace",
                        "2026-01-01T00:00:00+00:00",
                    )
                    for index in range(args.jobs)
                ],
            )

        queue = SQLiteQueue()
        payload = "x" * args.payload_bytes
        latencies: list[float] = []
        started = perf_counter()
        for index in range(args.jobs):
            operation_started = perf_counter()
            await queue.enqueue(
                f"load-execution-{index}",
                "load-workflow",
                "local-workspace",
                idempotency_key=f"load-operation-{index}",
                metadata={"payload": payload},
            )
            latencies.append((perf_counter() - operation_started) * 1000)

        errors = 0

        async def consume(worker_index: int) -> None:
            nonlocal errors
            while True:
                operation_started = perf_counter()
                job = await queue.dequeue(
                    f"load-worker-{worker_index}",
                    lease_duration_seconds=30,
                )
                if job is None:
                    return
                if not await queue.ack(job.id, f"load-worker-{worker_index}"):
                    errors += 1
                latencies.append((perf_counter() - operation_started) * 1000)

        await asyncio.gather(*(consume(index) for index in range(args.workers)))
        elapsed = perf_counter() - started
        stats = await queue.get_stats()
        if stats.completed != args.jobs:
            errors += abs(args.jobs - stats.completed)
        result = _summary(
            operation="sqlite-queue",
            total=args.jobs,
            errors=errors,
            elapsed_seconds=elapsed,
            latencies_ms=latencies,
        )
        result["workers"] = args.workers
        result["payload_bytes"] = args.payload_bytes
        result["queue_stats"] = stats.to_dict()
        close_db()
        return result


async def _http_probe(args: argparse.Namespace) -> dict[str, Any]:
    import httpx

    body = (
        json.loads(args.request_file.read_text(encoding="utf-8"))
        if args.request_file
        else None
    )
    semaphore = asyncio.Semaphore(args.concurrency)
    latencies: list[float] = []
    statuses: Counter[int | str] = Counter()

    headers = {}
    if args.token:
        headers["Authorization"] = f"Bearer {args.token}"

    async with httpx.AsyncClient(
        base_url=args.url,
        timeout=args.timeout,
        follow_redirects=False,
        headers=headers,
    ) as client:
        started = perf_counter()

        async def request_once() -> None:
            async with semaphore:
                operation_started = perf_counter()
                try:
                    response = await client.request(
                        args.method,
                        args.path,
                        json=body,
                    )
                    statuses[response.status_code] += 1
                except Exception:
                    statuses["transport_error"] += 1
                latencies.append((perf_counter() - operation_started) * 1000)

        await asyncio.gather(*(request_once() for _ in range(args.requests)))
        elapsed = perf_counter() - started

    errors = sum(
        count
        for status, count in statuses.items()
        if not isinstance(status, int) or status < 200 or status >= 300
    )
    result = _summary(
        operation="http",
        total=args.requests,
        errors=errors,
        elapsed_seconds=elapsed,
        latencies_ms=latencies,
    )
    result["concurrency"] = args.concurrency
    result["statuses"] = {str(status): count for status, count in statuses.items()}
    return result


def _passes_thresholds(result: dict[str, Any], args: argparse.Namespace) -> bool:
    return (
        result["error_rate"] <= args.max_error_rate
        and result["throughput_per_second"] >= args.min_throughput
    )


def main() -> int:
    parser = argparse.ArgumentParser(prog="flyto-load-test")
    commands = parser.add_subparsers(dest="command", required=True)

    queue = commands.add_parser("queue")
    queue.add_argument("--jobs", type=int, default=1000)
    queue.add_argument("--workers", type=int, default=8)
    queue.add_argument("--payload-bytes", type=int, default=1024)

    http = commands.add_parser("http")
    http.add_argument("--url", default="http://127.0.0.1:9000")
    http.add_argument("--path", default="/api/health")
    http.add_argument("--method", choices=("GET", "POST", "PUT"), default="GET")
    http.add_argument("--request-file", type=Path)
    http.add_argument("--requests", type=int, default=1000)
    http.add_argument("--concurrency", type=int, default=20)
    http.add_argument("--timeout", type=float, default=30.0)
    http.add_argument("--token", default=os.environ.get("FLYTO_LOAD_TEST_TOKEN", ""))

    for command in (queue, http):
        command.add_argument("--max-error-rate", type=float, default=0.0)
        command.add_argument("--min-throughput", type=float, default=1.0)

    args = parser.parse_args()
    numeric_values = [
        value
        for value in (
            getattr(args, "jobs", None),
            getattr(args, "workers", None),
            getattr(args, "payload_bytes", None),
            getattr(args, "requests", None),
            getattr(args, "concurrency", None),
        )
        if value is not None
    ]
    if any(value < 1 for value in numeric_values):
        parser.error("Load counts, concurrency, workers, and payload size must be positive")
    if not 0 <= args.max_error_rate <= 1:
        parser.error("--max-error-rate must be between 0 and 1")
    if args.min_throughput < 0:
        parser.error("--min-throughput cannot be negative")

    result = asyncio.run(
        _queue_probe(args) if args.command == "queue" else _http_probe(args)
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if _passes_thresholds(result, args) else 1


if __name__ == "__main__":
    raise SystemExit(main())
