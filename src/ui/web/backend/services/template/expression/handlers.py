"""AST node type handlers for SecureExpressionEvaluator."""

import ast
from typing import Any, Dict

from services.template.expression.models import (
    ExpressionError,
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


def _eval_constant(evaluator, node: ast.Constant, context: Dict[str, Any]) -> Any:
    return node.value


def _eval_num(evaluator, node: ast.Num, context: Dict[str, Any]) -> Any:
    """Python 3.7 compatibility."""
    return node.n


def _eval_str(evaluator, node: ast.Str, context: Dict[str, Any]) -> Any:
    """Python 3.7 compatibility."""
    return node.s


def _eval_nameconstant(evaluator, node: ast.NameConstant, context: Dict[str, Any]) -> Any:
    """Python 3.7 compatibility."""
    return node.value


def _eval_name(evaluator, node: ast.Name, context: Dict[str, Any]) -> Any:
    name = node.id
    if name not in context:
        raise ExpressionError(f"Undefined variable: {name}")
    return context[name]


def _eval_binop(evaluator, node: ast.BinOp, context: Dict[str, Any]) -> Any:
    if not evaluator.config.allow_arithmetic:
        raise SecurityViolation("Arithmetic operations not allowed")

    op_type = type(node.op)
    if op_type not in SAFE_BINARY_OPS:
        raise SecurityViolation(f"Operator not allowed: {op_type.__name__}")

    left = evaluator._eval_node(node.left, context)
    right = evaluator._eval_node(node.right, context)
    return SAFE_BINARY_OPS[op_type](left, right)


def _eval_unaryop(evaluator, node: ast.UnaryOp, context: Dict[str, Any]) -> Any:
    op_type = type(node.op)
    if op_type not in SAFE_UNARY_OPS:
        raise SecurityViolation(f"Operator not allowed: {op_type.__name__}")

    if op_type == ast.Not and not evaluator.config.allow_logical:
        raise SecurityViolation("Logical operations not allowed")

    operand = evaluator._eval_node(node.operand, context)
    return SAFE_UNARY_OPS[op_type](operand)


def _eval_compare(evaluator, node: ast.Compare, context: Dict[str, Any]) -> Any:
    if not evaluator.config.allow_comparison:
        raise SecurityViolation("Comparison operations not allowed")

    left = evaluator._eval_node(node.left, context)

    for op, comparator in zip(node.ops, node.comparators):
        op_type = type(op)
        if op_type not in SAFE_COMPARE_OPS:
            raise SecurityViolation(f"Operator not allowed: {op_type.__name__}")

        # Check membership operator permission
        if op_type in (ast.In, ast.NotIn) and not evaluator.config.allow_membership:
            raise SecurityViolation("Membership operations not allowed")

        right = evaluator._eval_node(comparator, context)
        if not SAFE_COMPARE_OPS[op_type](left, right):
            return False
        left = right

    return True


def _eval_boolop(evaluator, node: ast.BoolOp, context: Dict[str, Any]) -> Any:
    if not evaluator.config.allow_logical:
        raise SecurityViolation("Logical operations not allowed")

    if isinstance(node.op, ast.And):
        for value in node.values:
            if not evaluator._eval_node(value, context):
                return False
        return True
    elif isinstance(node.op, ast.Or):
        for value in node.values:
            if evaluator._eval_node(value, context):
                return True
        return False


def _eval_ifexp(evaluator, node: ast.IfExp, context: Dict[str, Any]) -> Any:
    test = evaluator._eval_node(node.test, context)
    if test:
        return evaluator._eval_node(node.body, context)
    else:
        return evaluator._eval_node(node.orelse, context)


def _eval_subscript(evaluator, node: ast.Subscript, context: Dict[str, Any]) -> Any:
    if not evaluator.config.allow_indexing:
        raise SecurityViolation("Indexing not allowed")

    value = evaluator._eval_node(node.value, context)

    # Handle slice
    if isinstance(node.slice, ast.Index):  # Python 3.8 compatibility
        idx = evaluator._eval_node(node.slice.value, context)
    elif isinstance(node.slice, ast.Slice):
        lower = evaluator._eval_node(node.slice.lower, context) if node.slice.lower else None
        upper = evaluator._eval_node(node.slice.upper, context) if node.slice.upper else None
        step = evaluator._eval_node(node.slice.step, context) if node.slice.step else None
        return value[lower:upper:step]
    else:
        idx = evaluator._eval_node(node.slice, context)

    try:
        return value[idx]
    except (KeyError, IndexError, TypeError):
        return None


def _eval_attribute(evaluator, node: ast.Attribute, context: Dict[str, Any]) -> Any:
    if not evaluator.config.allow_attribute:
        raise SecurityViolation("Attribute access not allowed")

    attr_name = node.attr
    if attr_name in DANGEROUS_ATTRS:
        raise SecurityViolation(f"Dangerous attribute access: {attr_name}")

    value = evaluator._eval_node(node.value, context)

    # Only allow safe methods
    if isinstance(value, str) and attr_name in SAFE_STRING_METHODS:
        return getattr(value, attr_name)
    if isinstance(value, (list, dict)) and attr_name in SAFE_COLLECTION_METHODS:
        return getattr(value, attr_name)

    raise SecurityViolation(f"Attribute access not allowed: {attr_name}")


def _eval_call(evaluator, node: ast.Call, context: Dict[str, Any]) -> Any:
    return evaluator._eval_call(node, context)


def _eval_list(evaluator, node: ast.List, context: Dict[str, Any]) -> Any:
    return [evaluator._eval_node(elt, context) for elt in node.elts]


def _eval_tuple(evaluator, node: ast.Tuple, context: Dict[str, Any]) -> Any:
    return tuple(evaluator._eval_node(elt, context) for elt in node.elts)


def _eval_dict(evaluator, node: ast.Dict, context: Dict[str, Any]) -> Any:
    return {
        evaluator._eval_node(k, context): evaluator._eval_node(v, context)
        for k, v in zip(node.keys, node.values)
        if k is not None
    }


def _eval_set(evaluator, node: ast.Set, context: Dict[str, Any]) -> Any:
    return {evaluator._eval_node(elt, context) for elt in node.elts}


NODE_HANDLERS = {
    ast.Constant: _eval_constant,
    ast.Num: _eval_num,
    ast.Str: _eval_str,
    ast.NameConstant: _eval_nameconstant,
    ast.Name: _eval_name,
    ast.BinOp: _eval_binop,
    ast.UnaryOp: _eval_unaryop,
    ast.Compare: _eval_compare,
    ast.BoolOp: _eval_boolop,
    ast.IfExp: _eval_ifexp,
    ast.Subscript: _eval_subscript,
    ast.Attribute: _eval_attribute,
    ast.Call: _eval_call,
    ast.List: _eval_list,
    ast.Tuple: _eval_tuple,
    ast.Dict: _eval_dict,
    ast.Set: _eval_set,
}
