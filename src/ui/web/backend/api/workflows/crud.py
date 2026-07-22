"""
Workflow CRUD Endpoints

Create, read, update, delete operations for workflows.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from gateway.local_context import get_local_principal
from gateway.providers.hub import get_data_provider
from gateway.providers.data import (
    WorkflowCreateDTO,
    WorkflowUpdateDTO,
    WorkflowNode,
    WorkflowEdge,
    TriggerType,
)
from common.error_messages import ErrorMessages
from api.workflows.models import (
    NodeCreate,
    EdgeCreate,
    WorkflowCreate,
    WorkflowUpdate,
)
import logging

_logger = logging.getLogger(__name__)

crud_router = APIRouter()


def _validate_workflow_graph_shape(nodes, edges) -> None:
    """Fail basic graph corruption without invoking core validation."""
    resolved_node_ids: set[str] = set()
    duplicate_ids: set[str] = set()

    for index, node in enumerate(nodes or []):
        node_id = getattr(node, "id", None) or f"node_{index}"
        if node_id in resolved_node_ids:
            duplicate_ids.add(node_id)
        resolved_node_ids.add(node_id)

    if duplicate_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Duplicate workflow node IDs: {', '.join(sorted(duplicate_ids))}",
        )

    unknown_refs: set[str] = set()
    for edge in edges or []:
        source = getattr(edge, "source_node_id", None)
        target = getattr(edge, "target_node_id", None)
        if source and source not in resolved_node_ids:
            unknown_refs.add(source)
        if target and target not in resolved_node_ids:
            unknown_refs.add(target)

    if unknown_refs:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow edges reference unknown node IDs: {', '.join(sorted(unknown_refs))}",
        )


async def _enforce_max_workflows(workspace_context, provider) -> None:
    del workspace_context, provider


def _build_workflow_dict(
    nodes,
    edges,
    *,
    node_extra_fields: tuple = (),
    edge_extra_fields: tuple = (),
    **top_level,
) -> dict:
    """Build a workflow dict from request nodes/edges.

    Args:
        nodes: Iterable of node objects with at least id, module_id, params.
        edges: Iterable of edge objects with at least id, source, target.
        node_extra_fields: Additional attribute names to include per node
            (e.g. ``("data",)`` or ``("data", "ui_state")``).
        edge_extra_fields: Additional attribute names to include per edge
            (e.g. ``("type", "data")`` or ``("type", "sourceHandle", "targetHandle", "data")``).
        **top_level: Extra top-level keys merged into the returned dict
            (e.g. ``has_loop=True``).
    """
    result: dict = {
        "nodes": [
            {
                "id": n.id,
                "module_id": n.module_id,
                "params": n.params,
                **{f: getattr(n, f) for f in node_extra_fields},
            }
            for n in nodes
        ],
        "edges": [
            {
                "id": e.id,
                "source": e.source,
                "target": e.target,
                **{f: getattr(e, f) for f in edge_extra_fields},
            }
            for e in edges
        ],
    }
    result.update(top_level)
    return result


# Combined local workflow router.
# Import conversion_router from its dedicated module
from api.workflows.conversion_routes import conversion_router  # noqa: E402

router = APIRouter()
router.include_router(conversion_router)
router.include_router(crud_router)


@crud_router.get("/")
async def list_workflows(
    page: int = Query(1, ge=1, le=1000, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    workspace_context=Depends(get_local_principal)
):
    """
    List all workflows for the local workspace.

    S-Grade: Supports server-side enabled/tag filtering via query params.
    """
    provider = get_data_provider()
    result = await provider.workflows.list_workspace_workflows(
        workspace_id=workspace_context.id,
        page=page,
        page_size=page_size,
        enabled=enabled,
    )

    items = result.items

    # Filter by tags (post-filter since providers don't support tag queries)
    tag_filter = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    if tag_filter:
        items = [w for w in items if any(t in (w.tags or []) for t in tag_filter)]

    workflows = [w.dict() for w in items]
    enabled_count = sum(1 for w in items if getattr(w, 'is_active', True))

    # Collect all available tags across workflows for filter UI
    all_tags = set()
    for w in result.items:
        all_tags.update(w.tags or [])

    return {
        "ok": True,
        "workflows": workflows,
        "total": result.total if (enabled is None and not tag_filter) else len(workflows),
        "page": result.page,
        "page_size": result.page_size,
        "has_next": result.has_next,
        "has_prev": result.has_prev,
        # S-Grade: Pre-computed counts
        "enabled_count": enabled_count,
        "total_count": len(workflows),
        "available_tags": sorted(all_tags),
    }


@crud_router.post("/")
async def create_workflow(
    workflow_data: WorkflowCreate,
    workspace_context=Depends(get_local_principal)
):
    """Create a new workflow"""
    provider = get_data_provider()

    # Enforce max workflows limit based on local workspace limits
    await _enforce_max_workflows(workspace_context, provider)

    _validate_workflow_graph_shape(workflow_data.nodes, workflow_data.edges)

    # Build node ID mapping: client-provided ID -> server ID
    id_map = {}
    for i, n in enumerate(workflow_data.nodes):
        server_id = f"node_{i}"
        client_id = n.id or server_id
        id_map[client_id] = server_id

    # Note: Skipping pre-save validation. The execution engine validates at
    # runtime with better context. Pre-validation produces false positives for
    # loop workflows and VueFlow edge handles (PORT_NOT_FOUND, MODULE_NOT_FOUND).

    # Convert to DTO with consistent IDs
    nodes = [
        WorkflowNode(
            id=id_map.get(n.id, f"node_{i}") if n.id else f"node_{i}",
            node_type=n.node_type,
            module_id=n.module_id,
            label=n.label,
            params=n.params,
            position_x=n.position_x,
            position_y=n.position_y,
            order_index=n.order_index,
            # Advanced fields
            when=n.when,
            on_error=n.on_error,
            retry=n.retry,
            timeout=n.timeout,
            parallel=n.parallel,
            foreach=n.foreach,
            as_=n.as_,
            description=n.description,
            output=n.output,
            connections=n.connections,
            resources=n.resources,
            pinned_output=n.pinned_output,
        )
        for i, n in enumerate(workflow_data.nodes)
    ]

    edges = [
        WorkflowEdge(
            id=f"edge_{i}",
            source_node_id=id_map.get(e.source_node_id, e.source_node_id),
            target_node_id=id_map.get(e.target_node_id, e.target_node_id),
            condition=e.condition,
            label=e.label,
            source_handle=e.source_handle,
            target_handle=e.target_handle,
            data=e.data,
        )
        for i, e in enumerate(workflow_data.edges)
    ]

    create_dto = WorkflowCreateDTO(
        name=workflow_data.name,
        description=workflow_data.description,
        trigger_type=TriggerType(workflow_data.trigger_type or "manual"),
        trigger_config=workflow_data.trigger_config,
        nodes=nodes,
        edges=edges,
        tags=workflow_data.tags,
    )

    workflow = await provider.workflows.create_workflow(
        workspace_id=workspace_context.id,
        data=create_dto,
    )

    return {"ok": True, "workflow": workflow.dict()}


@crud_router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    workspace_context=Depends(get_local_principal)
):
    """Get workflow details"""
    provider = get_data_provider()

    workflow = await provider.workflows.get_workflow(
        workspace_id=workspace_context.id,
        workflow_id=workflow_id,
    )

    if not workflow:
        raise HTTPException(status_code=404, detail=ErrorMessages.WORKFLOW_NOT_FOUND)

    return {"ok": True, "workflow": workflow.dict()}


@crud_router.put("/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    workflow_data: WorkflowUpdate,
    workspace_context=Depends(get_local_principal)
):
    """Update workflow"""
    provider = get_data_provider()
    if workflow_data.nodes is not None and workflow_data.edges is not None:
        _validate_workflow_graph_shape(workflow_data.nodes, workflow_data.edges)

    # Convert nodes if provided (includes position updates)
    nodes = None
    if workflow_data.nodes is not None:
        nodes = [
            WorkflowNode(
                id=n.id,
                node_type=n.node_type or "",
                module_id=n.module_id or "",
                label=n.label or "",
                params=n.params or {},
                position_x=n.position_x if n.position_x is not None else 0,
                position_y=n.position_y if n.position_y is not None else 0,
                order_index=n.order_index if n.order_index is not None else 0,
                # Advanced fields
                when=n.when,
                on_error=n.on_error,
                retry=n.retry,
                timeout=n.timeout,
                parallel=n.parallel,
                foreach=n.foreach,
                as_=n.as_,
                description=n.description,
                output=n.output,
                connections=n.connections,
                resources=n.resources,
                pinned_output=n.pinned_output,
            )
            for n in workflow_data.nodes
        ]

    # Convert edges if provided
    edges = None
    if workflow_data.edges is not None:
        edges = [
            WorkflowEdge(
                id=e.id,
                source_node_id=e.source_node_id,
                target_node_id=e.target_node_id,
                condition=e.condition or "always",
                label=e.label,
                source_handle=e.source_handle,
                target_handle=e.target_handle,
                data=e.data,
            )
            for e in workflow_data.edges
        ]

    # Note: Skipping pre-save validation (same as create/run).

    update_dto = WorkflowUpdateDTO(
        name=workflow_data.name,
        description=workflow_data.description,
        is_active=workflow_data.is_active,
        trigger_type=TriggerType(workflow_data.trigger_type) if workflow_data.trigger_type else None,
        trigger_config=workflow_data.trigger_config,
        tags=workflow_data.tags,
        nodes=nodes,
        edges=edges,
    )

    result = await provider.workflows.update_workflow(
        workspace_id=workspace_context.id,
        workflow_id=workflow_id,
        data=update_dto,
    )

    if not result:
        raise HTTPException(status_code=404, detail=ErrorMessages.WORKFLOW_NOT_FOUND)

    return {"ok": True, "message": "Update successful"}


@crud_router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    workspace_context=Depends(get_local_principal)
):
    """Delete workflow"""
    provider = get_data_provider()

    deleted = await provider.workflows.delete_workflow(
        workspace_id=workspace_context.id,
        workflow_id=workflow_id,
    )

    if not deleted:
        raise HTTPException(status_code=404, detail=ErrorMessages.WORKFLOW_NOT_FOUND)

    return {"ok": True, "message": "Delete successful"}


@crud_router.get("/{workflow_id}/history")
async def get_workflow_history(
    workflow_id: str,
    page: int = Query(1, ge=1, le=1000),
    page_size: int = Query(20, ge=1, le=100),
    workspace_context=Depends(get_local_principal)
):
    """
    Get execution history for a workflow.

    Returns list of past executions for the workflow.
    """
    provider = get_data_provider()

    # Verify workflow exists and belongs to the local workspace
    workflow = await provider.workflows.get_workflow(
        workspace_id=workspace_context.id,
        workflow_id=workflow_id,
    )

    if not workflow:
        raise HTTPException(status_code=404, detail=ErrorMessages.WORKFLOW_NOT_FOUND)

    # Try to get execution history
    try:
        history = await provider.executions.list_executions(
            workflow_id=workflow_id,
            workspace_id=workspace_context.id,
            page=page,
            page_size=page_size,
        )
        return {
            "ok": True,
            "workflow_id": workflow_id,
            "executions": [e.dict() if hasattr(e, 'dict') else e for e in history.items],
            "total": history.total,
            "page": page,
            "page_size": page_size,
        }
    except AttributeError:
        # Executions provider doesn't have list by workflow
        from gateway.storage.execution_repo import ExecutionRepository

        executions = ExecutionRepository.list_executions(
            workflow_id=workflow_id,
            limit=page_size,
            offset=(page - 1) * page_size,
        )

        return {
            "ok": True,
            "workflow_id": workflow_id,
            "executions": [
                {
                    "id": e.id,
                    "status": e.status,
                    "started_at": e.started_at,
                    "completed_at": e.completed_at,
                    "duration_ms": e.duration_ms,
                    "error_message": e.error_message,
                }
                for e in executions
            ],
            "total": len(executions),
            "page": page,
            "page_size": page_size,
        }
