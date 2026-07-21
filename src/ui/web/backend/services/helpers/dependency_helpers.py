"""
Template Dependency Helpers

Resolves nested template.invoke references in steps to determine:
- Which sub-templates are owned by the publisher → embed
- Which are others' published templates → declare as dependency
- Which are inaccessible → block publish
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def extract_template_refs(steps: List[Dict[str, Any]]) -> List[str]:
    """Extract all template IDs referenced by template.invoke steps.

    Handles all module ID formats:
    - template.invoke  (template_id in params)
    - template.invoke:{id}
    - template.{id}
    """
    refs = []
    for step in steps:
        module_id = step.get("module", "")
        params = step.get("params", {})

        if not (module_id == "template.invoke" or module_id.startswith("template.")):
            continue

        # Resolve template_id from params or module_id suffix
        tid = params.get("template_id") or params.get("library_id")
        if not tid and module_id.startswith("template.invoke:"):
            tid = module_id.replace("template.invoke:", "")
        elif not tid and module_id.startswith("template.") and module_id != "template.invoke":
            tid = module_id.replace("template.", "")

        if tid and tid not in refs:
            refs.append(tid)

    return refs


async def resolve_template_dependencies(
    steps: List[Dict[str, Any]],
    publisher_id: str,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Resolve all nested template references for publishing.

    For each template.invoke step, determines:
    - Own template → marked for embedding (embedded=True)
    - Others' published template → dependency reference
    - Inaccessible → added to errors list

    Args:
        steps: Template steps to scan
        publisher_id: User ID of the person publishing

    Returns:
        (dependencies, errors) where:
        - dependencies: list of dependency dicts
        - errors: list of human-readable error strings (non-empty = block publish)
    """
    template_ids = extract_template_refs(steps)
    if not template_ids:
        return [], []

    template_provider = _get_template_provider()
    dependencies = []
    errors = []

    for tid in template_ids:
        try:
            template = (
                await template_provider.get_template_internal(tid)
                if template_provider
                else None
            )
            if not template:
                errors.append(
                    f"Referenced template '{tid}' does not exist. "
                    f"Remove or replace the template.invoke step before publishing."
                )
                continue

            creator_id = _template_value(template, "creator_id") or _template_value(
                template, "author_id"
            )
            status = _template_value(template, "status", "draft")
            visibility = _template_value(template, "visibility", "private")
            name = _template_value(template, "name", "Untitled")
            pricing = _template_value(template, "pricing", "free")

            is_own = creator_id == publisher_id

            if is_own:
                # Own template → embed into snapshot (regardless of status)
                dependencies.append({
                    "template_id": tid,
                    "name": name,
                    "creator_id": creator_id,
                    "pricing": "free",
                    "required": True,
                    "embedded": True,
                })
            elif status == "published" and visibility == "public":
                # Others' published public template → dependency reference
                dependencies.append({
                    "template_id": tid,
                    "name": name,
                    "creator_id": creator_id,
                    "pricing": pricing,
                    "required": True,
                    "embedded": False,
                })
            else:
                # Others' private/draft template → block
                if status != "published":
                    errors.append(
                        f"Referenced template '{name}' ({tid}) is not published. "
                        f"It must be published before you can publish a template that uses it."
                    )
                elif visibility != "public":
                    errors.append(
                        f"Referenced template '{name}' ({tid}) is private. "
                        f"It must be public before you can publish a template that uses it."
                    )

        except Exception as e:
            logger.warning(f"Failed to resolve dependency {tid}: {e}")
            errors.append(f"Failed to check referenced template '{tid}': {e}")

    return dependencies, errors


async def build_embedded_definitions(
    dependencies: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """Fetch full definitions for dependencies marked embedded=True.

    Returns:
        Dict mapping template_id → embedded definition (steps, params_schema, etc.)
    """
    template_provider = _get_template_provider()
    embedded = {}

    for dep in dependencies:
        if not dep.get("embedded"):
            continue

        tid = dep["template_id"]
        try:
            template = (
                await template_provider.get_template_internal(tid)
                if template_provider
                else None
            )
            if not template:
                continue

            # Use marketplace_snapshot if available (published state), else live
            snap = _template_value(template, "marketplace_snapshot") or template

            embedded[tid] = {
                "steps": _template_value(snap, "steps", []),
                "name": _template_value(snap, "name", _template_value(template, "name")),
                "params_schema": _template_value(
                    snap,
                    "params_schema",
                ) or _template_value(template, "params_schema"),
                "output_schema": _template_value(
                    snap,
                    "output_schema",
                ) or _template_value(template, "output_schema"),
                "input_schema": _template_value(template, "input_schema"),
                "ui": _template_value(snap, "ui") or _template_value(template, "ui"),
                "version": _template_value(
                    snap,
                    "version",
                    _template_value(template, "version", "1.0.0"),
                ),
            }
        except Exception as e:
            logger.warning(f"Failed to build embedded definition for {tid}: {e}")

    return embedded


def _get_template_provider():
    from gateway.providers.hub import get_data_provider

    data_provider = get_data_provider()
    if data_provider is None:
        return None
    return data_provider.templates


def _template_value(template, key: str, default=None):
    if isinstance(template, dict):
        return template.get(key, default)
    return getattr(template, key, default)


def check_missing_dependencies(
    dependencies: List[Dict[str, Any]],
    user_library_ids: List[str],
) -> List[Dict[str, Any]]:
    """Check which non-embedded dependencies the user is missing.

    Args:
        dependencies: Template dependency list
        user_library_ids: Template IDs the user has in their library

    Returns:
        List of missing dependency dicts with install instructions
    """
    missing = []
    for dep in dependencies:
        if dep.get("embedded"):
            continue
        if dep["template_id"] not in user_library_ids:
            missing.append({
                "template_id": dep["template_id"],
                "name": dep["name"],
                "pricing": dep["pricing"],
                "action": "purchase" if dep["pricing"] != "free" else "install",
            })
    return missing
