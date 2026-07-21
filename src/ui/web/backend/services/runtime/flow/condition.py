"""Condition Evaluation"""

from typing import Any, Dict, List


class ConditionEvaluator:
    """
    Safe condition evaluation for flow control.

    Supports:
    - Comparison operators: ==, !=, <, >, <=, >=
    - Logical operators: and, or, not
    - Variable references: ${variable.path}
    - Literals: strings, numbers, booleans
    """

    # Allowed operators
    OPERATORS = {
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        "<": lambda a, b: a < b,
        ">": lambda a, b: a > b,
        "<=": lambda a, b: a <= b,
        ">=": lambda a, b: a >= b,
    }

    @classmethod
    def evaluate(cls, expression: str, context: Dict[str, Any]) -> bool:
        """
        Evaluate a condition expression.

        Args:
            expression: Condition expression
            context: Variable context

        Returns:
            Boolean result

        Examples:
            "${status} == 'completed'"
            "${count} > 10"
            "${data.items} != null"
        """
        if not expression:
            return True

        # Simple true/false
        expr_lower = expression.strip().lower()
        if expr_lower == "true":
            return True
        if expr_lower == "false":
            return False

        # Handle 'and' / 'or'
        if " and " in expression.lower():
            parts = expression.lower().split(" and ")
            return all(cls.evaluate(p.strip(), context) for p in parts)

        if " or " in expression.lower():
            parts = expression.lower().split(" or ")
            return any(cls.evaluate(p.strip(), context) for p in parts)

        # Handle 'not'
        if expression.lower().startswith("not "):
            return not cls.evaluate(expression[4:].strip(), context)

        # Find operator
        for op, func in cls.OPERATORS.items():
            if op in expression:
                parts = expression.split(op, 1)
                if len(parts) == 2:
                    left = cls._resolve_value(parts[0].strip(), context)
                    right = cls._resolve_value(parts[1].strip(), context)
                    return func(left, right)

        # No operator - treat as truthy check
        value = cls._resolve_value(expression, context)
        return bool(value)

    @classmethod
    def _resolve_value(cls, token: str, context: Dict[str, Any]) -> Any:
        """Resolve a token to its value."""
        token = token.strip()

        # Variable reference
        if token.startswith("${") and token.endswith("}"):
            path = token[2:-1]
            return cls._get_nested_value(context, path)

        # String literal
        if (token.startswith("'") and token.endswith("'")) or \
           (token.startswith('"') and token.endswith('"')):
            return token[1:-1]

        # Null
        if token.lower() == "null" or token.lower() == "none":
            return None

        # Boolean
        if token.lower() == "true":
            return True
        if token.lower() == "false":
            return False

        # Number
        try:
            if "." in token:
                return float(token)
            return int(token)
        except ValueError:
            pass

        # Bare variable name
        return cls._get_nested_value(context, token)

    @classmethod
    def _get_nested_value(cls, obj: Dict, path: str) -> Any:
        """Get nested value from dict using dot notation."""
        from core.engine.variable_resolver import VariableResolver
        return VariableResolver.get_nested_value(obj, path)
