"""
Module Validation Endpoints

Connection validation and compatibility endpoints.
Uses core.validation API as single source of truth.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, Depends

from gateway.local_context import get_local_principal
from gateway.providers.base import WorkspaceContext

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_validation_api():
    """Get validation API from flyto-core"""
    try:
        from core.validation import (
            validate_connection as core_validate_connection,
            validate_replacement as core_validate_replacement,
            get_connectable as core_get_connectable,
            get_connectable_for_replacement as core_get_connectable_for_replacement,
            get_startable_modules as core_get_startable_modules,
        )
        return {
            'validate_connection': core_validate_connection,
            'validate_replacement': core_validate_replacement,
            'get_connectable': core_get_connectable,
            'get_connectable_for_replacement': core_get_connectable_for_replacement,
            'get_startable_modules': core_get_startable_modules,
        }
    except ImportError as e:
        logger.warning(f"core.validation not available: {e}")
        return None


@router.get("/validate-connection")
async def validate_connection(
    source: str = Query(..., description="Source module ID"),
    target: str = Query(..., description="Target module ID"),
    source_port: str = Query(default=None, description="Source port name"),
    target_port: str = Query(default=None, description="Target port name"),
) -> Dict[str, Any]:
    """
    Validate if two modules can be connected.

    Uses core.validation.validate_connection as single source of truth.
    Cloud does NOT implement validation logic - only calls core API.
    """
    api = _get_validation_api()

    if api is None:
        # P2 Fix: Return invalid when validation unavailable to prevent unsafe connections
        return {
            "valid": False,
            "reason": "Validation service unavailable - please try again later",
            "error_code": "VALIDATION_UNAVAILABLE",
            "fallback": True
        }

    result = api['validate_connection'](
        from_module_id=source,
        to_module_id=target,
        from_port=source_port,
        to_port=target_port,
    )

    return {
        "valid": result.valid,
        "error_code": result.error_code,
        "reason": result.error_message,
        "meta": result.meta
    }


from pydantic import BaseModel


class EdgeInfo(BaseModel):
    """Edge information for workflow context validation"""
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None


class NodeInfo(BaseModel):
    """Node information for workflow context validation"""
    id: str
    module: str  # module_id


class WorkflowConnectionRequest(BaseModel):
    """Request for validating connection with workflow context"""
    source_node_id: str
    target_node_id: str
    source_module: str
    target_module: str
    source_port: Optional[str] = None
    target_port: Optional[str] = None
    existing_edges: List[EdgeInfo] = []


@router.post("/validate-connection-with-context")
async def validate_connection_with_context(
    request: WorkflowConnectionRequest
) -> Dict[str, Any]:
    """
    Validate connection with workflow context (existing edges).

    This endpoint performs:
    1. Module-level validation (type compatibility) via core API
    2. Workflow-level validation (max_connections check)

    Frontend should call this instead of GET /validate-connection
    when it has workflow context available.
    """
    # Step 0: True self-connection check (same node instance → itself)
    if request.source_node_id == request.target_node_id:
        return {
            "valid": False,
            "error_code": "SELF_CONNECTION",
            "reason": "A node cannot connect to itself",
            "meta": {}
        }

    # Step 1: Module-level validation
    api = _get_validation_api()

    if api is None:
        return {
            "valid": False,
            "reason": "Validation service unavailable",
            "error_code": "VALIDATION_UNAVAILABLE",
            "fallback": True
        }

    result = api['validate_connection'](
        from_module_id=request.source_module,
        to_module_id=request.target_module,
        from_port=request.source_port,
        to_port=request.target_port,
    )

    if not result.valid:
        return {
            "valid": False,
            "error_code": result.error_code,
            "reason": result.error_message,
            "meta": result.meta
        }

    # Step 2: Workflow-level validation - max_connections check
    # Get target module metadata for port limits
    from services.registry_loader import get_module_registry
    registry = get_module_registry()
    target_metadata = registry.get_metadata(request.target_module) if registry else None

    if target_metadata:
        # Find the target port definition
        input_ports = target_metadata.get('inputPorts') or target_metadata.get('input_ports') or []
        target_port_def = next(
            (p for p in input_ports if p.get('id') == request.target_port),
            None
        )

        if target_port_def:
            max_conn = target_port_def.get('maxConnections') or target_port_def.get('max_connections')

            if max_conn is not None and max_conn > 0:
                # Count existing connections to this port
                existing_count = sum(
                    1 for edge in request.existing_edges
                    if edge.target == request.target_node_id
                    and (edge.targetHandle or 'input') == request.target_port
                )

                if existing_count >= max_conn:
                    return {
                        "valid": False,
                        "error_code": "MAX_CONNECTIONS",
                        "reason": f"Port '{request.target_port}' already has maximum connections ({max_conn})",
                        "meta": {
                            "port": request.target_port,
                            "max_connections": max_conn,
                            "current_connections": existing_count
                        }
                    }

    return {
        "valid": True,
        "error_code": None,
        "reason": None,
        "meta": {}
    }


@router.get("/connectable")
async def get_connectable_modules(
    module_id: str = Query(..., description="Module ID to find connectable modules for"),
    direction: str = Query(default="next", description="'next' for downstream, 'prev' for upstream"),
    limit: int = Query(default=0, description="Maximum results (0 = no limit)"),
    search: Optional[str] = Query(default=None, description="Search filter"),
    category: Optional[str] = Query(default=None, description="Category filter"),
) -> Dict[str, Any]:
    """
    Get modules that can connect to/from a given module.

    Uses core.validation.get_connectable as single source of truth.
    """
    api = _get_validation_api()

    if api is None:
        return {
            "modules": [],
            "error": "Validation not available"
        }

    modules = api['get_connectable'](
        module_id=module_id,
        direction=direction,
        limit=limit if limit > 0 else 9999,
        search=search,
        category=category,
    )

    return {
        "module_id": module_id,
        "direction": direction,
        "modules": modules,
        "total": len(modules)
    }


# Keep old endpoint for backwards compatibility
@router.get("/compatible")
async def get_compatible_modules(
    after: str = Query(..., description="Module ID to find compatible successors for"),
    context: Optional[str] = Query(default=None, description="Deprecated - ignored"),
    include_composites: bool = Query(default=True, description="Include composite modules"),
) -> Dict[str, Any]:
    """
    Get modules that can follow a given module (backwards compatibility).

    DEPRECATED: Use /connectable instead.
    """
    api = _get_validation_api()

    if api is None:
        return {
            "modules": [],
            "error": "Validation not available"
        }

    modules = api['get_connectable'](
        module_id=after,
        direction='next',
        limit=100,
    )

    # Return just module IDs for backwards compatibility
    module_ids = [m['module_id'] for m in modules]

    return {
        "after": after,
        "modules": module_ids,
        "total": len(module_ids)
    }


@router.get("/starters")
async def get_starter_modules(
    include_composites: bool = Query(default=True, description="Include composite modules"),
    include_templates: bool = Query(default=True, description="Include local workflow templates"),
    limit: int = Query(default=100, description="Maximum results"),
    workspace_context: Optional[WorkspaceContext] = Depends(get_local_principal),
) -> Dict[str, Any]:
    """
    Get modules that can start a workflow.

    Uses core.validation.get_startable_modules as single source of truth.
    Also includes local workflow templates.
    """
    api = _get_validation_api()

    modules = []

    if api is not None:
        modules = api['get_startable_modules']()

        # Filter out composites if requested
        if not include_composites:
            modules = [m for m in modules if not m['module_id'].startswith('composite.')]

    # Add local workflow templates as starters.
    template_modules = []
    if include_templates and workspace_context:
        try:
            from api.modules.catalog import get_workspace_templates_as_modules

            workspace_id = workspace_context.id if hasattr(workspace_context, 'id') else workspace_context.get('id')
            if workspace_id:
                template_modules = await get_workspace_templates_as_modules(workspace_id)
                for module in template_modules:
                    module["can_start"] = True
                    module["start_requires_params"] = list(
                        module.get("params_schema", {}).get("required", [])
                    )

        except Exception as e:
            logger.warning(f"Error loading local templates for starters: {e}")

    # Combine core modules and template modules
    all_modules = modules + template_modules

    return {
        "modules": all_modules[:limit],
        "total": len(all_modules),
        "template_count": len(template_modules),
    }


@router.get("/connectable-summary")
async def get_connectable_summary(
    module_id: str = Query(..., description="Module ID"),
    direction: str = Query(default="next", description="'next' or 'prev'"),
) -> Dict[str, Any]:
    """
    Get category counts of connectable modules.

    Returns: {'browser': 12, 'http': 8, ...}
    """
    try:
        from core.validation import get_connectable_summary as core_get_summary
    except ImportError:
        return {"summary": {}, "error": "Validation not available"}

    summary = core_get_summary(module_id, direction)

    return {
        "module_id": module_id,
        "direction": direction,
        "summary": summary
    }


@router.get("/validate-insertion")
async def validate_insertion(
    source_module: str = Query(..., description="Source module ID (before insertion point)"),
    target_module: str = Query(..., description="Target module ID (after insertion point)"),
    insert_module: str = Query(..., description="Module ID to insert between source and target"),
    source_port: str = Query(default="output", description="Original source port"),
    target_port: str = Query(default="input", description="Original target port"),
) -> Dict[str, Any]:
    """
    Validate if a module can be inserted between two connected modules.

    Validates both connections:
    1. source → insert_module (using source_port → input)
    2. insert_module → target (using output → target_port)

    Returns validation result for both connections.
    """
    api = _get_validation_api()

    if api is None:
        # P2 Fix: Return invalid when validation unavailable to prevent unsafe insertions
        return {
            "valid": False,
            "reason": "Validation service unavailable - please try again later",
            "error_code": "VALIDATION_UNAVAILABLE",
            "fallback": True,
            "source_to_insert": {"valid": False, "reason": "Validation unavailable"},
            "insert_to_target": {"valid": False, "reason": "Validation unavailable"},
        }

    # Validate source → insert_module
    source_result = api['validate_connection'](
        from_module_id=source_module,
        to_module_id=insert_module,
        from_port=source_port,
        to_port="input",
    )

    # Validate insert_module → target
    insert_result = api['validate_connection'](
        from_module_id=insert_module,
        to_module_id=target_module,
        from_port="output",
        to_port=target_port,
    )

    # Both must be valid for insertion to work
    overall_valid = source_result.valid and insert_result.valid

    # Build error message if not valid
    errors = []
    if not source_result.valid:
        errors.append(f"Source → Insert: {source_result.error_message}")
    if not insert_result.valid:
        errors.append(f"Insert → Target: {insert_result.error_message}")

    return {
        "valid": overall_valid,
        "reason": "; ".join(errors) if errors else "Insertion valid",
        "source_to_insert": {
            "valid": source_result.valid,
            "error_code": source_result.error_code,
            "reason": source_result.error_message,
        },
        "insert_to_target": {
            "valid": insert_result.valid,
            "error_code": insert_result.error_code,
            "reason": insert_result.error_message,
        },
    }


@router.get("/validate-replacement")
async def validate_replacement(
    new_module: str = Query(..., description="New module ID to replace with"),
    upstream_module: Optional[str] = Query(default=None, description="Upstream module ID (if connected)"),
    downstream_module: Optional[str] = Query(default=None, description="Downstream module ID (if connected)"),
    upstream_port: str = Query(default="output", description="Upstream module's output port"),
    downstream_port: str = Query(default="input", description="Downstream module's input port"),
) -> Dict[str, Any]:
    """
    Validate if a module can replace an existing node.

    Uses core.validation.validate_replacement as single source of truth.
    """
    api = _get_validation_api()

    if api is None:
        # P2 Fix: Return invalid when validation unavailable to prevent unsafe replacements
        return {
            "valid": False,
            "reason": "Validation service unavailable - please try again later",
            "error_code": "VALIDATION_UNAVAILABLE",
            "fallback": True,
        }

    result = api['validate_replacement'](
        new_module_id=new_module,
        upstream_module_id=upstream_module,
        downstream_module_id=downstream_module,
        upstream_port=upstream_port,
        downstream_port=downstream_port,
    )

    return {
        "valid": result.valid,
        "error_code": result.error_code,
        "reason": result.error_message,
    }


@router.get("/connectable-for-replacement")
async def get_connectable_for_replacement(
    upstream_module: Optional[str] = Query(default=None, description="Upstream module ID (if connected)"),
    downstream_module: Optional[str] = Query(default=None, description="Downstream module ID (if connected)"),
    limit: int = Query(default=200, description="Maximum results"),
) -> Dict[str, Any]:
    """
    Get modules that can replace a node (compatible with both upstream and downstream).

    Uses core.validation.get_connectable_for_replacement as single source of truth.
    """
    api = _get_validation_api()

    if api is None:
        return {
            "modules": [],
            "error": "Validation not available"
        }

    modules = api['get_connectable_for_replacement'](
        upstream_module_id=upstream_module,
        downstream_module_id=downstream_module,
        limit=limit,
    )

    return {
        "modules": modules,
        "total": len(modules),
        "upstream_module": upstream_module,
        "downstream_module": downstream_module,
    }
