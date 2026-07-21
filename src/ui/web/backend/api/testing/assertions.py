"""
Testing Assertions

Assertion evaluation logic for test assertions.
"""

import re
from typing import Any, Callable, Dict, Tuple


def _assert_equals(actual_value: Any, expected: Any, field: str) -> Tuple[bool, str]:
    passed = actual_value == expected
    message = "" if passed else f"Expected {expected}, got {actual_value}"
    return passed, message


def _assert_not_equals(actual_value: Any, expected: Any, field: str) -> Tuple[bool, str]:
    passed = actual_value != expected
    message = "" if passed else f"Expected not {expected}, but got {actual_value}"
    return passed, message


def _assert_contains(actual_value: Any, expected: Any, field: str) -> Tuple[bool, str]:
    if isinstance(actual_value, (str, list, dict)):
        passed = expected in actual_value
    else:
        passed = False
    message = "" if passed else f"Expected {actual_value} to contain {expected}"
    return passed, message


def _assert_not_null(actual_value: Any, expected: Any, field: str) -> Tuple[bool, str]:
    passed = actual_value is not None
    message = "" if passed else f"Expected {field} to not be null"
    return passed, message


def _assert_type(actual_value: Any, expected: Any, field: str) -> Tuple[bool, str]:
    type_map = {
        'string': str,
        'number': (int, float),
        'integer': int,
        'boolean': bool,
        'array': list,
        'object': dict,
    }
    expected_type = type_map.get(expected)
    if expected_type:
        passed = isinstance(actual_value, expected_type)
    else:
        passed = False
    message = "" if passed else f"Expected {field} to be {expected}, got {type(actual_value).__name__}"
    return passed, message


def _assert_greater_than(actual_value: Any, expected: Any, field: str) -> Tuple[bool, str]:
    passed = actual_value is not None and actual_value > expected
    message = "" if passed else f"Expected {actual_value} > {expected}"
    return passed, message


def _assert_less_than(actual_value: Any, expected: Any, field: str) -> Tuple[bool, str]:
    passed = actual_value is not None and actual_value < expected
    message = "" if passed else f"Expected {actual_value} < {expected}"
    return passed, message


def _assert_regex(actual_value: Any, expected: Any, field: str) -> Tuple[bool, str]:
    if isinstance(actual_value, str):
        passed = bool(re.search(expected, actual_value))
    else:
        passed = False
    message = "" if passed else f"Expected {actual_value} to match regex {expected}"
    return passed, message


_ASSERTION_HANDLERS: Dict[str, Callable[[Any, Any, str], Tuple[bool, str]]] = {
    'equals': _assert_equals,
    'not_equals': _assert_not_equals,
    'contains': _assert_contains,
    'not_null': _assert_not_null,
    'type': _assert_type,
    'greater_than': _assert_greater_than,
    'less_than': _assert_less_than,
    'regex': _assert_regex,
}


def evaluate_assertion(assertion: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate a single assertion against actual data.

    Args:
        assertion: Assertion definition with type, field, expected
        actual: Actual output data to check against

    Returns:
        Result dict with passed, message, actual, expected
    """
    assertion_type = assertion.get('type', 'equals')
    field = assertion.get('field', '')
    expected = assertion.get('expected')

    # Get actual value using dot notation
    actual_value = actual
    for part in field.split('.'):
        if isinstance(actual_value, dict):
            actual_value = actual_value.get(part)
        else:
            actual_value = None
            break

    result = {
        "field": field,
        "type": assertion_type,
        "expected": expected,
        "actual": actual_value,
        "passed": False,
        "message": "",
    }

    try:
        handler = _ASSERTION_HANDLERS.get(assertion_type)
        if handler:
            result["passed"], result["message"] = handler(actual_value, expected, field)
        else:
            result["message"] = f"Unknown assertion type: {assertion_type}"

    except Exception as e:
        result["message"] = f"Assertion error: {str(e)}"

    return result
