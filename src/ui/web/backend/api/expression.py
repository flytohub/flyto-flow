"""
Expression Evaluation API

Secure expression evaluation endpoints.
All expression parsing and evaluation is done server-side.
Frontend should send expressions to this API rather than evaluating locally.

v1: Initial implementation for frontend architecture audit.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.auth import get_current_user
from api.responses import success_response, error_response
from services.template.expression.evaluator import SecureExpressionEvaluator
from services.template.expression.models import ExpressionError, SecurityViolation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/expression", tags=["Expression"])


class ExpressionEvaluateRequest(BaseModel):
    """Request to evaluate an expression"""
    expression: str = Field(..., description="Expression to evaluate (e.g., '${status} == \"completed\"')")
    context: Dict[str, Any] = Field(default_factory=dict, description="Variable context for evaluation")
    type: str = Field("auto", description="Expression type: 'condition', 'arithmetic', 'interpolate', or 'auto'")


class ExpressionValidateRequest(BaseModel):
    """Request to validate expression syntax"""
    expression: str = Field(..., description="Expression to validate")


class ExpressionBatchRequest(BaseModel):
    """Request to evaluate multiple expressions"""
    expressions: Dict[str, str] = Field(..., description="Map of key -> expression")
    context: Dict[str, Any] = Field(default_factory=dict, description="Shared context")


@router.post("/evaluate")
async def evaluate_expression(
    request: ExpressionEvaluateRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Evaluate an expression with the given context.

    The expression can be:
    - A condition: "${status} == 'completed'" -> returns boolean
    - Arithmetic: "${price} * ${quantity}" -> returns number
    - Interpolation: "Hello ${name}!" -> returns string
    - Auto (default): Tries to determine type automatically

    All evaluation is done securely server-side using AST parsing.
    No eval() or exec() is ever used.
    """
    evaluator = SecureExpressionEvaluator()

    try:
        expr_type = request.type.lower()

        if expr_type == "condition":
            result = evaluator.evaluate_condition(request.expression, request.context)
        elif expr_type == "arithmetic":
            result = evaluator.evaluate_arithmetic(request.expression, request.context)
        elif expr_type == "interpolate":
            result = evaluator.interpolate(request.expression, request.context)
        else:  # auto
            # Try to detect type
            expr = request.expression.strip()
            if any(op in expr for op in ["==", "!=", ">", "<", ">=", "<=", " and ", " or ", " in "]):
                result = evaluator.evaluate_condition(expr, request.context)
            elif any(op in expr for op in ["+", "-", "*", "/", "%", "**"]) and "${" in expr:
                # Likely arithmetic if has math operators and variables
                try:
                    result = evaluator.evaluate_arithmetic(expr, request.context)
                except (ExpressionError, SecurityViolation):
                    result = evaluator.interpolate(expr, request.context)
            else:
                result = evaluator.interpolate(expr, request.context)

        return success_response(
            result=result,
            result_type=type(result).__name__,
            expression=request.expression
        )

    except ExpressionError as e:
        return error_response(
            error=str(e),
            error_type="expression_error"
        )
    except SecurityViolation as e:
        return error_response(
            error=str(e),
            error_type="security_violation"
        )
    except Exception as e:
        logger.exception(f"Expression evaluation failed: {e}")
        return error_response(
            error=f"Evaluation failed: {str(e)}",
            error_type="unknown_error"
        )


@router.post("/validate")
async def validate_expression(
    request: ExpressionValidateRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Validate expression syntax without evaluating.

    Returns validation result with:
    - valid: boolean indicating if syntax is correct
    - variables: list of variables found in expression
    - warnings: any potential issues detected
    """
    import re

    expr = request.expression.strip()
    warnings = []
    variables = []

    # Extract ${variable} references
    var_pattern = r'\$\{([^}]+)\}'
    matches = re.findall(var_pattern, expr)
    variables = list(set(matches))

    # Basic syntax checks
    valid = True
    error = None

    # Check balanced braces
    open_count = expr.count('${')
    close_count = expr.count('}')
    if open_count != close_count:
        valid = False
        error = "Unbalanced braces in expression"

    # Check for empty variables
    if '${}'  in expr:
        valid = False
        error = "Empty variable reference ${}"

    # Try to parse as Python expression (if it looks like one)
    if valid and any(op in expr for op in ["==", "!=", ">", "<", "+", "-", "*", "/"]):
        try:
            # Preprocess variables for AST parsing
            from services.template.expression.resolver import preprocess_variables
            processed = preprocess_variables(expr)
            import ast
            ast.parse(processed, mode="eval")
        except SyntaxError as e:
            valid = False
            error = f"Invalid syntax: {e.msg}"
        except Exception:
            pass  # Not a parseable expression, but might still be valid template

    # Detect potential code injection (block dangerous patterns)
    _BLOCKED_PATTERNS = [
        "eval(", "exec(", "compile(", "__import__(",
        "getattr(", "setattr(", "delattr(",
        "globals(", "locals(", "vars(",
        "open(", "subprocess", "os.system", "os.popen",
    ]
    for pattern in _BLOCKED_PATTERNS:
        if pattern in expr:
            valid = False
            error = f"Expression contains blocked pattern: {pattern.rstrip('(')}"
            break
    if "__" in expr:
        valid = False
        error = "Dunder attributes are not allowed"

    return success_response(
        valid=valid,
        error=error,
        variables=variables,
        warnings=warnings
    )


@router.post("/batch")
async def evaluate_batch(
    request: ExpressionBatchRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Evaluate multiple expressions with a shared context.

    Useful for evaluating all parameter expressions for a workflow node.
    """
    evaluator = SecureExpressionEvaluator()
    results = {}
    errors = {}

    for key, expression in request.expressions.items():
        try:
            # Default to interpolation for batch (most common use case)
            result = evaluator.interpolate(expression, request.context)
            results[key] = result
        except (ExpressionError, SecurityViolation) as e:
            errors[key] = str(e)
        except Exception as e:
            errors[key] = f"Evaluation failed: {str(e)}"

    return success_response(
        results=results,
        errors=errors,
        ok=len(errors) == 0
    )


@router.get("/functions")
async def list_allowed_functions(
    _: dict = Depends(get_current_user),
):
    """
    List allowed functions in expressions.

    Returns the whitelist of safe functions that can be used in expressions.
    """
    from services.template.expression.models import ExpressionConfig

    config = ExpressionConfig()
    return success_response(
        allowed_functions=list(config.allowed_functions),
        description="These functions can be used in expressions. Example: len(${items})"
    )
