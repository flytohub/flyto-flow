"""
Engine API Routes - Variable Introspection and Autocomplete

Provides endpoints for workflow editor to:
- Introspect available variables at any node position
- Get autocomplete suggestions for expressions
- Validate expression syntax

Uses flyto-core's engine SDK for all introspection logic.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================

class IntrospectRequest(BaseModel):
    """Request for variable introspection"""
    workflow: Dict[str, Any] = Field(..., description="Workflow definition with nodes and edges")
    node_id: str = Field(..., description="Target node ID")
    mode: str = Field(default="edit", description="Introspection mode: 'edit' or 'runtime'")
    context_snapshot: Optional[Dict[str, Any]] = Field(default=None, description="Optional runtime context")
    # S-Grade options
    flatten: bool = Field(default=False, description="Return pre-flattened items")
    group: bool = Field(default=False, description="Return pre-grouped items (requires flatten=True)")


class AutocompleteRequest(BaseModel):
    """Request for autocomplete suggestions"""
    workflow: Dict[str, Any] = Field(..., description="Workflow definition")
    node_id: str = Field(..., description="Target node ID")
    prefix: str = Field(default="", description="Current input prefix")
    limit: int = Field(default=20, description="Maximum suggestions")
    context_snapshot: Optional[Dict[str, Any]] = Field(default=None, description="Optional runtime context")


class ValidateRequest(BaseModel):
    """Request for expression validation"""
    workflow: Dict[str, Any] = Field(..., description="Workflow definition")
    node_id: str = Field(..., description="Target node ID")
    expression: str = Field(..., description="Expression to validate")
    expected_type: Optional[str] = Field(default=None, description="Expected result type")
    context_snapshot: Optional[Dict[str, Any]] = Field(default=None, description="Optional runtime context")


class VarInfoResponse(BaseModel):
    """Variable information response"""
    path: str
    type: str
    description: str = ""
    example: Optional[Any] = None
    origin_node: Optional[str] = None
    is_available: bool = True


class PortInfoResponse(BaseModel):
    """Port information response"""
    port_id: str
    type: str
    description: str = ""
    example: Optional[Any] = None
    fields: Dict[str, VarInfoResponse] = {}


class NodeInfoResponse(BaseModel):
    """Node information response"""
    node_id: str
    node_type: str
    is_reachable: bool = True
    ports: Dict[str, PortInfoResponse] = {}


class AutocompleteItemResponse(BaseModel):
    """Single autocomplete suggestion"""
    path: str
    display: str
    type: str
    description: str = ""
    insert_text: str = ""
    score: float = 1.0


# =============================================================================
# S-Grade Helper Functions
# =============================================================================

def _catalog_item(
    path: str,
    item_type: str,
    category: str,
    description: str = "",
    **extra: Any,
) -> Dict[str, Any]:
    """Build one flattened catalog item using the frontend wire shape."""
    return {
        "path": path,
        "display": path,
        "type": item_type,
        "category": category,
        "description": description,
        "insertText": extra.pop("insert_text", path),
        **extra,
    }


def _flatten_fields(
    base_path: str,
    fields: Dict[str, Any],
    category: str,
    **metadata: Any,
) -> List[Dict[str, Any]]:
    return [
        _catalog_item(
            f"{base_path}.{field_name}",
            field_info.get("type", "any"),
            category,
            field_info.get("description", ""),
            **metadata,
        )
        for field_name, field_info in fields.items()
    ]


def _input_item(port_id: str, port_info: Dict[str, Any]) -> Dict[str, Any]:
    base_path = "input" if port_id == "main" else f"inputs.{port_id}"
    return _catalog_item(
        base_path,
        port_info.get("type", "any"),
        "input",
        port_info.get("description") or f"Input port: {port_id}",
    )


def _flatten_inputs(inputs: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for port_id, port_info in inputs.items():
        base_path = "input" if port_id == "main" else f"inputs.{port_id}"
        items.append(_input_item(port_id, port_info))
        items.extend(_flatten_fields(base_path, port_info.get("fields") or {}, "input"))
    return items


def _node_metadata(node_info: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "isConditional": node_info.get("is_conditional", False),
        "branchSource": node_info.get("branch_source"),
        "branchPort": node_info.get("branch_port"),
    }


def _node_item(node_id: str, node_info: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
    description = f"Output from {node_info.get('node_type', 'node')}"
    return _catalog_item(node_id, "object", "node", description, **metadata)


def _node_port_item(port_path: str, port_id: str, port_info: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
    description = port_info.get("description") or f"Port: {port_id}"
    return _catalog_item(port_path, port_info.get("type", "any"), "node", description, **metadata)


def _node_port_items(node_id: str, ports: Dict[str, Any], metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for port_id, port_info in ports.items():
        port_path = f"{node_id}.{port_id}"
        items.append(_node_port_item(port_path, port_id, port_info, metadata))
        items.extend(_flatten_fields(port_path, port_info.get("fields") or {}, "node", **metadata))
    return items


def _flatten_nodes(nodes: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for node_id, node_info in nodes.items():
        metadata = _node_metadata(node_info)
        items.append(_node_item(node_id, node_info, metadata))
        items.extend(_node_port_items(node_id, node_info.get("ports") or {}, metadata))
    return items


def _flatten_keyed_section(
    section: Dict[str, Any],
    prefix: str,
    category: str,
    default_type: str,
    label: str,
) -> List[Dict[str, Any]]:
    return [
        _catalog_item(
            f"{prefix}.{key}",
            info.get("type", default_type),
            category,
            info.get("description") or f"{label}: {key}",
        )
        for key, info in section.items()
    ]


def _flatten_catalog(catalog: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Flatten nested VarCatalog into a flat list for UI.

    S-Grade: This computation happens on backend.
    """
    items = [
        _catalog_item(
            "input",
            "any",
            "input",
            "Main input (shorthand)",
            insert_text="{{input}}",
        )
    ]
    items.extend(_flatten_inputs(catalog.get("inputs") or {}))
    items.extend(_flatten_nodes(catalog.get("nodes") or {}))
    items.extend(_flatten_keyed_section(catalog.get("params") or {}, "params", "param", "any", "Parameter"))
    items.extend(_flatten_keyed_section(catalog.get("globals") or {}, "global", "global", "any", "Global"))
    items.extend(_flatten_keyed_section(catalog.get("env") or {}, "env", "env", "string", "Environment"))
    return items


def _group_by_category(items: List[Dict[str, Any]], separate_conditional: bool = True) -> Dict[str, Any]:
    """
    Group variables by category for sidebar display.

    S-Grade: This grouping happens on backend.
    """
    groups = {
        "input": {"label": "Input", "icon": "ArrowRight", "items": []},
        "node": {"label": "Nodes", "icon": "Box", "items": []},
        "conditional": {"label": "Conditional", "icon": "GitBranch", "items": []},
        "param": {"label": "Parameters", "icon": "Settings", "items": []},
        "global": {"label": "Globals", "icon": "Globe", "items": []},
        "env": {"label": "Environment", "icon": "Terminal", "items": []}
    }

    for item in items:
        category = item.get("category", "node")

        # Separate conditional variables if enabled
        if separate_conditional and item.get("isConditional") and category == "node":
            category = "conditional"

        if category in groups:
            groups[category]["items"].append(item)

    # Filter out empty groups
    return {k: v for k, v in groups.items() if v["items"]}


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/introspect")
async def introspect_variables(request: IntrospectRequest) -> Dict[str, Any]:
    """
    Introspect available variables for a node.

    Returns VarCatalog with all variables available at the specified node position.
    Used by the variable sidebar in workflow editor.
    """
    try:
        try:
            from core.engine.introspection.catalog import build_catalog
            from core.engine.sdk.models import IntrospectionMode
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="Engine SDK not available. Install flyto-core."
            )

        mode = (
            IntrospectionMode.RUNTIME
            if request.mode == "runtime"
            else IntrospectionMode.EDIT
        )

        catalog = build_catalog(
            workflow=request.workflow,
            node_id=request.node_id,
            mode=mode,
            context_snapshot=request.context_snapshot,
        )

        catalog_dict = catalog.to_dict()
        result = {"ok": True, **catalog_dict}

        # S-Grade: Return pre-flattened items if requested
        if request.flatten:
            flattened = _flatten_catalog(catalog_dict)
            result["items"] = flattened

            # S-Grade: Return pre-grouped items if requested
            if request.group:
                result["grouped"] = _group_by_category(flattened)

        return result

    except ImportError as e:
        logger.error(f"Import error in introspect: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error in introspect: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/autocomplete")
async def get_autocomplete(request: AutocompleteRequest) -> Dict[str, Any]:
    """
    Get autocomplete suggestions for an expression prefix.

    Returns scored suggestions based on prefix matching.
    Used by expression input fields in workflow editor.
    """
    try:
        try:
            from core.engine.introspection.autocomplete import autocomplete
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="Engine SDK not available. Install flyto-core."
            )

        result = autocomplete(
            workflow=request.workflow,
            node_id=request.node_id,
            prefix=request.prefix,
            context_snapshot=request.context_snapshot,
            limit=request.limit,
        )

        return {
            "ok": True,
            "prefix": result.prefix,
            "items": [
                {
                    "path": item.path,
                    "display": item.display,
                    "type": item.var_type,
                    "description": item.description,
                    "insert_text": item.insert_text,
                    "score": item.score,
                }
                for item in result.items
            ],
        }

    except ImportError as e:
        logger.error(f"Import error in autocomplete: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error in autocomplete: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_expression_endpoint(request: ValidateRequest) -> Dict[str, Any]:
    """
    Validate an expression.

    Checks if the expression references valid variables in the catalog.
    Returns validation result with errors/warnings.
    """
    try:
        try:
            from core.engine.introspection.autocomplete import validate_expression
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="Engine SDK not available. Install flyto-core."
            )

        result = validate_expression(
            workflow=request.workflow,
            node_id=request.node_id,
            expression=request.expression,
            expected_type=request.expected_type,
            context_snapshot=request.context_snapshot,
        )

        return {"ok": True, **result}

    except ImportError as e:
        logger.error(f"Import error in validate: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error in validate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def engine_health() -> Dict[str, Any]:
    """Check engine SDK availability"""
    sdk_available = False
    version = "unknown"

    try:
        from core.engine.sdk import models
        sdk_available = True
        version = getattr(models, "__version__", "1.0.0")
    except ImportError:
        pass

    return {
        "ok": True,
        "sdk_available": sdk_available,
        "version": version,
    }
