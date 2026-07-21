"""
Workflow Conversion Endpoints

Validation, layout, graph computation, and format conversion routes.
All graph computation happens server-side; frontend just renders.
"""

from fastapi import APIRouter

from api.workflows.models import (
    WorkflowValidateRequest,
    WorkflowLayoutRequest,
    StepsToVueFlowRequest,
    VueFlowToStepsRequest,
    SchemaPreviewRequest,
)
from api.workflows.validation import (
    validate_workflow_connections_for_api,
    validate_workflow_start_nodes,
    topological_sort_workflow,
    compute_layout_positions,
    compute_graph_relations,
    convert_steps_to_vueflow,
    convert_vueflow_to_steps,
    compute_preview_schema,
)
from api.workflows.crud import _build_workflow_dict

conversion_router = APIRouter()


@conversion_router.post("/validate")
async def validate_workflow(
    request: WorkflowValidateRequest,
):
    """
    Validate a workflow before save/execute.

    Uses core.validation.validate_workflow as single source of truth.
    Public endpoint (no authentication required for validation).
    """
    workflow_dict = _build_workflow_dict(
        request.nodes,
        request.edges,
        edge_extra_fields=("type", "data", "sourceHandle", "targetHandle"),
        has_loop=request.has_loop,
    )

    result = validate_workflow_connections_for_api(workflow_dict)
    return {"ok": result.get("valid", False), **result}


@conversion_router.post("/validate-start")
async def validate_workflow_start(
    request: WorkflowValidateRequest,
):
    """
    Quick validation of start nodes only.

    Faster than full validation, good for UI feedback.
    """
    workflow_dict = _build_workflow_dict(
        request.nodes,
        request.edges,
        edge_extra_fields=("type",),
    )

    result = validate_workflow_start_nodes(workflow_dict)
    return {"ok": result.get("valid", False), **result}


@conversion_router.post("/sort")
async def sort_workflow_steps(
    request: WorkflowValidateRequest,
):
    """
    Topological sort workflow steps.

    S-Grade: All graph computation on backend, frontend just renders.

    Returns:
        - sorted_steps: Steps in topological order
        - step_order: Array of step IDs in order
        - valid: Whether the workflow has no cycles
        - has_cycle: Whether a cycle was detected
    """
    workflow_dict = _build_workflow_dict(
        request.nodes,
        request.edges,
        node_extra_fields=("data",),
        edge_extra_fields=("type", "data"),
    )

    result = topological_sort_workflow(workflow_dict)
    return {"ok": result.get("valid", False), **result}


@conversion_router.post("/layout")
async def compute_workflow_layout(
    request: WorkflowLayoutRequest,
):
    """
    Compute auto layout positions for workflow nodes.

    S-Grade: All graph computation on backend, frontend just renders.

    Returns:
        - positions: { node_id: { x, y }, ... }
    """
    workflow_dict = _build_workflow_dict(
        request.nodes,
        request.edges,
        node_extra_fields=("data", "ui_state"),
        edge_extra_fields=("type", "sourceHandle", "targetHandle", "data"),
    )

    result = compute_layout_positions(
        workflow_dict,
        preset=request.preset or "default",
        direction=request.direction or "RIGHT",
    )

    return {"ok": True, **result}


@conversion_router.post("/graph-relations")
async def compute_workflow_relations(
    request: WorkflowValidateRequest,
):
    """
    Pre-compute graph relations for all nodes.

    S-Grade: All graph traversal on backend, frontend just looks up.

    Returns:
        - relations: { node_id: { predecessors: [...], successors: [...] }, ... }
    """
    workflow_dict = _build_workflow_dict(
        request.nodes,
        request.edges,
        node_extra_fields=("data",),
        edge_extra_fields=("type", "data"),
    )

    result = compute_graph_relations(workflow_dict)
    return {"ok": True, **result}


@conversion_router.post("/steps-to-vueflow")
async def convert_steps_to_vueflow_elements(
    request: StepsToVueFlowRequest,
):
    """
    Convert backend steps to VueFlow-compatible format.

    S-Grade: All graph topology and edge creation on backend.

    Returns:
        - nodes: VueFlow node objects
        - edges: VueFlow edge objects
    """
    steps = [
        {
            "id": s.id,
            "module": s.module or s.type,
            "label": s.label,
            "params": s.params or s.config or {},
            "position_x": s.position_x,
            "position_y": s.position_y,
            "connections": s.connections,
            "resources": s.resources,
            "description": s.description,
            "output": s.output,
            "when": s.when,
            "on_error": s.on_error,
            "retry": s.retry,
            "timeout": s.timeout,
            "parallel": s.parallel,
            "foreach": s.foreach,
            "as": s.as_,
        }
        for s in request.steps
    ]

    result = convert_steps_to_vueflow(steps)
    return {"ok": True, **result}


@conversion_router.post("/vueflow-to-steps")
async def convert_vueflow_to_steps_endpoint(
    request: VueFlowToStepsRequest,
):
    """
    Convert VueFlow elements to backend steps format.

    S-Grade: All graph analysis on backend.

    Returns:
        - steps: Backend step objects
    """
    nodes = [
        {
            "id": n.id,
            "type": n.type,
            "position": n.position,
            "label": n.label,
            "data": n.data or {},
        }
        for n in request.nodes
    ]

    edges = [
        {
            "id": e.id,
            "source": e.source,
            "target": e.target,
            "sourceHandle": e.sourceHandle,
            "targetHandle": e.targetHandle,
            "type": e.type,
            "data": e.data,
            "label": e.label,
        }
        for e in request.edges
    ]

    result = convert_vueflow_to_steps(nodes, edges)
    return {"ok": True, **result}


@conversion_router.post("/schema/preview")
async def compute_schema_preview(
    request: SchemaPreviewRequest,
):
    """
    Compute preview input schema from workflow and UI components.

    S-Grade: All schema inference on backend.

    Returns:
        - merged_schema: Combined schema from UI + inferred inputs
        - ui_fields: Fields defined in UI sections
        - inferred_fields: Auto-inferred fields from workflow refs
        - workflow_refs: Variable references found in workflow
        - workflow_steps: Workflow steps for progress display
    """
    workflow_elements = [
        {
            "id": el.id,
            "type": el.type,
            "position": el.position,
            "label": el.label,
            "data": el.data or {},
        }
        for el in request.workflow_elements
    ]

    ui_sections = [
        {
            "id": s.id,
            "columns_data": s.columns_data or [],
        }
        for s in request.ui_sections
    ]

    result = compute_preview_schema(workflow_elements, ui_sections)
    return {"ok": True, **result}
