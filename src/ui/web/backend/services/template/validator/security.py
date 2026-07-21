"""
Security Validation

Pattern scanning and security checks for workflow validation.
"""

import re
from typing import Any, List, Pattern, Tuple

from services.template.validator.models import ValidationIssue, ValidationSeverity, ValidatorConfig
from services.template.validator.schema import DANGEROUS_PATTERNS


class SecurityScanner:
    """
    Scans workflow content for security issues.

    Detects:
    - Code injection patterns
    - Template injection
    - Path traversal
    - Command injection
    - SQL injection
    - SSRF patterns
    """

    def __init__(self, config: ValidatorConfig):
        """Initialize with validator config."""
        self.config = config

        # Compile dangerous patterns for performance
        self._compiled_patterns: List[Tuple[Pattern, str, str]] = [
            (re.compile(pattern, re.IGNORECASE), code, msg)
            for pattern, code, msg in DANGEROUS_PATTERNS
        ]

    def scan_for_patterns(
        self,
        obj: Any,
        path: str,
    ) -> List[ValidationIssue]:
        """
        Recursively scan for dangerous patterns.

        Args:
            obj: Object to scan (string, dict, or list)
            path: JSON path for error reporting

        Returns:
            List of security issues found
        """
        issues = []

        if isinstance(obj, str):
            for pattern, code, message in self._compiled_patterns:
                if pattern.search(obj):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        path=path,
                        message=message,
                        code=code,
                        suggestion="Remove or escape the suspicious content",
                    ))
        elif isinstance(obj, dict):
            for key, value in obj.items():
                # Also check keys for dangerous patterns
                for pattern, code, message in self._compiled_patterns:
                    if pattern.search(str(key)):
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            path=f"{path}.{key}",
                            message=f"Dangerous pattern in key: {message}",
                            code=code,
                        ))
                issues.extend(self.scan_for_patterns(value, f"{path}.{key}"))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                issues.extend(self.scan_for_patterns(item, f"{path}[{i}]"))

        return issues

    def validate_modules(
        self,
        nodes: List[dict],
    ) -> List[ValidationIssue]:
        """
        Validate module references against whitelist/blocklist.

        Args:
            nodes: List of workflow nodes

        Returns:
            List of module validation issues
        """
        issues = []

        for i, node in enumerate(nodes):
            module_id = node.get("module", "")

            # Check if module is blocked
            if module_id in self.config.blocked_modules:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    path=f"$.nodes[{i}].module",
                    message=f"Module '{module_id}' is blocked for security reasons",
                    code="BLOCKED_MODULE",
                ))

            # Check whitelist if configured
            if self.config.allowed_modules is not None:
                if module_id not in self.config.allowed_modules:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        path=f"$.nodes[{i}].module",
                        message=f"Module '{module_id}' is not in allowed list",
                        code="MODULE_NOT_ALLOWED",
                    ))

            # Validate module ID format
            if not re.match(r"^[a-zA-Z0-9_.:-]{1,100}$", module_id):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    path=f"$.nodes[{i}].module",
                    message=f"Invalid module ID format: {module_id}",
                    code="INVALID_MODULE_ID",
                ))

        return issues
