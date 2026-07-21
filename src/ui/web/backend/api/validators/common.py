"""
Common Validators

Unified validation functions to replace scattered HTTPException checks.
These functions raise HTTPException with consistent error messages.
"""

import re
import uuid
from typing import Any, Optional, List, Type
from enum import Enum

from fastapi import HTTPException


def require_admin(current_user: dict, detail: str = "Admin access required") -> None:
    """
    Verify user has admin privileges.

    Args:
        current_user: User dict from get_current_user dependency
        detail: Custom error message

    Raises:
        HTTPException 403 if user is not admin
    """
    is_admin = current_user.get("is_admin", False)
    roles = current_user.get("roles", [])

    if not is_admin and "admin" not in roles:
        raise HTTPException(status_code=403, detail=detail)


def require_resource(
    resource: Any,
    resource_name: str = "Resource",
    resource_id: Optional[str] = None,
) -> None:
    """
    Verify resource exists (is not None/False/empty).

    Args:
        resource: The resource to check
        resource_name: Human-readable name for error message
        resource_id: Optional ID for more specific error

    Raises:
        HTTPException 404 if resource is None, False, or falsy

    Note:
        Uses truthiness check to handle:
        - None (get returns None when not found)
        - False (delete returns False when not found)
        - Empty dict/list (rare but possible)
    """
    if not resource:
        if resource_id:
            detail = f"{resource_name} '{resource_id}' not found"
        else:
            detail = f"{resource_name} not found"
        raise HTTPException(status_code=404, detail=detail)


def require_owner(
    resource_owner_id: str,
    current_user_id: str,
    allow_admin: bool = True,
    current_user: Optional[dict] = None,
    detail: str = "You do not have permission to access this resource",
) -> None:
    """
    Verify user owns the resource or is admin.

    Args:
        resource_owner_id: Owner ID of the resource
        current_user_id: Current user's ID
        allow_admin: If True, admins can access any resource
        current_user: Full user dict (needed if allow_admin=True)
        detail: Custom error message

    Raises:
        HTTPException 403 if user doesn't own resource and isn't admin
    """
    if resource_owner_id == current_user_id:
        return

    if allow_admin and current_user:
        is_admin = current_user.get("is_admin", False)
        roles = current_user.get("roles", [])
        if is_admin or "admin" in roles:
            return

    raise HTTPException(status_code=403, detail=detail)


def validate_pagination(
    page: int,
    page_size: int,
    max_page_size: int = 100,
    min_page: int = 1,
) -> None:
    """
    Validate pagination parameters.

    Args:
        page: Page number (1-indexed)
        page_size: Items per page
        max_page_size: Maximum allowed page size
        min_page: Minimum page number (usually 1)

    Raises:
        HTTPException 400 if pagination is invalid
    """
    if page < min_page:
        raise HTTPException(
            status_code=400,
            detail=f"Page must be >= {min_page}"
        )

    if page_size < 1:
        raise HTTPException(
            status_code=400,
            detail="Page size must be >= 1"
        )

    if page_size > max_page_size:
        raise HTTPException(
            status_code=400,
            detail=f"Page size must be <= {max_page_size}"
        )


def validate_uuid(
    value: str,
    field_name: str = "ID",
) -> None:
    """
    Validate string is a valid UUID.

    Args:
        value: String to validate
        field_name: Field name for error message

    Raises:
        HTTPException 400 if not a valid UUID
    """
    try:
        uuid.UUID(value)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field_name}: must be a valid UUID"
        )


def validate_email(
    email: str,
    field_name: str = "Email",
) -> None:
    """
    Validate email format.

    Args:
        email: Email string to validate
        field_name: Field name for error message

    Raises:
        HTTPException 400 if email format is invalid
    """
    # Simple email regex - not exhaustive but catches most issues
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not email or not re.match(email_pattern, email):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field_name} format"
        )


def validate_not_empty(
    value: Any,
    field_name: str = "Field",
) -> None:
    """
    Validate value is not None, empty string, or empty collection.

    Args:
        value: Value to check
        field_name: Field name for error message

    Raises:
        HTTPException 400 if value is empty
    """
    if value is None:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} is required"
        )

    if isinstance(value, str) and not value.strip():
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} cannot be empty"
        )

    if isinstance(value, (list, dict, set)) and len(value) == 0:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} cannot be empty"
        )


def validate_string_length(
    value: str,
    field_name: str = "Field",
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
) -> None:
    """
    Validate string length constraints.

    Args:
        value: String to validate
        field_name: Field name for error message
        min_length: Minimum length (inclusive)
        max_length: Maximum length (inclusive)

    Raises:
        HTTPException 400 if length constraints violated
    """
    if value is None:
        return  # Use validate_not_empty for required fields

    length = len(value)

    if min_length is not None and length < min_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be at least {min_length} characters"
        )

    if max_length is not None and length > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be at most {max_length} characters"
        )


def validate_enum_value(
    value: Any,
    enum_class: Type[Enum],
    field_name: str = "Value",
) -> None:
    """
    Validate value is a valid enum member.

    Args:
        value: Value to check
        enum_class: Enum class to validate against
        field_name: Field name for error message

    Raises:
        HTTPException 400 if value is not a valid enum member
    """
    valid_values = [e.value for e in enum_class]

    if value not in valid_values:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field_name}. Must be one of: {', '.join(map(str, valid_values))}"
        )
