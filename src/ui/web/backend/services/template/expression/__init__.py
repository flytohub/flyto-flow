"""
Secure Expression Package

AST-based expression evaluation that prevents code injection.
"""

from typing import Any, Dict, Optional, Union

from services.template.expression.models import (
    ExpressionConfig,
    ExpressionError,
    ExpressionType,
    SecurityViolation,
)
from services.template.expression.operators import (
    DANGEROUS_ATTRS,
    SAFE_BINARY_OPS,
    SAFE_COLLECTION_METHODS,
    SAFE_COMPARE_OPS,
    SAFE_STRING_METHODS,
    SAFE_UNARY_OPS,
)
from services.template.expression.resolver import preprocess_variables, resolve_variable_path
from services.template.expression.evaluator import SecureExpressionEvaluator


# Global evaluator instance
_evaluator: Optional[SecureExpressionEvaluator] = None


def get_secure_evaluator() -> SecureExpressionEvaluator:
    """Get or create global secure evaluator."""
    global _evaluator
    if _evaluator is None:
        _evaluator = SecureExpressionEvaluator()
    return _evaluator


def evaluate_condition(expression: str, context: Dict[str, Any]) -> bool:
    """Convenience function to evaluate a condition."""
    return get_secure_evaluator().evaluate_condition(expression, context)


def interpolate_variables(template: str, context: Dict[str, Any]) -> str:
    """Convenience function to interpolate variables."""
    return get_secure_evaluator().interpolate(template, context)


def evaluate_arithmetic(expression: str, context: Dict[str, Any]) -> Union[int, float]:
    """Convenience function to evaluate arithmetic."""
    return get_secure_evaluator().evaluate_arithmetic(expression, context)


__all__ = [
    # Models
    "ExpressionConfig",
    "ExpressionError",
    "ExpressionType",
    "SecurityViolation",
    # Operators
    "DANGEROUS_ATTRS",
    "SAFE_BINARY_OPS",
    "SAFE_COLLECTION_METHODS",
    "SAFE_COMPARE_OPS",
    "SAFE_STRING_METHODS",
    "SAFE_UNARY_OPS",
    # Resolver
    "preprocess_variables",
    "resolve_variable_path",
    # Evaluator
    "SecureExpressionEvaluator",
    # Convenience
    "get_secure_evaluator",
    "evaluate_condition",
    "interpolate_variables",
    "evaluate_arithmetic",
]
