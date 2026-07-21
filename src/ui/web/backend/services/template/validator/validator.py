"""
Workflow Validator

Main validator class combining all validation components.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from services.template.validator.models import (
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
    ValidatorConfig,
)
from services.template.validator.schema import WORKFLOW_SCHEMA
from services.template.validator.security import SecurityScanner
from services.template.validator.structure import (
    validate_basic_structure,
    validate_graph,
    validate_limits,
    validate_resource_edges,
    sanitize_workflow,
)

logger = logging.getLogger(__name__)

# Try to import jsonschema for full validation
try:
    from jsonschema import Draft7Validator
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    logger.warning("jsonschema library not found, using basic validation")


class WorkflowValidator:
    """
    Validates workflow definitions against JSON Schema and security rules.

    Features:
    - JSON Schema validation (Draft-07)
    - Security pattern scanning
    - Module whitelist/blocklist
    - Size and depth limits
    - Automatic sanitization

    Usage:
        validator = WorkflowValidator()
        result = validator.validate(workflow_dict)

        if not result.valid:
            for issue in result.issues:
                print(f"{issue.severity}: {issue.message}")
    """

    def __init__(self, config: Optional[ValidatorConfig] = None):
        """Initialize validator with configuration."""
        self.config = config or ValidatorConfig()

        # Initialize security scanner
        self._security_scanner = SecurityScanner(self.config)

        # Create JSON Schema validator if available
        if HAS_JSONSCHEMA:
            self._schema_validator = Draft7Validator(WORKFLOW_SCHEMA)
        else:
            self._schema_validator = None

    def validate(self, workflow: Dict[str, Any]) -> ValidationResult:
        """
        Validate a workflow definition.

        Args:
            workflow: Workflow dictionary to validate

        Returns:
            ValidationResult with issues and optional sanitized workflow
        """
        issues: List[ValidationIssue] = []

        # 1. Basic structure validation
        issues.extend(validate_basic_structure(workflow))

        # 2. JSON Schema validation
        if self._schema_validator:
            issues.extend(self._validate_schema(workflow))

        # 3. Security validation
        issues.extend(self._security_scanner.scan_for_patterns(workflow, "$"))

        # 4. Module validation
        nodes = workflow.get("nodes", [])
        issues.extend(self._security_scanner.validate_modules(nodes))

        # 5. Graph validation
        issues.extend(validate_graph(workflow))

        # 6. Resource edge semantic validation
        issues.extend(validate_resource_edges(workflow))

        # 7. Size limits validation
        issues.extend(validate_limits(workflow, self.config))

        # Determine validity
        error_count = len([i for i in issues if i.severity == ValidationSeverity.ERROR])
        warning_count = len([i for i in issues if i.severity == ValidationSeverity.WARNING])

        valid = error_count == 0
        if self.config.strict_mode and warning_count > 0:
            valid = False

        # Sanitize if enabled and valid
        sanitized = None
        if self.config.enable_sanitization and valid:
            sanitized = sanitize_workflow(workflow, self.config.max_string_length)

        return ValidationResult(
            valid=valid,
            issues=issues,
            sanitized=sanitized,
        )

    def validate_params(
        self,
        module_id: str,
        params: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate module parameters.

        Performs schema-aware validation when the module's paramsSchema is
        available in the registry, checking constraints like minLength,
        maxLength, minimum, maximum, pattern, enum, etc.

        Args:
            module_id: Module identifier
            params: Parameter dictionary

        Returns:
            ValidationResult
        """
        issues: List[ValidationIssue] = []

        # Check params size (safety limit regardless of schema)
        params_json = json.dumps(params)
        if len(params_json) > self.config.max_params_size:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                path="params",
                message=f"Parameters exceed maximum size ({len(params_json)} > {self.config.max_params_size})",
                code="PARAMS_TOO_LARGE",
            ))

        # Check for dangerous patterns in params (warning-level — informational,
        # does not block execution since legitimate params may match patterns)
        security_issues = self._security_scanner.scan_for_patterns(params, "params")
        for issue in security_issues:
            issue.severity = ValidationSeverity.WARNING
        issues.extend(security_issues)

        # Schema-aware validation: check constraints from the module's paramsSchema
        params_schema = self._get_params_schema(module_id)
        if params_schema:
            from services.template.validator.params import validate_params_against_schema
            issues.extend(validate_params_against_schema(params, params_schema))

        valid = len([i for i in issues if i.severity == ValidationSeverity.ERROR]) == 0

        return ValidationResult(valid=valid, issues=issues)

    def _get_params_schema(self, module_id: str) -> Optional[Dict[str, Any]]:
        """
        Try to retrieve the paramsSchema for a module from the registry.

        Args:
            module_id: Module identifier (e.g. "browser.goto")

        Returns:
            Normalized paramsSchema dict, or None if unavailable
        """
        try:
            from services.registry_loader import get_module_registry
            registry = get_module_registry()
            if registry is None:
                return None
            metadata = registry.get_metadata(module_id)
            if metadata is None:
                return None
            # The metadata may store schema under different keys
            return (
                metadata.get("params_schema")
                or metadata.get("paramsSchema")
                or metadata.get("ui_params_schema")
                or None
            )
        except Exception:
            logger.debug(f"Could not load paramsSchema for {module_id}", exc_info=True)
            return None

    def _validate_schema(self, workflow: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate against JSON Schema."""
        issues = []

        if not self._schema_validator:
            return issues

        errors = list(self._schema_validator.iter_errors(workflow))
        for error in errors:
            path = ".".join(str(p) for p in error.absolute_path) or "$"
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                path=path,
                message=error.message,
                code="SCHEMA_VIOLATION",
            ))

        return issues


# Global validator instance
_validator: Optional[WorkflowValidator] = None


def get_workflow_validator() -> WorkflowValidator:
    """Get or create global workflow validator."""
    global _validator
    if _validator is None:
        _validator = WorkflowValidator()
    return _validator


def validate_workflow(workflow: Dict[str, Any]) -> ValidationResult:
    """Convenience function to validate a workflow."""
    return get_workflow_validator().validate(workflow)


def validate_params(module_id: str, params: Dict[str, Any]) -> ValidationResult:
    """Convenience function to validate module parameters."""
    return get_workflow_validator().validate_params(module_id, params)
