"""
Schema-Aware Parameter Validation

Validates parameter values against their paramsSchema constraints.
Each parameter is checked against its individual schema constraints
(minLength, maxLength, minimum, maximum, pattern, enum, etc.).
"""

import re
import logging
from typing import Any, Dict, List, Optional

from services.template.validator.models import ValidationIssue, ValidationSeverity

logger = logging.getLogger(__name__)


def validate_params_against_schema(
    params: Dict[str, Any],
    params_schema: Dict[str, Any],
) -> List[ValidationIssue]:
    """
    Validate parameter values against their paramsSchema constraints.

    Args:
        params: Parameter key-value pairs to validate
        params_schema: Normalized paramsSchema dict with "properties" and "required"

    Returns:
        List of ValidationIssue for constraint violations
    """
    issues: List[ValidationIssue] = []

    if not isinstance(params_schema, dict):
        return issues

    properties = params_schema.get("properties", {})
    required_fields = params_schema.get("required", [])

    # Check required fields
    for field_name in required_fields:
        if field_name not in params or params[field_name] is None:
            prop = properties.get(field_name, {})
            # Skip hidden fields — they are typically auto-filled
            if prop.get("hidden"):
                continue
            label = prop.get("label", field_name) if prop else field_name
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                path=f"params.{field_name}",
                message=f"Missing required parameter: {label}",
                code="REQUIRED_PARAM_MISSING",
            ))

    # Validate each provided parameter against its schema
    for key, value in params.items():
        prop_schema = properties.get(key)
        if prop_schema is None:
            # Unknown parameter — skip (don't block, modules may accept extras)
            continue

        path = f"params.{key}"
        issues.extend(_validate_value(value, prop_schema, path))

    return issues


def _validate_value(
    value: Any,
    schema: Dict[str, Any],
    path: str,
) -> List[ValidationIssue]:
    """
    Validate a single value against its property schema.

    Args:
        value: The value to validate
        schema: Property schema dict (type, minLength, maxLength, etc.)
        path: JSON path for error reporting

    Returns:
        List of ValidationIssue
    """
    issues: List[ValidationIssue] = []

    if value is None:
        # None values are handled by required check above
        return issues

    prop_type = schema.get("type", "string")
    label = schema.get("label", path.split(".")[-1])

    # --- Enum validation (applies to any type) ---
    enum_values = schema.get("enum")
    if enum_values is not None and isinstance(enum_values, list):
        if value not in enum_values:
            display = ", ".join(str(v) for v in enum_values[:10])
            suffix = f"... ({len(enum_values)} total)" if len(enum_values) > 10 else ""
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                path=path,
                message=f"Invalid value for {label}: must be one of [{display}{suffix}]",
                code="ENUM_MISMATCH",
                suggestion=f"Choose from: {display}",
            ))

    # --- String constraints ---
    if prop_type == "string" and isinstance(value, str):
        issues.extend(_validate_string(value, schema, path, label))

    # --- Number constraints ---
    elif prop_type in ("number", "integer") and isinstance(value, (int, float)):
        issues.extend(_validate_number(value, schema, path, label))

    # --- Array constraints ---
    elif prop_type == "array" and isinstance(value, list):
        issues.extend(_validate_array(value, schema, path, label))

    return issues


def _validate_string(
    value: str,
    schema: Dict[str, Any],
    path: str,
    label: str,
) -> List[ValidationIssue]:
    """Validate string value against minLength, maxLength, pattern."""
    issues: List[ValidationIssue] = []

    min_length = schema.get("minLength")
    if min_length is not None and len(value) < min_length:
        issues.append(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            path=path,
            message=f"{label} is too short ({len(value)} < {min_length} characters)",
            code="STRING_TOO_SHORT",
        ))

    max_length = schema.get("maxLength")
    if max_length is not None and len(value) > max_length:
        issues.append(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            path=path,
            message=f"{label} is too long ({len(value)} > {max_length} characters)",
            code="STRING_TOO_LONG",
        ))

    pattern = schema.get("pattern")
    if pattern is not None and isinstance(pattern, str):
        try:
            if not re.search(pattern, value):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    path=path,
                    message=f"{label} does not match required pattern: {pattern}",
                    code="PATTERN_MISMATCH",
                ))
        except re.error:
            logger.warning(f"Invalid regex pattern in schema for {path}: {pattern}")

    return issues


def _validate_number(
    value: Any,
    schema: Dict[str, Any],
    path: str,
    label: str,
) -> List[ValidationIssue]:
    """Validate number value against minimum, maximum."""
    issues: List[ValidationIssue] = []

    minimum = schema.get("minimum")
    if minimum is not None and value < minimum:
        issues.append(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            path=path,
            message=f"{label} is below minimum ({value} < {minimum})",
            code="NUMBER_TOO_SMALL",
        ))

    maximum = schema.get("maximum")
    if maximum is not None and value > maximum:
        issues.append(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            path=path,
            message=f"{label} exceeds maximum ({value} > {maximum})",
            code="NUMBER_TOO_LARGE",
        ))

    return issues


def _validate_array(
    value: list,
    schema: Dict[str, Any],
    path: str,
    label: str,
) -> List[ValidationIssue]:
    """Validate array value against minItems, maxItems."""
    issues: List[ValidationIssue] = []

    min_items = schema.get("minItems")
    if min_items is not None and len(value) < min_items:
        issues.append(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            path=path,
            message=f"{label} has too few items ({len(value)} < {min_items})",
            code="ARRAY_TOO_FEW",
        ))

    max_items = schema.get("maxItems")
    if max_items is not None and len(value) > max_items:
        issues.append(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            path=path,
            message=f"{label} has too many items ({len(value)} > {max_items})",
            code="ARRAY_TOO_MANY",
        ))

    return issues
