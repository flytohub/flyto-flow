"""
Lineage Item Routes

Item-level lineage endpoints for tracking individual data items.
Similar to n8n's pairedItem concept.
"""

import re
import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from api.lineage.models import (
    ItemOriginResponse,
    TrackedOutputResponse,
    ItemLevelLineageResponse,
)
from api.lineage.services import (
    load_execution_evidence,
    load_tracking_data,
    get_value_preview,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/executions/{execution_id}/item-lineage")
async def get_item_level_lineage(
    execution_id: str,
) -> ItemLevelLineageResponse:
    """
    Get item-level lineage for an execution.

    Returns tracked outputs with origin information for each item,
    similar to n8n's pairedItem concept.
    """
    # Try to load tracking data
    tracking_data = load_tracking_data(execution_id)

    if tracking_data and "tracked_outputs" in tracking_data:
        tracked_outputs = []
        total_items = 0

        for node_id, ports in tracking_data["tracked_outputs"].items():
            for port_id, tracked in ports.items():
                origin = None
                if tracked.get("origin"):
                    origin = ItemOriginResponse(
                        node_id=tracked["origin"]["node_id"],
                        port_id=tracked["origin"]["port_id"],
                        index=tracked["origin"].get("index"),
                        key_path=tracked["origin"].get("key_path"),
                        timestamp=tracked["origin"].get("timestamp"),
                        transform_chain=tracked.get("transform_chain", []),
                    )

                # Get item origins for arrays
                item_origins = None
                value = tracked.get("value")
                if isinstance(value, list) and tracked.get("children"):
                    item_origins = []
                    for i in range(len(value)):
                        child = tracked["children"].get(str(i), {})
                        child_origin = child.get("origin", {})
                        if child_origin:
                            item_origins.append(ItemOriginResponse(
                                node_id=child_origin.get("node_id", node_id),
                                port_id=child_origin.get("port_id", port_id),
                                index=i,
                                key_path=child_origin.get("key_path"),
                                timestamp=child_origin.get("timestamp"),
                                transform_chain=child.get("transform_chain", []),
                            ))
                    total_items += len(value)
                else:
                    total_items += 1

                tracked_outputs.append(TrackedOutputResponse(
                    step_id=node_id,
                    port_id=port_id,
                    value_type=type(value).__name__ if value is not None else "null",
                    value_preview=get_value_preview(value),
                    is_array=isinstance(value, list),
                    item_count=len(value) if isinstance(value, list) else None,
                    origin=origin,
                    transform_chain=tracked.get("transform_chain", []),
                    item_origins=item_origins,
                ))

        return ItemLevelLineageResponse(
            execution_id=execution_id,
            tracked_outputs=tracked_outputs,
            total_items_tracked=total_items,
        )

    # Fallback: Build from evidence.jsonl
    steps = load_execution_evidence(execution_id)
    if not steps:
        raise HTTPException(status_code=404, detail="Execution not found")

    tracked_outputs = []
    total_items = 0

    for i, step in enumerate(steps):
        step_id = step.get('step_id', f'step_{i}')
        after = step.get('context_after', {})
        before = step.get('context_before', {})

        # Find produced variables
        for key in after:
            if key not in before or before.get(key) != after.get(key):
                value = after[key]
                is_array = isinstance(value, list)

                # Create basic origin (step-level, not item-level)
                origin = ItemOriginResponse(
                    node_id=step_id,
                    port_id="default",
                    timestamp=step.get('timestamp'),
                    transform_chain=[step_id],
                )

                # For arrays, create item origins (all from same source in fallback)
                item_origins = None
                if is_array:
                    item_origins = [
                        ItemOriginResponse(
                            node_id=step_id,
                            port_id="default",
                            index=idx,
                            timestamp=step.get('timestamp'),
                            transform_chain=[step_id],
                        )
                        for idx in range(len(value))
                    ]
                    total_items += len(value)
                else:
                    total_items += 1

                tracked_outputs.append(TrackedOutputResponse(
                    step_id=step_id,
                    port_id="default",
                    value_type=type(value).__name__,
                    value_preview=get_value_preview(value),
                    is_array=is_array,
                    item_count=len(value) if is_array else None,
                    origin=origin,
                    transform_chain=[step_id],
                    item_origins=item_origins,
                ))

    return ItemLevelLineageResponse(
        execution_id=execution_id,
        tracked_outputs=tracked_outputs,
        total_items_tracked=total_items,
    )


@router.get("/executions/{execution_id}/steps/{step_id}/item-origins")
async def get_step_item_origins(
    execution_id: str,
    step_id: str,
    port_id: str = Query(default="default"),
) -> Dict[str, Any]:
    """
    Get item-level origins for a specific step output.

    Useful for debugging where specific data items came from.
    """
    tracking_data = load_tracking_data(execution_id)

    if tracking_data and "tracked_outputs" in tracking_data:
        node_data = tracking_data["tracked_outputs"].get(step_id, {})
        port_data = node_data.get(port_id, {})

        if port_data:
            value = port_data.get("value")
            children = port_data.get("children", {})

            items = []
            if isinstance(value, list):
                for i, item in enumerate(value):
                    child = children.get(str(i), {})
                    child_origin = child.get("origin", port_data.get("origin", {}))

                    items.append({
                        "index": i,
                        "value_preview": get_value_preview(item),
                        "value_type": type(item).__name__,
                        "origin": {
                            "node_id": child_origin.get("node_id", step_id),
                            "port_id": child_origin.get("port_id", port_id),
                            "index": child_origin.get("index"),
                            "key_path": child_origin.get("key_path"),
                            "timestamp": child_origin.get("timestamp"),
                        },
                        "transform_chain": child.get("transform_chain", [step_id]),
                    })

            return {
                "step_id": step_id,
                "port_id": port_id,
                "value_type": type(value).__name__ if value is not None else "null",
                "is_array": isinstance(value, list),
                "item_count": len(value) if isinstance(value, list) else None,
                "items": items,
            }

    # Fallback to evidence.jsonl
    steps = load_execution_evidence(execution_id)

    for step in steps:
        if step.get('step_id') == step_id:
            after = step.get('context_after', {})

            # Find the value for the requested port
            for key, value in after.items():
                items = []
                if isinstance(value, list):
                    for i, item in enumerate(value):
                        items.append({
                            "index": i,
                            "value_preview": get_value_preview(item),
                            "value_type": type(item).__name__,
                            "origin": {
                                "node_id": step_id,
                                "port_id": "default",
                                "index": i,
                            },
                            "transform_chain": [step_id],
                        })

                if items:
                    return {
                        "step_id": step_id,
                        "port_id": port_id,
                        "value_type": type(value).__name__,
                        "is_array": True,
                        "item_count": len(value),
                        "items": items,
                    }

            # Non-array fallback
            return {
                "step_id": step_id,
                "port_id": port_id,
                "value_type": "unknown",
                "is_array": False,
                "item_count": None,
                "items": [],
            }

    raise HTTPException(status_code=404, detail="Step not found")


def _parse_variable_path(variable_path: str) -> list:
    """Parse a variable path like 'users[0].name' into parts ['users', '0', 'name']."""
    parts = re.split(r'\.|\[|\]', variable_path)
    return [p for p in parts if p]


def _navigate_path(value, tracked, parts: list):
    """
    Navigate a value tree along path parts, tracking lineage metadata.

    Returns (resolved_value, resolved_tracked, found) tuple.
    """
    current = value
    current_tracked = tracked
    for part in parts:
        try:
            idx = int(part)
            if not isinstance(current, list) or idx >= len(current):
                return None, current_tracked, False
            current = current[idx]
            children = current_tracked.get("children", {})
            if str(idx) in children:
                current_tracked = children[str(idx)]
        except ValueError:
            if not isinstance(current, dict) or part not in current:
                return None, current_tracked, False
            current = current[part]
            children = current_tracked.get("children", {})
            if part in children:
                current_tracked = children[part]
    return current, current_tracked, True


def _navigate_value(value, parts: list):
    """Navigate a raw value tree along path parts. Returns the resolved value."""
    for part in parts:
        try:
            idx = int(part)
            if isinstance(value, list) and idx < len(value):
                value = value[idx]
            else:
                break
        except ValueError:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                break
    return value


def _find_in_tracking_data(tracking_data: dict, parts: list) -> Dict[str, Any] | None:
    """Search tracked outputs for a variable path. Returns result dict or None."""
    for node_id, ports in tracking_data["tracked_outputs"].items():
        for port_id, tracked in ports.items():
            value = tracked.get("value")
            sub_parts = parts[1:] if parts else []
            current, current_tracked, found = _navigate_path(value, tracked, sub_parts)
            if not found or current is None:
                continue

            origin_data = current_tracked.get("origin", tracked.get("origin", {}))
            return {
                "origin": {
                    "node_id": origin_data.get("node_id", node_id),
                    "port_id": origin_data.get("port_id", port_id),
                    "key_path": origin_data.get("key_path"),
                    "timestamp": origin_data.get("timestamp"),
                },
                "transform_chain": current_tracked.get(
                    "transform_chain",
                    tracked.get("transform_chain", []),
                ),
                "current_value": get_value_preview(current),
                "value_type": type(current).__name__,
            }
    return None


def _find_in_evidence(steps: list, parts: list) -> Dict[str, Any] | None:
    """Search evidence steps for a variable path. Returns result dict or None."""
    for step in reversed(steps):
        after = step.get('context_after', {})
        if not parts or parts[0] not in after:
            continue

        value = _navigate_value(after[parts[0]], parts[1:])
        return {
            "origin": {
                "node_id": step.get('step_id'),
                "port_id": "default",
            },
            "transform_chain": [step.get('step_id')],
            "current_value": get_value_preview(value),
            "value_type": type(value).__name__,
        }
    return None


@router.get("/executions/{execution_id}/trace/{variable_path}")
async def trace_variable_origin(
    execution_id: str,
    variable_path: str,
) -> Dict[str, Any]:
    """
    Trace the origin of a specific variable or path.

    The variable_path can be:
    - A simple variable name: "user"
    - A nested path: "user.address.city"
    - An array index: "items[0]"
    - Combined: "users[0].name"

    Returns the full lineage chain showing how the value was produced.
    """
    parts = _parse_variable_path(variable_path)

    result = {
        "variable_path": variable_path,
        "origin": None,
        "transform_chain": [],
        "intermediate_steps": [],
    }

    tracking_data = load_tracking_data(execution_id)
    if tracking_data and "tracked_outputs" in tracking_data:
        found = _find_in_tracking_data(tracking_data, parts)
        if found:
            result.update(found)
            return result

    steps = load_execution_evidence(execution_id)
    found = _find_in_evidence(steps, parts)
    if found:
        result.update(found)
        return result

    return result
