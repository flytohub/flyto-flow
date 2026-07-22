"""
Workflow Execution Endpoints

Execute workflows and manage execution history.
"""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException

from common.error_messages import ErrorMessages
from api.workflows.models import WorkflowRunRequest
from gateway.local_context import get_local_actor, get_local_principal
from gateway.providers.hub import get_data_provider

logger = logging.getLogger(__name__)

run_router = APIRouter()
router = run_router



def _build_edges_by_source(raw_edges) -> Dict[str, list]:
    """Build edges-by-source map from edge models/dicts to uniform dict format."""
    edges_by_source = {}
    for edge in raw_edges:
        if isinstance(edge, dict):
            source_id = edge.get("source_node_id", "")
            target_id = edge.get("target_node_id", "")
            source_handle = edge.get("source_handle") or edge.get("sourceHandle") or ""
            target_handle = edge.get("target_handle") or edge.get("targetHandle") or ""
            edge_data = edge.get("data")
        else:
            source_id = edge.source_node_id
            target_id = edge.target_node_id
            source_handle = getattr(edge, "source_handle", None) or ""
            target_handle = getattr(edge, "target_handle", None) or ""
            edge_data = getattr(edge, "data", None)
        if not source_id or not target_id:
            continue
        edges_by_source.setdefault(source_id, []).append({
            "source": source_id,
            "target": target_id,
            "sourceHandle": source_handle,
            "targetHandle": target_handle,
            "data": edge_data,
        })
    return edges_by_source


def _nodes_to_steps(nodes, edges_by_source: Dict[str, list]) -> list:
    """Convert workflow nodes to engine steps with connection resolution."""
    from api.workflows.utils import normalize_template_module
    from services.template.workflow_converter import WorkflowConverter

    sorted_nodes = sorted(
        nodes,
        key=lambda n: n.get("order_index", 0) if isinstance(n, dict) else n.order_index,
    )
    steps = []
    for node in sorted_nodes:
        if isinstance(node, dict):
            node_module_id = node.get("module_id", "")
            node_params_raw = node.get("params", {})
            node_id = node.get("id", "")
            node_label = node.get("label", "")
            node_connections = node.get("connections")
        else:
            node_module_id = node.module_id
            node_params_raw = node.params
            node_id = node.id
            node_label = node.label
            node_dict = node.dict() if hasattr(node, 'dict') else node.__dict__
            node_connections = node_dict.get("connections")

        module_id, node_params = normalize_template_module(node_module_id, node_params_raw)
        step = {"id": node_id, "module": module_id, "label": node_label, **node_params}

        connections_from_edges = WorkflowConverter._extract_connections_from_edges(
            node_id, module_id, node_params, edges_by_source
        )
        if connections_from_edges:
            step["connections"] = connections_from_edges
        elif node_connections:
            step["connections"] = node_connections
        steps.append(step)
    return steps


def _extract_step_ids(workflow: Dict[str, Any]) -> set[str]:
    """Return explicit step IDs from a parsed workflow definition."""
    step_ids: set[str] = set()
    for step in workflow.get("steps") or []:
        if isinstance(step, dict):
            step_id = step.get("id")
            if isinstance(step_id, str) and step_id:
                step_ids.add(step_id)
    return step_ids


def _validate_run_preflight(request: WorkflowRunRequest, workflow: Dict[str, Any]) -> None:
    """Validate run controls that depend on parsed workflow structure."""
    steps = workflow.get("steps") or []
    step_count = len(steps)

    start_step = getattr(request, "start_step", None)
    end_step = getattr(request, "end_step", None)

    if start_step is not None and start_step >= step_count:
        raise HTTPException(status_code=400, detail="startStep must reference an existing workflow step")
    if end_step is not None and end_step >= step_count:
        raise HTTPException(status_code=400, detail="endStep must reference an existing workflow step")

    breakpoints = getattr(request, "breakpoints", None) or []
    if breakpoints:
        step_ids = _extract_step_ids(workflow)
        unknown_breakpoints = [breakpoint for breakpoint in breakpoints if breakpoint not in step_ids]
        if unknown_breakpoints:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown breakpoint node IDs: {', '.join(unknown_breakpoints)}",
            )


@run_router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    execution_params: Optional[Dict[str, Any]] = None,
    workspace_context=Depends(get_local_principal),
):
    """
    Execute workflow by ID.
    Returns execution_id for tracking and cancellation.

    This is a LOCAL endpoint (run_router) because it requires flyto-core ExecutionManager.
    Workflow data is fetched from the local CE data provider.
    """
    import yaml
    from services.runtime.execution_manager import get_execution_manager

    provider = get_data_provider()

    workflow = await _fetch_workflow(
        provider=provider, workspace_id=workspace_context.id, workflow_id=workflow_id,
    )
    if not workflow:
        raise HTTPException(status_code=404, detail=ErrorMessages.WORKFLOW_NOT_FOUND)

    is_active = workflow.get("is_active", True) if isinstance(workflow, dict) else workflow.is_active
    if not is_active:
        raise HTTPException(status_code=400, detail="Workflow not enabled")

    # Convert nodes + edges to engine steps
    nodes = workflow.get("nodes", []) if isinstance(workflow, dict) else (workflow.nodes or [])
    raw_edges = workflow.get("edges", []) if isinstance(workflow, dict) else (workflow.edges or [])
    steps = _nodes_to_steps(nodes, _build_edges_by_source(raw_edges)) if nodes else []

    if not steps:
        raise HTTPException(status_code=400, detail="Workflow has no steps to execute")

    wf_name = workflow.get("name", "") if isinstance(workflow, dict) else workflow.name
    wf_desc = workflow.get("description", "") if isinstance(workflow, dict) else (workflow.description or "")
    # Build edges list for engine (resource edges needed for AI sub-nodes)
    edges_for_engine = []
    for source_id, edge_list in _build_edges_by_source(raw_edges).items():
        edges_for_engine.extend(edge_list)

    workflow_yaml = yaml.dump(
        {"name": wf_name, "description": wf_desc, "steps": steps, "edges": edges_for_engine},
        allow_unicode=True,
    )

    try:
        exec_manager = get_execution_manager()
        execution_id = await exec_manager.start(
            workflow_yaml=workflow_yaml,
            variables=execution_params or {},
            workflow_id=workflow_id,
            workspace_id=workspace_context.id,
        )
        return {
            "ok": True,
            "execution_id": execution_id,
            "status": "running",
            "message": "Workflow execution started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start execution: {e}")


async def _fetch_workflow(provider, workspace_id: str, workflow_id: str):
    """Fetch workflow data only from CE's local provider."""
    return await provider.workflows.get_workflow(
        workspace_id=workspace_id,
        workflow_id=workflow_id,
        include_graph=True,
    )


@run_router.post("/run")
async def run_workflow_direct(
    request: WorkflowRunRequest,
    workspace_context: dict = Depends(get_local_actor),
):
    """
    Run workflow directly using Core engine.
    Accepts workflow as YAML string and executes immediately.
    Returns execution_id for tracking.

    CE always associates execution state with its fixed local workspace actor.
    """
    import yaml
    from services.runtime.execution_manager import get_execution_manager

    workspace_id = workspace_context["id"]
    logger.debug("Direct local workflow request workspace=%s", workspace_id)

    try:
        workflow = yaml.safe_load(request.workflow_yaml)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")

    if not workflow:
        raise HTTPException(status_code=400, detail="Empty workflow")
    if not workflow.get("steps"):
        raise HTTPException(status_code=400, detail="Workflow must have steps")
    _validate_run_preflight(request, workflow)

    # Note: Skipping pre-execution validation for /run endpoint.
    # The execution engine validates at runtime with better context.
    # Pre-validation produces false positives for loop workflows
    # (INVALID_START_NODE, PORT_NOT_FOUND, MODULE_NOT_FOUND for type-based nodes).

    try:
        exec_manager = get_execution_manager()
        execution_id = await exec_manager.start(
            workflow_yaml=request.workflow_yaml,
            variables=request.params or {},
            workflow_id="local",
            start_step=request.start_step,
            end_step=request.end_step,
            breakpoints=request.breakpoints,
            screenshot_mode=request.screenshot_mode,
            workspace_id=workspace_id,
        )

        return {
            "ok": True,
            "execution_id": execution_id,
            "message": "Workflow execution started"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as exc:
        logger.exception("Direct workflow execution failed")
        raise HTTPException(status_code=500, detail="Workflow execution failed") from exc
