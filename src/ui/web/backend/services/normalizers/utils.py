"""
Generic Utility Helpers

Shared utility functions for normalizers that don't fit into a specific category.
"""

from typing import Dict, Any


def get_value_with_aliases(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    Get value from dict trying multiple keys (for handling camelCase/snake_case).

    Args:
        data: Source dictionary
        *keys: Keys to try in order
        default: Default value if no key found

    Returns:
        First found value or default
    """
    for key in keys:
        if key in data:
            return data[key]
    return default


def extract_action_from_module_id(module_id: str) -> str:
    """
    Extract action name from module ID.

    Examples:
        "string.uppercase" -> "uppercase"
        "template.invoke:abc123" -> "invoke"

    Args:
        module_id: The module identifier

    Returns:
        Action name (last part before any resource ID)
    """
    if not module_id:
        return ""

    # Remove resource ID if present
    base_id = module_id.split(":")[0]

    # Get last part
    parts = base_id.split(".")
    return parts[-1] if parts else ""
