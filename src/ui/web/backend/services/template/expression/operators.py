"""
Secure Expression Operators

Safe operator mappings and attribute whitelists.
"""

import ast
import operator
from typing import Callable, Dict, Set


# Safe binary operators
SAFE_BINARY_OPS: Dict[type, Callable] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.LShift: operator.lshift,
    ast.RShift: operator.rshift,
    ast.BitOr: operator.or_,
    ast.BitXor: operator.xor,
    ast.BitAnd: operator.and_,
}

# Safe comparison operators
SAFE_COMPARE_OPS: Dict[type, Callable] = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
    ast.In: lambda x, y: x in y,
    ast.NotIn: lambda x, y: x not in y,
}

# Safe unary operators
SAFE_UNARY_OPS: Dict[type, Callable] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Not: operator.not_,
    ast.Invert: operator.invert,
}

# Dangerous attribute names (never allow access)
DANGEROUS_ATTRS: Set[str] = {
    "__class__", "__bases__", "__mro__", "__subclasses__",
    "__init__", "__new__", "__del__", "__call__",
    "__getattr__", "__setattr__", "__delattr__",
    "__getattribute__", "__dict__", "__slots__",
    "__globals__", "__code__", "__func__", "__self__",
    "__builtins__", "__import__", "__loader__", "__spec__",
    "__file__", "__name__", "__doc__", "__module__",
    "__reduce__", "__reduce_ex__", "__getstate__", "__setstate__",
}

# Safe methods that can be called on strings
SAFE_STRING_METHODS: Set[str] = {
    "lower", "upper", "strip", "lstrip", "rstrip",
    "startswith", "endswith", "replace", "split", "join",
    "find", "rfind", "index", "rindex", "count",
    "isalpha", "isdigit", "isalnum", "isspace",
    "capitalize", "title", "swapcase",
}

# Safe methods that can be called on lists/dicts
SAFE_COLLECTION_METHODS: Set[str] = {
    "get", "keys", "values", "items",
    "index", "count", "copy",
}
