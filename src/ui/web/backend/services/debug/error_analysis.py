"""
Debug Error Analysis

Error analysis and fix suggestions for failed executions.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def get_fix_suggestions(error_category: str) -> List[str]:
    """Get fix suggestions based on error category."""
    suggestions = {
        "timeout": [
            "Increase timeout configuration for this step",
            "Check if target service is responding slowly",
            "Consider adding retry with longer delays",
        ],
        "network_error": [
            "Verify network connectivity",
            "Check if target URL is correct",
            "Add retry logic for transient failures",
        ],
        "rate_limit": [
            "Add delay between requests",
            "Implement exponential backoff",
            "Check API rate limit quotas",
        ],
        "auth_error": [
            "Verify credentials are correct",
            "Check if token has expired",
            "Ensure proper permissions are granted",
        ],
        "validation_error": [
            "Check input parameters format",
            "Verify required fields are provided",
            "Review data types and constraints",
        ],
        "resource_not_found": [
            "Verify resource ID/path is correct",
            "Check if resource was deleted",
            "Ensure proper access permissions",
        ],
    }

    return suggestions.get(error_category, [
        "Review error message for details",
        "Check logs for more context",
        "Consider rerunning with debug logging",
    ])


async def get_error_analysis(execution_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed error analysis for a failed execution.

    Args:
        execution_id: Execution to analyze

    Returns:
        Error analysis or None
    """
    from gateway.storage.execution_repo import ExecutionRepository

    execution = ExecutionRepository.get_execution(
        execution_id,
        include_steps=True,
    )

    if not execution:
        return None

    if execution.status not in ("failure", "failed"):
        return {
            "execution_id": execution_id,
            "status": execution.status,
            "has_error": False,
        }

    # Find failed step
    failed_step = None
    if execution.steps:
        for step in execution.steps:
            if step.status in ("failure", "failed"):
                failed_step = step
                break

    analysis = {
        "execution_id": execution_id,
        "status": execution.status,
        "has_error": True,
        "error_message": execution.error_message,
        "error_category": execution.error_category,
        "error_fingerprint": execution.error_fingerprint,
    }

    if failed_step:
        analysis["failed_step"] = {
            "step_id": failed_step.step_id,
            "step_index": failed_step.step_index,
            "module_id": failed_step.module_id,
            "error": failed_step.error_message,
            "inputs": failed_step.input_params,
            "started_at": failed_step.started_at,
            "finished_at": failed_step.finished_at,
        }

        # Suggest fix based on error category
        if execution.error_category:
            analysis["suggestions"] = get_fix_suggestions(execution.error_category)

    return analysis
