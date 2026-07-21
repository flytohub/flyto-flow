"""
Lightweight CRUD Audit Logger

Fire-and-forget audit logging for CRUD operations.
Writes through the configured data provider and falls back to structured
logging when audit storage is unavailable.

Usage:
    from services.audit.crud_logger import log_crud

    log_crud("create", "template", template_id, current_user)
    log_crud("delete", "webhook", webhook_id, current_user)
"""

import asyncio
import inspect
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from gateway.providers.data.models import AuditAction, AuditLogCreateDTO

logger = logging.getLogger(__name__)


def log_crud(
    action: str,
    resource_type: str,
    resource_id: str,
    user: Optional[Dict[str, Any]] = None,
    *,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Record a CRUD audit event. Non-blocking, never raises.

    Args:
        action: "create", "update", "delete", "publish", "unpublish", etc.
        resource_type: "template", "workflow", "webhook", "schedule", etc.
        resource_id: ID of the affected resource.
        user: The current_user dict (must have "id", optionally "email").
        details: Optional extra context (e.g. {"name": "My Workflow"}).
    """
    try:
        user_id = user.get("id") if user else None
        user_email = user.get("email") if user else None

        entry = {
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_id": user_id,
            "user_email": user_email,
            "details": _safe_summary(details) if details else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if _write_with_provider(entry):
            return

        # Fallback: structured log (local/offline mode)
        logger.info(
            "AUDIT: %s %s/%s by=%s",
            action, resource_type, resource_id, user_id,
        )

    except Exception as e:
        # Audit must NEVER fail the request
        logger.debug("Audit log failed: %s", e)


def _write_with_provider(entry: Dict[str, Any]) -> bool:
    """Write through the active audit-log provider when one is configured."""
    try:
        from gateway.providers.hub import get_data_provider

        data_provider = get_data_provider()
        audit_provider = getattr(data_provider, "audit_logs", None) if data_provider else None
        if audit_provider is None:
            return False

        result = audit_provider.create_log(_to_create_dto(entry))
        if inspect.isawaitable(result):
            _run_audit_write(result)
        return True
    except NotImplementedError:
        return False
    except Exception as e:
        logger.debug("Audit provider unavailable: %s", e)
        return False


def _to_create_dto(entry: Dict[str, Any]) -> AuditLogCreateDTO:
    action = entry["action"]
    return AuditLogCreateDTO(
        actor_id=entry["user_id"] or "",
        actor_email=entry["user_email"],
        action=AuditAction(action),
        resource_type=entry["resource_type"],
        resource_id=entry["resource_id"],
        description=f"{action} {entry['resource_type']}",
        metadata={
            "details": entry["details"],
            "timestamp": entry["timestamp"],
        },
    )


def _run_audit_write(awaitable) -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(_swallow_audit_errors(awaitable))
        return

    loop.create_task(_swallow_audit_errors(awaitable))


async def _swallow_audit_errors(awaitable) -> None:
    try:
        await awaitable
    except Exception as e:
        logger.debug("Audit provider write failed: %s", e)


def _safe_summary(data: Optional[Dict], max_keys: int = 20) -> Optional[Dict]:
    """Truncate large dicts to keep audit storage lean."""
    if not data:
        return None
    if len(data) <= max_keys:
        return data
    keys = list(data.keys())[:max_keys]
    return {k: data[k] for k in keys}
