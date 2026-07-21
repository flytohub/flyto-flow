"""Disabled marketplace settlement interface for Cloud CE executions."""

from typing import Any


_TERMINAL = {
    "success",
    "succeeded",
    "completed",
    "complete",
    "failed",
    "failure",
    "error",
    "cancelled",
    "canceled",
    "timed_out",
    "timeout",
}


def is_terminal_execution_status(status: Any) -> bool:
    return str(getattr(status, "value", status) or "").lower() in _TERMINAL


async def settle_per_call_execution(
    execution_id: str,
    status: Any,
    error_message: str | None = None,
) -> dict:
    del execution_id, status, error_message
    return {"ok": True, "settled": False, "reason": "disabled_in_ce"}
