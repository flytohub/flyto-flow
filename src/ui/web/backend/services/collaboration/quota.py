"""
Collaboration Quota Service

Tracks collaboration usage minutes per user per month.
Only free-plan owners are subject to quota limits.

Provider storage structure:
    collaboration_usage/{user_id}
    └── months: { "2026-02": { "minutes": 42, "last_updated": "..." } }
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _current_month_key() -> str:
    """Return current UTC month key, e.g. '2026-02'."""
    return datetime.now(timezone.utc).strftime("%Y-%m")


async def get_configured_free_hours() -> int:
    """Read admin-configured free collaboration hours from plan_config service.

    Uses the unified plan_config service which reads from Firestore with TTL cache.
    """
    try:
        from services.plan_config import get_collaboration_hours
        hours = await get_collaboration_hours("free")
        return hours if hours is not None else 5
    except Exception as e:
        logger.warning(f"Failed to read collaboration hours from plan_config: {e}")
        return 5


async def get_used_minutes(user_id: str) -> int:
    """Read current month's used collaboration minutes from the data provider."""
    try:
        provider = _get_collaboration_quota_provider()
        if provider is None:
            return 0
        return await provider.get_used_minutes(user_id, _current_month_key())
    except NotImplementedError:
        logger.debug("Collaboration quota provider not available, returning 0 used minutes")
        return 0
    except Exception as e:
        logger.error(f"Failed to read collaboration usage for {user_id}: {e}")
        return 0


async def add_minutes(user_id: str, minutes: int = 1) -> int:
    """Atomically add minutes to current month's usage. Returns new total."""
    try:
        provider = _get_collaboration_quota_provider()
        if provider is None:
            return 0
        return await provider.add_minutes(
            user_id,
            minutes,
            _current_month_key(),
            datetime.now(timezone.utc).isoformat(),
        )
    except NotImplementedError:
        logger.debug("Collaboration quota provider not available, skipping add_minutes")
        return 0
    except Exception as e:
        logger.error(f"Failed to add collaboration minutes for {user_id}: {e}")
        return 0


def _get_collaboration_quota_provider():
    from gateway.providers.hub import get_data_provider

    data_provider = get_data_provider()
    if data_provider is None:
        return None
    return data_provider.collaboration_quota


def build_quota_info(
    is_pro: bool,
    is_owner: bool,
    used_minutes: int = 0,
    limit_hours: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Build the quota_info payload for WebSocket.

    Rules:
    - Pro user or guest (not owner) -> unlimited
    - Free owner -> limited by collaboration_hours
    """
    if is_pro or not is_owner:
        return {
            "type": "quota_info",
            "is_unlimited": True,
        }

    # Free owner with limit
    if limit_hours is None:
        # Fallback: treat as free default (5 hours)
        limit_hours = 5

    total_minutes = limit_hours * 60
    remaining = max(0, total_minutes - used_minutes)

    return {
        "type": "quota_info",
        "is_unlimited": False,
        "used_minutes": used_minutes,
        "total_minutes": total_minutes,
        "remaining_minutes": remaining,
    }
