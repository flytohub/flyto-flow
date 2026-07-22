"""
Module ID Specification

Unified module ID format and utilities for parsing/generating module IDs.

Format: [source:]category.action[:resourceId]

| Source | Format | Example |
|--------|--------|---------|
| Atomic | category.action | browser.goto |
| Composite | category.action | browser.scrape_to_json |
| Plugin | category.action | database.query |
| Template | template.invoke:uuid | template.invoke:abc123 |
"""

import re
from typing import Optional, NamedTuple
from dataclasses import dataclass


@dataclass
class ModuleIdParts:
    """Parsed module ID components."""
    category: str
    action: str
    source: Optional[str] = None  # Explicit source prefix if present
    resource_id: Optional[str] = None  # Resource identifier (template_id, model_id)

    @property
    def base_id(self) -> str:
        """Get base module ID without resource ID."""
        return f"{self.category}.{self.action}"

    @property
    def full_id(self) -> str:
        """Get full module ID including resource ID."""
        base = self.base_id
        if self.resource_id:
            return f"{base}:{self.resource_id}"
        return base

    def __str__(self) -> str:
        """Return the full module ID string."""
        return self.full_id


def parse_module_id(module_id: str) -> ModuleIdParts:
    """
    Parse a module ID into its components.

    Examples:
        "browser.goto" → ModuleIdParts(category="browser", action="goto")
        "template.invoke:abc123" → ModuleIdParts(category="template", action="invoke", resource_id="abc123")
        "api.openai.chat" → ModuleIdParts(category="api", action="openai.chat")

    Args:
        module_id: The module identifier string

    Returns:
        ModuleIdParts with parsed components

    Raises:
        ValueError: If module_id is empty or invalid
    """
    if not module_id:
        raise ValueError("Module ID cannot be empty")

    # Split resource ID if present
    if ":" in module_id:
        base_part, resource_id = module_id.split(":", 1)
    else:
        base_part = module_id
        resource_id = None

    # Split category and action
    parts = base_part.split(".", 1)

    if len(parts) < 2:
        # Single part - use as both category and action
        return ModuleIdParts(
            category=parts[0],
            action=parts[0],
            resource_id=resource_id
        )

    category = parts[0]
    action = parts[1]

    return ModuleIdParts(
        category=category,
        action=action,
        resource_id=resource_id
    )


def generate_module_id(
    category: str,
    action: str,
    resource_id: Optional[str] = None,
) -> str:
    """
    Generate a module ID from components.

    Examples:
        generate_module_id("browser", "goto") → "browser.goto"
        generate_module_id("template", "invoke", "abc123") → "template.invoke:abc123"

    Args:
        category: Module category (e.g., "browser", "template")
        action: Module action (e.g., "goto", "invoke")
        resource_id: Optional resource identifier

    Returns:
        Complete module ID string
    """
    base = f"{category}.{action}"
    if resource_id:
        return f"{base}:{resource_id}"
    return base


def is_template_module(module_id: str) -> bool:
    """
    Check if a module ID represents a template module.

    Args:
        module_id: The module identifier

    Returns:
        True if this is a template module
    """
    if not module_id:
        return False

    return (
        module_id.startswith("template.invoke") or
        module_id.startswith("template.")
    )


def extract_template_id(module_id: str) -> Optional[str]:
    """
    Extract template ID from a template module ID.

    Examples:
        "template.invoke:abc123" → "abc123"
        "template.abc123" → "abc123"
        "browser.goto" → None

    Args:
        module_id: The module identifier

    Returns:
        Template ID or None if not a template module
    """
    if not module_id:
        return None

    # Format: template.invoke:uuid
    if module_id.startswith("template.invoke:"):
        return module_id.replace("template.invoke:", "")

    # Legacy format: template.xxx
    if module_id.startswith("template.") and module_id != "template.invoke":
        return module_id.replace("template.", "")

    return None


def normalize_template_module_id(module_id: str, template_id: Optional[str] = None) -> str:
    """
    Normalize template module ID to standard format.

    Standard format: template.invoke:uuid

    Examples:
        normalize_template_module_id("template.abc123") → "template.invoke:abc123"
        normalize_template_module_id("template.invoke:abc123") → "template.invoke:abc123"
        normalize_template_module_id("template.invoke", "abc123") → "template.invoke:abc123"

    Args:
        module_id: The module identifier
        template_id: Optional template ID to use if not in module_id

    Returns:
        Normalized template module ID
    """
    # Already in correct format
    if module_id.startswith("template.invoke:"):
        return module_id

    # Extract template ID from module_id or use provided
    tid = extract_template_id(module_id) or template_id

    if tid:
        return f"template.invoke:{tid}"

    return "template.invoke"


def is_plugin_module(module_id: str, source: Optional[str] = None) -> bool:
    """
    Check if a module ID represents a plugin module.

    Plugin modules don't have a special prefix, so we need source info.

    Args:
        module_id: The module identifier
        source: Optional source type hint

    Returns:
        True if this is a plugin module
    """
    return source == "plugin"


def get_module_display_name(module_id: str) -> str:
    """
    Generate a human-readable display name from module ID.

    Examples:
        "string.uppercase" → "Uppercase"
        "browser.goto" → "Goto"
        "template.invoke:abc123" → "Template: Invoke"

    Args:
        module_id: The module identifier

    Returns:
        Human-readable display name
    """
    parts = parse_module_id(module_id)

    # Format action as title case
    action = parts.action.replace("_", " ").replace("-", " ").title()

    if parts.category == "template":
        return f"Template: {action}"

    return action


def validate_module_id(module_id: str) -> tuple[bool, Optional[str]]:
    """
    Validate a module ID format.

    Args:
        module_id: The module identifier to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not module_id:
        return False, "Module ID cannot be empty"

    if not isinstance(module_id, str):
        return False, "Module ID must be a string"

    # Check for valid characters
    # Allow resource IDs after a colon; slashes support namespaced local plugins.
    pattern = r'^[a-zA-Z0-9._\-:/]+$'
    if not re.match(pattern, module_id):
        return False, f"Module ID contains invalid characters: {module_id}"

    # Must have at least category.action format
    if "." not in module_id and ":" not in module_id:
        return False, f"Module ID must have category.action format: {module_id}"

    return True, None
