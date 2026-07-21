"""
Workflow Validator Package

JSON Schema-based validation for workflow definitions.
Prevents YAML/JSON injection attacks and ensures structural integrity.

Security features:
- Strict JSON Schema validation
- Module ID whitelist enforcement
- Parameter sanitization
- Maximum depth/size limits
- Dangerous pattern detection
"""

from services.template.validator.models import (
    ValidationSeverity,
    ValidationIssue,
    ValidationResult,
    ValidatorConfig,
)
from services.template.validator.schema import WORKFLOW_SCHEMA, DANGEROUS_PATTERNS
from services.template.validator.security import SecurityScanner
from services.template.validator.structure import (
    validate_basic_structure,
    validate_graph,
    validate_limits,
    validate_string_lengths,
    get_depth,
    sanitize_workflow,
)
from services.template.validator.params import validate_params_against_schema
from services.template.validator.validator import (
    WorkflowValidator,
    get_workflow_validator,
    validate_workflow,
    validate_params,
)

__all__ = [
    # Models
    "ValidationSeverity",
    "ValidationIssue",
    "ValidationResult",
    "ValidatorConfig",
    # Schema
    "WORKFLOW_SCHEMA",
    "DANGEROUS_PATTERNS",
    # Security
    "SecurityScanner",
    # Structure
    "validate_basic_structure",
    "validate_graph",
    "validate_limits",
    "validate_string_lengths",
    "get_depth",
    "sanitize_workflow",
    # Params
    "validate_params_against_schema",
    # Validator
    "WorkflowValidator",
    "get_workflow_validator",
    "validate_workflow",
    "validate_params",
]
