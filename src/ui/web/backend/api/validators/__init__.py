"""
API Validators Module

Provides unified validation utilities for all API routes.
This eliminates duplicate validation code and ensures consistent error handling.

Usage:
    from api.validators import require_admin, require_resource, validate_pagination

    @router.get("/admin/users")
    async def list_users(current_user: dict = Depends(get_current_user)):
        require_admin(current_user)
        # ... rest of handler
"""

from api.validators.common import (
    require_admin,
    require_resource,
    require_owner,
    validate_pagination,
    validate_uuid,
    validate_email,
    validate_not_empty,
    validate_string_length,
    validate_enum_value,
)

from api.validators.dependencies import (
    PaginationParams,
    get_pagination,
)

__all__ = [
    # Common validators
    "require_admin",
    "require_resource",
    "require_owner",
    "validate_pagination",
    "validate_uuid",
    "validate_email",
    "validate_not_empty",
    "validate_string_length",
    "validate_enum_value",
    # Dependencies
    "PaginationParams",
    "get_pagination",
]
