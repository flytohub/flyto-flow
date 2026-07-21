"""CE execution quota policy. Self-hosted local execution is not metered."""

from fastapi import Depends

from gateway.auth import get_current_active_user
from gateway.providers.base import UserInfo


def get_execution_cost(module_id: str) -> int:
    del module_id
    return 0


async def check_execution_quota(user_id: str, plan_name=None) -> bool:
    del user_id, plan_name
    return True


async def deduct_execution_points(user_id: str, points: int) -> float:
    del user_id, points
    return 0.0


async def deduct_points_for_module(user_id: str, module_id: str) -> float:
    del user_id, module_id
    return 0.0


async def require_execution_quota(
    user: UserInfo = Depends(get_current_active_user),
) -> UserInfo:
    return user
