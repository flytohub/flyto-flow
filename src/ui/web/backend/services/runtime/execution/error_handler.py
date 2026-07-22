"""
Error Handler — Trigger error workflows on execution failure.

Extracted from ExecutionManager to keep service.py focused on orchestration.
"""

import logging
import re
from typing import Any, Dict, Optional

from services.runtime.execution.utils import utc_now
from services.runtime.execution.template_loader import fetch_workflow_yaml

logger = logging.getLogger(__name__)

# Metadata key to mark executions as error workflows (prevents infinite loops)
ERROR_WORKFLOW_MARKER = '__is_error_workflow__'


async def trigger_error_workflow(
    manager: Any,
    info: Any,
    error_message: str,
    traceback_str: str,
    workflow_data: Optional[Dict[str, Any]],
) -> None:
    """
    Trigger error workflow when execution fails.

    Looks up the error_workflow_id from the workflow metadata and triggers
    it with error context. Prevents infinite loops by marking error workflow
    executions.

    Args:
        manager: ExecutionManager instance (used to call start())
        info: Failed execution info
        error_message: Error message
        traceback_str: Full traceback
        workflow_data: Parsed workflow data
    """
    try:
        # Get error workflow ID from workflow metadata
        error_workflow_id = await get_error_workflow_id(
            info.workflow_id, info.workspace_id
        )

        if not error_workflow_id:
            logger.debug(f"No error workflow configured for {info.workflow_id}")
            return

        # Prevent infinite loops: don't trigger error workflow for error workflows
        if info.metadata.get(ERROR_WORKFLOW_MARKER):
            logger.warning(
                f"Skipping error workflow trigger: {info.execution_id} is already an error workflow"
            )
            return

        # Build error context
        failed_step_id = info.error_step_id or info.active_node_id or 'unknown'
        error_context = {
            'source_workflow_id': info.workflow_id,
            'source_workflow_name': info.workflow_name,
            'source_execution_id': info.execution_id,
            'failed_step_id': failed_step_id,
            'failed_step_module': get_failed_step_module(
                workflow_data, failed_step_id
            ),
            'error_message': error_message,
            'error_code': extract_error_code(error_message),
            'error_traceback': traceback_str,
            'failed_at': utc_now(),
            'workspace_id': info.workspace_id or '',
            'input_params': info.input_params,
            'node_states': dict(info.node_states) if info.node_states else {},
        }

        # Fetch error workflow YAML
        error_workflow_yaml = await fetch_workflow_yaml(
            error_workflow_id, info.workspace_id
        )

        if not error_workflow_yaml:
            logger.warning(f"Error workflow {error_workflow_id} not found")
            return

        # Start error workflow with error context
        error_exec_id = await manager.start(
            workflow_yaml=error_workflow_yaml,
            variables={'error_context': error_context},
            workflow_id=error_workflow_id,
            workspace_id=info.workspace_id,
            workflow_name=f"Error Handler for {info.workflow_name}",
        )

        # Mark as error workflow to prevent loops
        error_info = manager._executions.get(error_exec_id)
        if error_info:
            error_info.metadata[ERROR_WORKFLOW_MARKER] = True
            error_info.metadata['source_execution_id'] = info.execution_id

        logger.info(
            f"Triggered error workflow {error_workflow_id} "
            f"(execution: {error_exec_id}) for failed execution {info.execution_id}"
        )

    except Exception as e:
        # Don't let error workflow failures propagate
        logger.error(f"Failed to trigger error workflow: {e}")


async def get_error_workflow_id(
    workflow_id: str,
    workspace_id: Optional[str],
) -> Optional[str]:
    """
    Get error workflow ID from workflow metadata.

    Looks up the workflow in the data provider and returns the
    configured error_workflow_id if set.
    """
    if not workspace_id:
        return None

    try:
        from gateway.providers.hub import get_data_provider

        workflow = await get_data_provider().workflows.get_workflow(
            workspace_id=workspace_id,
            workflow_id=workflow_id,
            include_graph=False,
        )
        wf_data = workflow.model_dump() if hasattr(workflow, "model_dump") else workflow
        if wf_data:
            return wf_data.get('error_workflow_id')

        return None
    except Exception as e:
        logger.warning(f"Failed to get error workflow ID: {e}")
        return None


def get_failed_step_module(
    workflow_data: Optional[Dict[str, Any]],
    step_id: Optional[str],
) -> str:
    """Get module ID of failed step."""
    if not workflow_data or not step_id:
        return 'unknown'

    steps = workflow_data.get('steps', [])
    for step in steps:
        if step.get('id') == step_id:
            return step.get('module', 'unknown')

    return 'unknown'


def extract_error_code(error_message: str) -> str:
    """Extract error code from error message if present."""
    # Common patterns: [CODE], ERROR_CODE:, Code:
    patterns = [
        r'\[([A-Z_]+)\]',  # [ERROR_CODE]
        r'([A-Z_]+):',     # ERROR_CODE:
        r'Code:\s*(\w+)',  # Code: XYZ
    ]

    for pattern in patterns:
        match = re.search(pattern, error_message)
        if match:
            return match.group(1)

    return 'EXECUTION_ERROR'
