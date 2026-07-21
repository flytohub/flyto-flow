"""
YAML Security Utilities

Provides secure YAML parsing with validation for workflow definitions.
Prevents YAML injection and enforces module whitelisting.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set

import yaml

logger = logging.getLogger(__name__)

# Maximum YAML size (1MB)
MAX_YAML_SIZE = 1024 * 1024

# Maximum workflow depth
MAX_WORKFLOW_DEPTH = 100

# Maximum number of steps
MAX_STEPS = 500

# Allowed top-level keys in workflow
ALLOWED_WORKFLOW_KEYS = {
    "name", "description", "version", "author", "tags",
    "steps", "nodes", "edges", "variables", "inputs", "outputs",
    "settings", "metadata", "triggers", "on_error", "timeout",
}

# Module prefix whitelist (categories that are allowed)
# "core" is the namespace prefix used by flyto-core modules (e.g., core.api.http_get)
ALLOWED_MODULE_PREFIXES = {
    # Core namespace
    "core",  # flyto-core namespace (e.g., core.api.http_get, core.browser.click)

    # Browser & UI
    "browser", "element", "form", "ui", "screenshot",

    # Flow control
    "flow",

    # Data & Files
    "data", "file", "json", "csv", "excel", "word", "pdf",

    # API & HTTP
    "api", "http", "webhook",

    # Communication
    "notification", "notify", "email", "slack", "telegram", "discord",

    # Storage & State
    "storage", "cache", "state",

    # Comparison & Logic
    "compare", "condition", "logic",

    # AI & ML
    "ai", "agent", "llm", "huggingface", "vision", "vector",

    # Image & Media
    "image", "video", "audio", "media",

    # Utilities
    "utility", "variable", "text", "string", "math", "datetime", "array", "object",

    # Analysis & Testing
    "analysis", "testing", "test",

    # System (with restrictions)
    "shell", "process", "port", "database",

    # External services
    "google", "serpapi",

    # Code (restricted)
    "code",

    # Templates
    "template", "mcp",

    # Additional flyto-core categories
    "atomic", "check", "cloud", "convert", "crypto", "document",
    "encode", "error", "format", "hash", "meta", "output", "path",
    "productivity", "random", "regex", "set", "stats", "validate", "verify",
}

# Explicitly blocked modules (even if prefix is allowed)
BLOCKED_MODULES = {
    "code.shell",  # No arbitrary shell execution
    "code.exec",   # No arbitrary code execution
    "code.eval",   # No eval
    "file.delete_recursive",  # No recursive delete
    "system.exec",
    "system.shell",
}


class YAMLSecurityError(Exception):
    """Raised when YAML security validation fails."""

    def __init__(self, message: str, error_code: str = "YAML_SECURITY_ERROR"):
        """Initialize with error message and security error code."""
        super().__init__(message)
        self.error_code = error_code


def parse_workflow_yaml(
    yaml_str: str,
    max_size: int = MAX_YAML_SIZE,
    validate_modules: bool = True,
) -> Dict[str, Any]:
    """
    Securely parse workflow YAML with validation.

    Args:
        yaml_str: Raw YAML string
        max_size: Maximum allowed size in bytes
        validate_modules: Whether to validate module IDs

    Returns:
        Parsed workflow dictionary

    Raises:
        YAMLSecurityError: If validation fails
    """
    # Check size limit
    if len(yaml_str) > max_size:
        raise YAMLSecurityError(
            f"YAML exceeds maximum size ({len(yaml_str)} > {max_size} bytes)",
            "YAML_TOO_LARGE"
        )

    # Parse with safe_load (no code execution)
    try:
        workflow = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        raise YAMLSecurityError(
            f"Invalid YAML syntax: {e}",
            "YAML_PARSE_ERROR"
        )

    if workflow is None:
        raise YAMLSecurityError("Empty workflow", "YAML_EMPTY")

    if not isinstance(workflow, dict):
        raise YAMLSecurityError(
            "Workflow must be a dictionary",
            "YAML_INVALID_TYPE"
        )

    # Validate structure
    _validate_workflow_structure(workflow)

    # Validate modules if requested
    if validate_modules:
        _validate_workflow_modules(workflow)

    return workflow


def _validate_workflow_structure(workflow: Dict[str, Any]) -> None:
    """Validate workflow structure and keys."""
    # Check for unknown top-level keys
    unknown_keys = set(workflow.keys()) - ALLOWED_WORKFLOW_KEYS
    if unknown_keys:
        logger.warning(f"Unknown workflow keys (ignored): {unknown_keys}")

    # Check step count
    steps = workflow.get("steps") or workflow.get("nodes") or []
    if len(steps) > MAX_STEPS:
        raise YAMLSecurityError(
            f"Too many steps ({len(steps)} > {MAX_STEPS})",
            "YAML_TOO_MANY_STEPS"
        )

    # Validate depth (prevent deeply nested structures)
    _check_depth(workflow, 0, MAX_WORKFLOW_DEPTH)


def _check_depth(obj: Any, current_depth: int, max_depth: int) -> None:
    """Check object nesting depth."""
    if current_depth > max_depth:
        raise YAMLSecurityError(
            f"Workflow exceeds maximum nesting depth ({max_depth})",
            "YAML_TOO_DEEP"
        )

    if isinstance(obj, dict):
        for value in obj.values():
            _check_depth(value, current_depth + 1, max_depth)
    elif isinstance(obj, list):
        for item in obj:
            _check_depth(item, current_depth + 1, max_depth)


def _validate_workflow_modules(workflow: Dict[str, Any]) -> None:
    """Validate that all modules are in the whitelist."""
    steps = workflow.get("steps") or workflow.get("nodes") or []
    invalid_modules = []

    for step in steps:
        if not isinstance(step, dict):
            continue

        module_id = step.get("action") or step.get("module") or step.get("module_id") or step.get("type")
        if not module_id:
            continue

        # Check if blocked
        if module_id in BLOCKED_MODULES:
            invalid_modules.append((module_id, "blocked"))
            continue

        # Check if prefix is allowed
        prefix = module_id.split(".")[0] if "." in module_id else module_id
        if prefix not in ALLOWED_MODULE_PREFIXES:
            invalid_modules.append((module_id, "unknown_prefix"))

    if invalid_modules:
        blocked = [m for m, reason in invalid_modules if reason == "blocked"]
        unknown = [m for m, reason in invalid_modules if reason == "unknown_prefix"]

        messages = []
        if blocked:
            messages.append(f"Blocked modules: {', '.join(blocked)}")
        if unknown:
            messages.append(f"Unknown module types: {', '.join(unknown)}")

        raise YAMLSecurityError(
            "; ".join(messages),
            "YAML_INVALID_MODULES"
        )


def is_module_allowed(module_id: str) -> bool:
    """Check if a module ID is allowed."""
    if module_id in BLOCKED_MODULES:
        return False

    prefix = module_id.split(".")[0] if "." in module_id else module_id
    return prefix in ALLOWED_MODULE_PREFIXES


def get_allowed_module_prefixes() -> Set[str]:
    """Get the set of allowed module prefixes."""
    return ALLOWED_MODULE_PREFIXES.copy()


def get_blocked_modules() -> Set[str]:
    """Get the set of explicitly blocked modules."""
    return BLOCKED_MODULES.copy()
