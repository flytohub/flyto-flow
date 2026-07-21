"""
Library ID resolution helpers.

Centralizes the logic for resolving library_id from templates,
which varies based on whether the template is purchased, forked, or owned.
"""
from typing import Dict, Tuple, Optional, Literal

SourceType = Literal["purchase", "fork", "own"]


def resolve_library_id(template: Dict) -> Tuple[Optional[str], SourceType]:
    """
    Resolve the library ID from a template.

    The library_id determines the unique identifier used in moduleId generation.
    Priority order:
    1. purchase_context.purchase_id - for purchased templates from marketplace
    2. fork_context.fork_id - for forked templates
    3. template_id or id - for user's own templates

    Args:
        template: Template dict that may contain purchase_context, fork_context,
                  template_id, or id fields.

    Returns:
        Tuple of (library_id, source_type) where:
        - library_id: The resolved ID, or None if template is invalid
        - source_type: One of "purchase", "fork", or "own"

    Examples:
        >>> resolve_library_id({"purchase_context": {"purchase_id": "p1"}})
        ("p1", "purchase")

        >>> resolve_library_id({"fork_context": {"fork_id": "f1"}})
        ("f1", "fork")

        >>> resolve_library_id({"id": "t1"})
        ("t1", "own")

        >>> resolve_library_id({})
        (None, "own")
    """
    if not template or not isinstance(template, dict):
        return None, "own"

    # Check for purchase context first (purchased templates from marketplace)
    purchase_context = template.get("purchase_context")
    if purchase_context and isinstance(purchase_context, dict):
        purchase_id = purchase_context.get("purchase_id")
        if purchase_id:
            return purchase_id, "purchase"

    # Check for fork context (forked templates)
    fork_context = template.get("fork_context")
    if fork_context and isinstance(fork_context, dict):
        fork_id = fork_context.get("fork_id")
        if fork_id:
            return fork_id, "fork"

    # Fall back to template_id or id (user's own templates)
    library_id = template.get("template_id") or template.get("id")
    return library_id, "own"


def get_library_id(template: Dict) -> Optional[str]:
    """
    Convenience function to get just the library ID without the source type.

    Args:
        template: Template dict

    Returns:
        The resolved library_id, or None if template is invalid
    """
    library_id, _ = resolve_library_id(template)
    return library_id
