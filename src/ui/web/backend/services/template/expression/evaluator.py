"""
Secure Expression Evaluator

AST-based expression evaluation that prevents code injection.
"""

import ast
import logging
import re
from typing import Any, Dict, Optional, Union

from services.template.expression.models import (
    ExpressionConfig,
    ExpressionError,
    ExpressionType,
    SecurityViolation,
)
from services.template.expression.handlers import NODE_HANDLERS
from services.template.expression.operators import (
    SAFE_COLLECTION_METHODS,
    SAFE_STRING_METHODS,
)
from services.template.expression.resolver import preprocess_variables, resolve_variable_path

logger = logging.getLogger(__name__)


class SecureExpressionEvaluator:
    """
    AST-based secure expression evaluator.

    Evaluates expressions without using eval() or exec().
    Only allows whitelisted operations.

    Usage:
        evaluator = SecureExpressionEvaluator()

        # Evaluate condition
        result = evaluator.evaluate_condition(
            "${status} == 'completed'",
            {"status": "completed"}
        )  # Returns True

        # Evaluate arithmetic
        result = evaluator.evaluate_arithmetic(
            "${price} * ${quantity}",
            {"price": 10.5, "quantity": 3}
        )  # Returns 31.5

        # Interpolate string
        result = evaluator.interpolate(
            "Hello ${name}!",
            {"name": "World"}
        )  # Returns "Hello World!"
    """

    def __init__(self, config: Optional[ExpressionConfig] = None):
        """Initialize evaluator with configuration."""
        self.config = config or ExpressionConfig()
        self._depth = 0

    def evaluate_condition(
        self,
        expression: str,
        context: Dict[str, Any],
    ) -> bool:
        """
        Evaluate a boolean condition expression.

        Args:
            expression: Condition expression (e.g., "${x} > 10")
            context: Variable context

        Returns:
            Boolean result

        Raises:
            ExpressionError: If evaluation fails
            SecurityViolation: If expression contains disallowed operations
        """
        if not expression or not expression.strip():
            return True

        # Handle simple literals
        expr_lower = expression.strip().lower()
        if expr_lower in ("true", "1", "yes"):
            return True
        if expr_lower in ("false", "0", "no", "null", "none"):
            return False

        # Preprocess ${} variables
        processed = preprocess_variables(expression)

        # Parse and evaluate
        result = self._evaluate(processed, context, ExpressionType.CONDITION)
        return bool(result)

    def evaluate_arithmetic(
        self,
        expression: str,
        context: Dict[str, Any],
    ) -> Union[int, float]:
        """
        Evaluate an arithmetic expression.

        Args:
            expression: Arithmetic expression (e.g., "${x} + ${y} * 2")
            context: Variable context

        Returns:
            Numeric result

        Raises:
            ExpressionError: If evaluation fails
            SecurityViolation: If expression contains disallowed operations
        """
        if not expression or not expression.strip():
            return 0

        # Preprocess ${} variables
        processed = preprocess_variables(expression)

        # Parse and evaluate
        result = self._evaluate(processed, context, ExpressionType.ARITHMETIC)

        if not isinstance(result, (int, float)):
            raise ExpressionError(f"Expected numeric result, got {type(result)}")

        return result

    def interpolate(
        self,
        template: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Interpolate ${} variables in a string template.

        Args:
            template: String with ${variable} placeholders
            context: Variable context

        Returns:
            Interpolated string

        Raises:
            ExpressionError: If interpolation fails
        """
        if not template:
            return ""

        def replace_var(match):
            var_expr = match.group(1).strip()
            try:
                value = resolve_variable_path(var_expr, context)
                if value is None:
                    return ""
                return str(value)
            except Exception as e:
                logger.warning(f"Variable interpolation failed: {var_expr} -> {e}")
                return match.group(0)  # Keep original

        result = re.sub(r"\$\{([^}]+)\}", replace_var, template)

        # Enforce max length
        if len(result) > self.config.max_string_length:
            result = result[:self.config.max_string_length]
            logger.warning("Interpolation result truncated due to length limit")

        return result

    def _evaluate(
        self,
        expression: str,
        context: Dict[str, Any],
        expr_type: ExpressionType,
    ) -> Any:
        """Evaluate a preprocessed expression."""
        # Check length limit
        if len(expression) > self.config.max_length:
            raise SecurityViolation(
                f"Expression exceeds max length ({self.config.max_length})"
            )

        try:
            # Parse to AST
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as e:
            raise ExpressionError(f"Invalid expression syntax: {e}")

        # Create evaluation context
        eval_context = {"__ctx__": context}

        # Add safe builtins via lookup (no eval/exec — only whitelisted callables)
        _SAFE_BUILTINS = {
            "len": len, "str": str, "int": int, "float": float,
            "bool": bool, "min": min, "max": max, "abs": abs, "round": round,
        }
        if self.config.allowed_functions:
            for fn_name in self.config.allowed_functions:
                if fn_name in _SAFE_BUILTINS:
                    eval_context[fn_name] = _SAFE_BUILTINS[fn_name]

        # Evaluate
        self._depth = 0
        return self._eval_node(tree.body, eval_context)

    def _eval_node(self, node: ast.AST, context: Dict[str, Any]) -> Any:
        """Recursively evaluate an AST node."""
        self._depth += 1
        if self._depth > self.config.max_depth:
            raise SecurityViolation(f"Expression depth exceeds limit ({self.config.max_depth})")

        try:
            return self._dispatch_node(node, context)
        finally:
            self._depth -= 1

    def _dispatch_node(self, node: ast.AST, context: Dict[str, Any]) -> Any:
        """Dispatch evaluation to specific node handler."""
        handler = NODE_HANDLERS.get(type(node))
        if handler is None:
            raise SecurityViolation(f"AST node type not allowed: {type(node).__name__}")
        return handler(self, node, context)

    def _eval_call(self, node: ast.Call, context: Dict[str, Any]) -> Any:
        """Evaluate a function call node."""
        # Get function name
        if isinstance(node.func, ast.Name):
            fn_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            fn_name = node.func.attr
        else:
            raise SecurityViolation("Complex function calls not allowed")

        if fn_name not in self.config.allowed_functions:
            # Check if it's a method call on allowed types
            if isinstance(node.func, ast.Attribute):
                value = self._eval_node(node.func.value, context)
                if isinstance(value, str) and fn_name in SAFE_STRING_METHODS:
                    args = [self._eval_node(arg, context) for arg in node.args]
                    return getattr(value, fn_name)(*args)
                if isinstance(value, (list, dict)) and fn_name in SAFE_COLLECTION_METHODS:
                    args = [self._eval_node(arg, context) for arg in node.args]
                    return getattr(value, fn_name)(*args)

            raise SecurityViolation(f"Function not allowed: {fn_name}")

        # Evaluate function
        func = context.get(fn_name)
        if func is None:
            raise ExpressionError(f"Function not found: {fn_name}")

        args = [self._eval_node(arg, context) for arg in node.args]
        kwargs = {
            kw.arg: self._eval_node(kw.value, context)
            for kw in node.keywords
            if kw.arg is not None
        }

        return func(*args, **kwargs)
