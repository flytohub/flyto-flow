"""
Workflow Execution Endpoints

Execute workflows and manage execution history.
"""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from common.error_messages import ErrorMessages
from api.workflows.models import WorkflowRunRequest
from gateway.auth import get_current_active_user
from gateway.providers.hub import get_data_provider
from services.quota_enforcement import require_execution_quota

logger = logging.getLogger(__name__)

cloud_router = APIRouter()
run_router = APIRouter()

# Combined router (for cloud + dev mode)
router = APIRouter()
router.include_router(run_router)
router.include_router(cloud_router)



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


async def _check_points_quota(user_id: str, plan_name: str):
    """Check monthly points quota and fail closed when usage cannot be verified."""
    try:
        plan = (plan_name or "free").lower()
        points_limit = await _resolve_monthly_points_limit(plan)
        if points_limit is not None:
            usage = await _resolve_current_points_usage(user_id)
            if usage.get("total_points", 0) >= points_limit:
                raise HTTPException(
                    status_code=402,
                    detail="Monthly points quota exceeded. Upgrade your plan for more points.",
                )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Points quota verification failed")
        raise HTTPException(
            status_code=503,
            detail="Unable to verify monthly points quota",
        ) from exc


async def _resolve_monthly_points_limit(plan: str):
    from services.plan_config import get_monthly_points_limit

    return await get_monthly_points_limit(plan)


async def _resolve_current_points_usage(user_id: str) -> dict:
    from services.cloud.metering_service import get_metering_service

    return await get_metering_service().get_current_usage(user_id)


@run_router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    execution_params: Optional[Dict[str, Any]] = None,
    current_user=Depends(require_execution_quota)
):
    """
    Execute workflow by ID.
    Returns execution_id for tracking and cancellation.

    This is a LOCAL endpoint (run_router) because it requires flyto-core ExecutionManager.
    Workflow data is fetched from Firestore via data_provider (dev/cloud mode)
    or via cloud proxy HTTP (local/desktop mode).
    """
    import yaml
    from services.runtime.execution_manager import get_execution_manager

    provider = get_data_provider()

    workflow = await _fetch_workflow(
        provider=provider, user_id=current_user.id, workflow_id=workflow_id,
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

    await _check_points_quota(
        current_user.id,
        getattr(current_user, "subscription_plan", None),
    )

    try:
        exec_manager = get_execution_manager()
        execution_id = await exec_manager.start(
            workflow_yaml=workflow_yaml,
            variables=execution_params or {},
            workflow_id=workflow_id,
            user_id=current_user.id,
        )
        return {
            "ok": True,
            "execution_id": execution_id,
            "status": "running",
            "message": "Workflow execution started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start execution: {e}")


async def _fetch_workflow(provider, user_id: str, workflow_id: str):
    """
    Fetch workflow data from Firestore (dev/cloud) or cloud proxy (local/desktop).

    Returns workflow model or dict, or None if not found.
    """
    if provider is not None and hasattr(provider, 'workflows') and provider.workflows is not None:
        return await provider.workflows.get_workflow(
            user_id=user_id,
            workflow_id=workflow_id,
            include_graph=True,
        )

    # Local mode: data_provider is None, fetch via cloud proxy HTTP
    try:
        from config.settings import get_settings
        from local.cloud_proxy import get_proxy_client

        settings = get_settings()
        client = await get_proxy_client(settings.cloud_api_url)
        resp = await client.get(
            f"/api/workflows/{workflow_id}",
            params={"include_graph": "true"},
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        return data.get("workflow") or data
    except Exception as exc:
        logger.exception("Failed to fetch workflow through cloud proxy")
        raise HTTPException(
            status_code=502,
            detail="Cannot fetch workflow data from cloud",
        ) from exc


async def get_optional_user_from_token(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Get user from token if provided, otherwise return None."""
    logger.debug("Optional authorization present=%s", bool(authorization))
    if not authorization or not authorization.startswith("Bearer "):
        logger.debug("No authorization header or not Bearer token")
        return None

    token = authorization.split("Bearer ")[1]
    try:
        from gateway.providers.hub import get_auth_provider
        auth_provider = get_auth_provider()
        result = await auth_provider.verify_token(token)
        logger.debug("Optional token verification succeeded=%s", bool(result.ok and result.user))
        if result.ok and result.user:
            return result.user.model_dump()
    except Exception:
        logger.debug("Optional token verification failed", exc_info=True)
    return None


@run_router.post("/run")
async def run_workflow_direct(
    request: WorkflowRunRequest,
    current_user: Optional[dict] = Depends(get_optional_user_from_token)
):
    """
    Run workflow directly using Core engine.
    Accepts workflow as YAML string and executes immediately.
    Returns execution_id for tracking.

    Note: Auth is optional - local execution works without login.
    If authenticated, execution is associated with user for status tracking.
    """
    import yaml
    from services.runtime.execution_manager import get_execution_manager

    # Get user_id from token if authenticated
    user_id = current_user.get("id") if current_user else None
    logger.debug("Direct workflow request authenticated=%s", bool(user_id))

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

    # Quota check: monthly points (only for authenticated users)
    if current_user:
        await _check_points_quota(user_id, current_user.get("subscription_plan"))

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
            user_id=user_id,
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


@cloud_router.post("/{workflow_id}/execute")
async def execute_cloud_workflow(
    workflow_id: str,
    execution_params: Optional[Dict[str, Any]] = None,
    current_user=Depends(require_execution_quota),
):
    """Dispatch a persisted cloud or enterprise workflow through its provider."""
    provider = get_data_provider()

    try:
        execution = await provider.workflows.execute_workflow(
            user_id=current_user.id,
            workflow_id=workflow_id,
            params=execution_params or {},
        )
    except Exception:
        logger.exception("Provider workflow execution failed")
        raise HTTPException(
            status_code=502,
            detail="Workflow execution service unavailable",
        )

    return {
        "ok": True,
        "execution_id": execution.id,
        "status": execution.status,
        "started_at": execution.started_at.isoformat(),
        "message": "Workflow execution started",
    }


@cloud_router.get("/{workflow_id}/executions")
async def list_executions(
    workflow_id: str,
    limit: int = 20,
    current_user=Depends(get_current_active_user)
):
    """List workflow execution history"""
    provider = get_data_provider()

    executions = await provider.workflows.list_executions(
        user_id=current_user.id,
        workflow_id=workflow_id,
        limit=limit,
    )

    return {"ok": True, "executions": [e.dict() for e in executions]}


@cloud_router.get("/executions/{execution_id}")
async def get_execution(
    execution_id: str,
    workflow_id: str,
    current_user=Depends(get_current_active_user)
):
    """Get execution details"""
    provider = get_data_provider()

    execution = await provider.workflows.get_execution(
        user_id=current_user.id,
        workflow_id=workflow_id,
        execution_id=execution_id,
    )

    if not execution:
        raise HTTPException(status_code=404, detail=ErrorMessages.EXECUTION_NOT_FOUND)

    return {"ok": True, "execution": execution.dict()}
