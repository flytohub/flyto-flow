"""
Secure Expression Variable Resolver

Variable path resolution and preprocessing.
"""

import re
from typing import Any, Dict, Optional

from services.template.expression.operators import DANGEROUS_ATTRS


def preprocess_variables(expression: str) -> str:
    """
    Convert ${var} syntax to __ctx__['var'] for AST parsing.

    Handles nested paths: ${user.name} -> __ctx__['user']['name']
    """
    def convert_var(match):
        var_path = match.group(1).strip()
        parts = var_path.split(".")
        result = "__ctx__"
        for part in parts:
            # Handle array indexing: items[0] -> ['items'][0]
            if "[" in part:
                base, idx = part.split("[", 1)
                result += f"['{base}'][{idx}"
            else:
                result += f"['{part}']"
        return result

    # Also handle [[var]] syntax (UI variable references)
    result = re.sub(r"\$\{([^}]+)\}", convert_var, expression)
    result = re.sub(r"\[\[([^\]]+)\]\]", convert_var, result)

    return result


def resolve_variable_path(
    path: str,
    context: Dict[str, Any],
) -> Optional[Any]:
    """
    Resolve a dot-notation variable path.

    Args:
        path: Variable path (e.g., "user.profile.name")
        context: Variable context

    Returns:
        Resolved value or None
    """
    parts = path.split(".")
    current = context

    for part in parts:
        # Handle array indexing: items[0]
        if "[" in part:
            base, rest = part.split("[", 1)
            idx_str = rest.rstrip("]")

            # Get base value
            if isinstance(current, dict):
                current = current.get(base)
            else:
                return None

            if current is None:
                return None

            # Get indexed value
            try:
                idx = int(idx_str)
                current = current[idx]
            except (ValueError, IndexError, TypeError):
                return None
        else:
            if isinstance(current, dict):
                current = current.get(part)
            elif hasattr(current, part) and part not in DANGEROUS_ATTRS:
                current = getattr(current, part)
            else:
                return None

        if current is None:
            return None

    return current
