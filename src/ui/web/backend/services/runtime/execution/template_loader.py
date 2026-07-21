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
    user_id: Optional[str],
    embedded_templates: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Pre-load template definitions for template.invoke steps.

    Resolution order:
    1. embedded_templates (bundled into snapshot at publish time)
    2. Live fetch from cloud API

    Args:
        steps: Workflow steps to scan
        user_id: Current user ID
        embedded_templates: Pre-bundled definitions from snapshot (publisher's own templates)

    Returns:
        Dict mapping library_id to template definition

    Raises:
        TemplateDependencyError: If any referenced template is unavailable
    """
    logger.debug(f"load_template_definitions called with user_id={user_id}")
    if not user_id:
        logger.debug("No user_id, returning empty")
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

        # 2. Fetch from cloud API
        try:
            definition = await fetch_template_definition(library_id, user_id)
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
            f"Please install or purchase the missing templates."
        )


async def fetch_template_definition(
    library_id: str,
    user_id: str,
) -> Optional[Dict[str, Any]]:
    """Fetch template definition from provider."""
    try:
        from services.cloud_client import cloud_get

        # Try fetching template directly (cloud handles purchases/forks/owned)
        data = await cloud_get(f"templates/{library_id}")
        if data:
            template = data if isinstance(data, dict) else {}
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
    user_id: Optional[str],
) -> Optional[str]:
    """
    Fetch workflow YAML by ID.

    Retrieves the workflow definition and converts it to YAML format.
    """
    if not user_id:
        return None

    try:
        from services.cloud_client import cloud_get

        wf_data = await cloud_get(
            f"workflows/{workflow_id}",
            params={"include_graph": "true"},
        )
        workflow = wf_data

        if not workflow:
            return None

        # Convert workflow to YAML format
        workflow_dict = workflow.model_dump() if hasattr(workflow, 'model_dump') else workflow

        # Build steps from nodes
        from services.template.workflow_converter import WorkflowConverter
        steps_data = WorkflowConverter.vueflow_to_steps(
            nodes=workflow_dict.get('nodes', []),
            edges=workflow_dict.get('edges', []),
        )

        workflow_yaml_data = {
            'name': workflow_dict.get('name', 'Error Workflow'),
            'version': '1.0.0',
            'steps': steps_data.get('steps', []),
            'edges': steps_data.get('edges', []),
        }

        return yaml.dump(workflow_yaml_data, allow_unicode=True)

    except Exception as e:
        logger.warning(f"Failed to fetch workflow YAML: {e}")
        return None
