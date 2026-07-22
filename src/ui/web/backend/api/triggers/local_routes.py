"""Accountless, local-only trigger utilities."""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from services.infra.scheduler import CronParser

from .models import CronValidateRequest


local_router = APIRouter(prefix="/triggers", tags=["triggers"])


@local_router.post("/cron/validate")
async def validate_cron_expression(request: CronValidateRequest) -> Dict[str, Any]:
    result = CronParser.validate(request.expression)
    if not result.valid:
        return {"ok": False, "valid": False, "error": result.error}
    try:
        next_run = CronParser.get_next_run(request.expression)
        return {
            "ok": True,
            "valid": True,
            "expression": request.expression,
            "next_run_at": next_run.isoformat(),
        }
    except Exception as exc:
        return {"ok": False, "valid": False, "error": str(exc)}


@local_router.get("/cron/next")
async def get_cron_next_run(
    expression: str,
    timezone: str = "UTC",
    count: int = Query(5, ge=1, le=20),
) -> Dict[str, Any]:
    try:
        next_runs = []
        current = None
        for _ in range(count):
            current = CronParser.get_next_run(expression, current, timezone_str=timezone)
            next_runs.append(current.isoformat())
        return {
            "ok": True,
            "expression": expression,
            "timezone": timezone,
            "next_runs": next_runs,
            "next_run_at": next_runs[0] if next_runs else None,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid cron expression: {exc}") from exc
