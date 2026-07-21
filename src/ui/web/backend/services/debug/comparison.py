"""
Debug Comparison

Compare executions for debugging.
"""

import logging
from typing import Any, Dict

from services.debug.timeline import get_timeline

logger = logging.getLogger(__name__)


async def compare_executions(
    exec_id_1: str,
    exec_id_2: str,
) -> Dict[str, Any]:
    """
    Compare two executions.

    Args:
        exec_id_1: First execution ID
        exec_id_2: Second execution ID

    Returns:
        Comparison result
    """
    timeline_1 = await get_timeline(exec_id_1)
    timeline_2 = await get_timeline(exec_id_2)

    if not timeline_1 or not timeline_2:
        return {
            "error": "One or both executions not found",
            "found_1": timeline_1 is not None,
            "found_2": timeline_2 is not None,
        }

    # Compare basic info
    comparison = {
        "execution_1": {
            "id": exec_id_1,
            "status": timeline_1.status,
            "duration_ms": timeline_1.duration_ms,
            "total_steps": timeline_1.total_steps,
            "completed_steps": timeline_1.completed_steps,
        },
        "execution_2": {
            "id": exec_id_2,
            "status": timeline_2.status,
            "duration_ms": timeline_2.duration_ms,
            "total_steps": timeline_2.total_steps,
            "completed_steps": timeline_2.completed_steps,
        },
        "differences": [],
    }

    # Compare step by step
    steps_1 = {e.node_id: e for e in timeline_1.events if e.event_type != "started"}
    steps_2 = {e.node_id: e for e in timeline_2.events if e.event_type != "started"}

    all_nodes = set(steps_1.keys()) | set(steps_2.keys())

    for node_id in sorted(all_nodes):
        step_1 = steps_1.get(node_id)
        step_2 = steps_2.get(node_id)

        if step_1 and step_2:
            if step_1.event_type != step_2.event_type:
                comparison["differences"].append({
                    "node_id": node_id,
                    "type": "status_changed",
                    "exec_1": step_1.event_type,
                    "exec_2": step_2.event_type,
                })

            if step_1.duration_ms and step_2.duration_ms:
                diff_pct = abs(step_1.duration_ms - step_2.duration_ms) / max(
                    step_1.duration_ms, 1
                ) * 100
                if diff_pct > 50:  # >50% difference
                    comparison["differences"].append({
                        "node_id": node_id,
                        "type": "duration_changed",
                        "exec_1_ms": step_1.duration_ms,
                        "exec_2_ms": step_2.duration_ms,
                        "diff_pct": round(diff_pct, 1),
                    })

        elif step_1:
            comparison["differences"].append({
                "node_id": node_id,
                "type": "missing_in_exec_2",
            })
        else:
            comparison["differences"].append({
                "node_id": node_id,
                "type": "missing_in_exec_1",
            })

    return comparison
