"""
Template Loader — Pre-load template definitions for template.invoke steps.

Extracted from ExecutionManager to keep service.py focused on orchestration.
"""

import logging
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


async def load_template_definitions(
    steps: List[Dict[str, Any]],
    workspace_id: Optional[str],
    embedded_templates: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Pre-load template definitions for template.invoke steps.

    Resolution order:
    1. embedded_templates (bundled into snapshot at publish time)
    2. Local CE template storage

    Args:
        steps: Workflow steps to scan
        workspace_id: Current workspace ID
        embedded_templates: Pre-bundled definitions from snapshot (publisher's own templates)

    Returns:
        Dict mapping library_id to template definition

    Raises:
        TemplateDependencyError: If any referenced template is unavailable
    """
    logger.debug(f"load_template_definitions called with workspace_id={workspace_id}")
    if not workspace_id:
        logger.debug("No workspace_id, returning empty")
        return {}

    embedded = embedded_templates or {}
    template_definitions = {}
    missing = []

    for step in steps:
        module_id = step.get("module", "")
        params = step.get("params", {})

        # Check if this is a template.invoke step
        if not (module_id == "template.invoke" or module_id.startswith("template.")):
            continue

        library_id = params.get("library_id") or params.get("template_id")

        # Extract from old format if needed
        if not library_id and module_id.startswith("template.invoke:"):
            library_id = module_id.replace("template.invoke:", "")
        elif not library_id and module_id.startswith("template.") and module_id != "template.invoke":
            library_id = module_id.replace("template.", "")

        if not library_id or library_id in template_definitions:
            continue

        # 1. Check embedded definitions first (publisher's own templates)
        if library_id in embedded:
            emb = embedded[library_id]
            template_definitions[library_id] = {
                "steps": emb.get("steps", []),
                "templateId": library_id,
            }
            logger.debug(f"Using embedded definition for {library_id}")
            continue

        # 2. Fetch from local CE storage.
        try:
            definition = await fetch_template_definition(library_id, workspace_id)
            if definition:
                template_definitions[library_id] = definition
                logger.debug(f"Loaded template definition for {library_id}: "
                           f"{len(definition.get('steps', []))} steps")
            else:
                missing.append(library_id)
                logger.warning(f"Template dependency unavailable: {library_id}")
        except Exception as e:
            missing.append(library_id)
            logger.error(f"Failed to load template {library_id}: {e}")

    if missing:
        raise TemplateDependencyError(missing)

    return template_definitions


class TemplateDependencyError(Exception):
    """Raised when required template dependencies cannot be resolved."""

    def __init__(self, missing_ids: List[str]):
        self.missing_ids = missing_ids
        names = ", ".join(missing_ids)
        super().__init__(
            f"Cannot execute: {len(missing_ids)} required sub-template(s) unavailable: {names}. "
            f"Import the missing templates into this CE workspace."
        )


async def fetch_template_definition(
    library_id: str,
    workspace_id: str,
) -> Optional[Dict[str, Any]]:
    """Fetch template definition from provider."""
    try:
        from gateway.providers.hub import get_data_provider

        data = await get_data_provider().templates.get_template(
            library_id,
            workspace_id=workspace_id,
        )
        if data:
            template = data.model_dump() if hasattr(data, "model_dump") else data
            return {
                "steps": template.get("steps", []),
                "templateId": template.get("id") or library_id,
            }

        return None
    except Exception as e:
        logger.error(f"Error fetching template definition: {e}")
        return None


async def fetch_workflow_yaml(
    workflow_id: str,
    workspace_id: Optional[str],
) -> Optional[str]:
    """
    Fetch workflow YAML by ID.

    Retrieves the workflow definition and converts it to YAML format.
    """
    if not workspace_id:
        return None

    try:
        from gateway.providers.hub import get_data_provider

        template = await get_data_provider().templates.get_template(
            workflow_id, workspace_id=workspace_id,
        )

        if not template:
            return None

        workflow_yaml_data = {
            'name': template.name or 'Error Workflow',
            'version': '1.0.0',
            'steps': template.steps or [],
        }

        return yaml.dump(workflow_yaml_data, allow_unicode=True)

    except Exception as e:
        logger.warning(f"Failed to fetch workflow YAML: {e}")
        return None
