"""Admin-role FastAPI dependency.

Lives here (instead of api/admin/) because api/admin/ was deleted when admin
moved to flyto-admin BFF (Go on :8001). A handful of customer-facing routes
in this app still have admin-only operations (audit, billing/orders refund,
billing/subscriptions list-all, invite_keys, creator_program, issues admin).
They keep working by importing require_admin from here.

If you find yourself adding a NEW admin endpoint, build it in flyto-admin BFF
instead. See [[project-flyto-admin]] in the team memory.
"""
from fastapi import Depends

from api.auth import get_current_user
from api.validators import require_admin as _validate_admin


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    _validate_admin(current_user)
    return current_user
