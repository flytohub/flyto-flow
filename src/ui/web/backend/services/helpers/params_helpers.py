"""
Parameter normalization helpers.

Centralizes type coercion logic for workflow parameters,
ensuring consistent types when saving templates/workflows.
"""
from typing import Dict, Any, Optional
import re


def normalize_param_types(params: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Normalize parameter types based on schema.

    Converts string representations to proper types:
    - "true"/"false" -> bool
    - "123" -> int/float (based on schema or content)
    - Preserves ${...} variable references as strings

    Args:
        params: Parameter dict to normalize
        schema: Optional params_schema to guide type conversion.
                If provided, uses schema type hints.
                If not provided, uses heuristic type detection.

    Returns:
        New dict with normalized parameter types

    Examples:
        >>> normalize_param_types({"enabled": "true", "count": "5"})
        {"enabled": True, "count": 5}

        >>> normalize_param_types({"value": "${input.x}"})
        {"value": "${input.x}"}  # Preserved as string

        >>> normalize_param_types({"rate": "3.14"}, {"properties": {"rate": {"type": "number"}}})
        {"rate": 3.14}
    """
    if not params or not isinstance(params, dict):
        return params or {}

    # Get schema properties if available
    properties = {}
    if schema and isinstance(schema, dict):
        properties = schema.get("properties", schema)
        if not isinstance(properties, dict):
            properties = {}

    result = {}
    for key, value in params.items():
        result[key] = _normalize_value(value, properties.get(key))

    return result


def _normalize_value(value: Any, prop_schema: Optional[Dict[str, Any]] = None) -> Any:
    """
    Normalize a single parameter value.

    Args:
        value: The value to normalize
        prop_schema: Optional schema for this property

    Returns:
        Normalized value
    """
    # None/missing values pass through
    if value is None:
        return value

    # Non-string values pass through (already correct type)
    if not isinstance(value, str):
        # Recursively normalize nested dicts
        if isinstance(value, dict):
            nested_schema = prop_schema.get("properties") if prop_schema else None
            return normalize_param_types(value, {"properties": nested_schema} if nested_schema else None)
        # Recursively normalize arrays
        if isinstance(value, list):
            item_schema = prop_schema.get("items") if prop_schema else None
            return [_normalize_value(item, item_schema) for item in value]
        return value

    # Preserve variable references
    if _is_variable_reference(value):
        return value

    # Preserve expression syntax
    if _is_expression(value):
        return value

    # Get expected type from schema
    expected_type = prop_schema.get("type") if prop_schema else None

    # Type-based conversion
    if expected_type == "boolean":
        return _to_boolean(value)
    elif expected_type == "integer":
        return _to_integer(value)
    elif expected_type == "number":
        return _to_number(value)
    elif expected_type == "string":
        return value  # Keep as string
    elif expected_type == "array":
        # Try to parse JSON array
        return _try_parse_json(value, fallback=value)
    elif expected_type == "object":
        # Try to parse JSON object
        return _try_parse_json(value, fallback=value)

    # No schema - use heuristic detection
    return _heuristic_normalize(value)


def _is_variable_reference(value: str) -> bool:
    """Check if value is a variable reference like ${input.x}."""
    return bool(re.match(r'^\$\{.*\}$', value.strip()))


def _is_expression(value: str) -> bool:
    """Check if value contains expression syntax."""
    # Matches: ${{ ... }}, {{ ... }}, or contains ${
    return bool(
        re.search(r'\$\{\{.*\}\}', value) or
        re.search(r'\{\{.*\}\}', value) or
        '${' in value
    )


def _to_boolean(value: str) -> Any:
    """Convert string to boolean, preserving original if not boolean-like."""
    lower = value.strip().lower()
    if lower in ("true", "yes", "1", "on"):
        return True
    elif lower in ("false", "no", "0", "off"):
        return False
    return value  # Not a boolean string, keep original


def _to_integer(value: str) -> Any:
    """Convert string to integer if valid."""
    try:
        # Check if it's a valid integer string
        stripped = value.strip()
        if stripped and stripped.lstrip("-").isdigit():
            return int(stripped)
    except (ValueError, AttributeError):
        pass
    return value


def _to_number(value: str) -> Any:
    """Convert string to number (int or float) if valid."""
    try:
        stripped = value.strip()
        if not stripped:
            return value

        # Try integer first
        if stripped.lstrip("-").isdigit():
            return int(stripped)

        # Try float
        float_val = float(stripped)
        # Return int if it's a whole number
        if float_val.is_integer():
            return int(float_val)
        return float_val
    except (ValueError, AttributeError):
        pass
    return value


def _try_parse_json(value: str, fallback: Any = None) -> Any:
    """Try to parse value as JSON."""
    import json
    try:
        stripped = value.strip()
        if stripped.startswith(("[", "{")):
            return json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        pass
    return fallback if fallback is not None else value


def _heuristic_normalize(value: str) -> Any:
    """
    Heuristic type detection when no schema is available.

    Conservative approach: only convert obvious cases.
    """
    stripped = value.strip()

    # Boolean detection (exact matches only)
    if stripped.lower() == "true":
        return True
    if stripped.lower() == "false":
        return False

    # Integer detection (no decimals, no scientific notation)
    if stripped.lstrip("-").isdigit():
        try:
            return int(stripped)
        except ValueError:
            pass

    # Float detection (has decimal point)
    if "." in stripped and not stripped.startswith(".") and not stripped.endswith("."):
        try:
            parts = stripped.lstrip("-").split(".")
            if len(parts) == 2 and all(p.isdigit() for p in parts):
                return float(stripped)
        except ValueError:
            pass

    # JSON array/object detection
    if stripped.startswith("[") or stripped.startswith("{"):
        result = _try_parse_json(stripped, fallback=None)
        if result is not None:
            return result

    # Default: keep as string
    return value


def coerce_params_for_save(params: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Coerce parameter types before saving to database.

    This is the main entry point for normalizing params when saving
    templates or workflows. It ensures consistent types in the database.

    Args:
        params: Raw params dict (may have string representations)
        schema: Optional params_schema for type guidance

    Returns:
        Normalized params dict ready for storage
    """
    return normalize_param_types(params, schema)
