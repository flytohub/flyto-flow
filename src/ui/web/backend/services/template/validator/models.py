"""
Validation Data Models

Enums and dataclasses for workflow validation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class ValidationSeverity(str, Enum):
    """Severity level for validation issues."""
    ERROR = "error"       # Blocks execution
    WARNING = "warning"   # Allows execution with caution
    INFO = "info"         # Informational only


@dataclass
class ValidationIssue:
    """A single validation issue."""
    severity: ValidationSeverity
    path: str              # JSON path to issue location
    message: str
    code: str              # Machine-readable error code
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert validation issue to dictionary."""
        return {
            "severity": self.severity.value,
            "path": self.path,
            "message": self.message,
            "code": self.code,
            "suggestion": self.suggestion,
        }


@dataclass
class ValidationResult:
    """Result of workflow validation."""
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    sanitized: Optional[Dict[str, Any]] = None  # Sanitized workflow

    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary with issue counts."""
        return {
            "valid": self.valid,
            "issues": [i.to_dict() for i in self.issues],
            "error_count": len([i for i in self.issues if i.severity == ValidationSeverity.ERROR]),
            "warning_count": len([i for i in self.issues if i.severity == ValidationSeverity.WARNING]),
        }


@dataclass
class ValidatorConfig:
    """Configuration for workflow validation."""
    max_depth: int = 20                    # Maximum nesting depth
    max_nodes: int = 500                   # Maximum number of nodes
    max_edges: int = 1000                  # Maximum number of edges
    max_string_length: int = 10000         # Maximum string length
    max_params_size: int = 100000          # Maximum params JSON size
    allowed_modules: Optional[Set[str]] = None  # Whitelist of allowed modules
    blocked_modules: Set[str] = field(default_factory=set)  # Blocked modules
    enable_sanitization: bool = True       # Auto-sanitize inputs
    strict_mode: bool = False              # Fail on warnings

    def __post_init__(self):
        """Initialize default blocked modules if none provided."""
        # Default blocked modules (dangerous operations)
        if not self.blocked_modules:
            self.blocked_modules = {
                "code.eval",
                "code.exec",
                "system.shell_unsafe",
                "file.delete_recursive",
            }
