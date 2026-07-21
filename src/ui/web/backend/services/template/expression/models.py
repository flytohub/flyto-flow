"""
Secure Expression Models

Enums, exceptions, and configuration for expression evaluation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Set


class ExpressionError(Exception):
    """Raised when expression evaluation fails."""
    pass


class SecurityViolation(ExpressionError):
    """Raised when expression contains disallowed operations."""
    pass


class ExpressionType(str, Enum):
    """Type of expression being evaluated."""
    CONDITION = "condition"      # Boolean result expected
    ARITHMETIC = "arithmetic"    # Numeric result expected
    INTERPOLATION = "interpolation"  # String with ${} variables


@dataclass
class ExpressionConfig:
    """Configuration for expression evaluation."""
    max_length: int = 1000          # Maximum expression length
    max_depth: int = 10             # Maximum AST nesting depth
    max_string_length: int = 10000  # Maximum result string length
    allow_arithmetic: bool = True   # Allow +, -, *, /, %
    allow_comparison: bool = True   # Allow ==, !=, <, >, <=, >=
    allow_logical: bool = True      # Allow and, or, not
    allow_membership: bool = True   # Allow in, not in
    allow_indexing: bool = True     # Allow list[0], dict['key']
    allow_attribute: bool = False   # Allow obj.attr (restricted)
    allowed_functions: Set[str] = None  # Whitelisted functions

    def __post_init__(self):
        if self.allowed_functions is None:
            self.allowed_functions = {
                "len", "str", "int", "float", "bool",
                "min", "max", "abs", "round",
                "lower", "upper", "strip",
            }
