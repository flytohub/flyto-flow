"""
API Response Helpers

Standardized response formats for API endpoints.
All responses follow the convention:
- ok: boolean - success/failure indicator
- data: dict - response payload (optional)
- message: string - success message (optional)
- error: string - error message (optional)

For list endpoints:
- items/users/templates etc: array - list of items
- total: int - total count
- page: int - current page
- page_size: int - items per page
"""

from typing import Any, Dict, List, Optional


def success_response(
    data: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a success response.

    Args:
        data: Response payload
        message: Success message
        **kwargs: Additional fields to include

    Returns:
        Standardized success response dict
    """
    response = {"ok": True}
    if data is not None:
        response["data"] = data
    if message is not None:
        response["message"] = message
    response.update(kwargs)
    return response


def error_response(
    error: str,
    code: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create an error response.

    Args:
        error: Error message
        code: Optional error code
        **kwargs: Additional fields

    Returns:
        Standardized error response dict
    """
    response = {"ok": False, "error": error}
    if code is not None:
        response["error_code"] = code
    response.update(kwargs)
    return response


def list_response(
    items: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
    key: str = "items",
    **kwargs
) -> Dict[str, Any]:
    """
    Create a paginated list response.

    Args:
        items: List of items
        total: Total count
        page: Current page number
        page_size: Items per page
        key: Key name for items list (e.g., "users", "templates")
        **kwargs: Additional fields

    Returns:
        Standardized list response dict
    """
    response = {
        "ok": True,
        key: items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
    response.update(kwargs)
    return response


def ensure_ok(result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Ensure a result dict has the 'ok' field.

    Args:
        result: Result dict from provider

    Returns:
        Result with 'ok' field added if missing
    """
    if result is None:
        return {"ok": False, "error": "Not found"}
    if isinstance(result, dict) and "ok" not in result:
        result["ok"] = True
    return result


def to_camel_case(data: Any) -> Any:
    """
    Convert snake_case keys to camelCase recursively.

    Args:
        data: Dict, list, or primitive value

    Returns:
        Same structure with camelCase keys
    """
    import re

    def convert_key(key: str) -> str:
        # Convert snake_case to camelCase
        components = key.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])

    if isinstance(data, dict):
        return {convert_key(k): to_camel_case(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [to_camel_case(item) for item in data]
    return data
