"""
Testing Routes - Test Run Endpoints

Run and list tests for workflows.
"""

import logging
import uuid
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from api.testing.models import RunTestsRequest, RunTestsByTagsRequest
from api.testing.loader import load_tests_from_yaml
from api.testing.execution import (
    execute_test_run,
    get_test_run,
    create_test_run,
    get_workflow_runs,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/workflows/{workflow_id}/tests")
async def list_tests(
    workflow_id: str,
) -> Dict[str, Any]:
    """
    List all tests for a workflow.

    Tests are loaded from the workflow's tests.yaml file.
    """
    tests = load_tests_from_yaml(workflow_id)

    return {
        "workflow_id": workflow_id,
        "tests": [t.dict() for t in tests],
        "test_count": len(tests),
    }


@router.post("/workflows/{workflow_id}/run")
async def run_tests(
    workflow_id: str,
    background_tasks: BackgroundTasks,
    request: RunTestsRequest = RunTestsRequest(),
) -> Dict[str, Any]:
    """
    Run tests for a workflow.

    If test_names is empty, runs all tests.
    Returns immediately with a test_run_id for polling.
    """
    tests = load_tests_from_yaml(workflow_id)

    if not tests:
        return {
            "ok": False,
            "error": "No tests found for workflow",
        }

    # Filter tests if specific names provided
    test_names = request.test_names
    if test_names:
        tests = [t for t in tests if t.name in test_names]

    if not tests:
        return {
            "ok": False,
            "error": "No matching tests found",
        }

    # Create test run
    test_run_id = str(uuid.uuid4())
    create_test_run(test_run_id, workflow_id, len(tests))

    # Run tests in background
    background_tasks.add_task(execute_test_run, test_run_id, workflow_id, tests)

    return {
        "ok": True,
        "test_run_id": test_run_id,
        "test_count": len(tests),
    }


@router.post("/workflows/{workflow_id}/run-by-tags")
async def run_tests_by_tags(
    workflow_id: str,
    background_tasks: BackgroundTasks,
    request: RunTestsByTagsRequest = RunTestsByTagsRequest(),
) -> Dict[str, Any]:
    """
    Run tests matching specified tags.
    """
    tests = load_tests_from_yaml(workflow_id)

    if not tests:
        return {
            "ok": False,
            "error": "No tests found for workflow",
        }

    # Filter by tags
    tags = request.tags
    if tags:
        tests = [t for t in tests if any(tag in t.tags for tag in tags)]

    if not tests:
        return {
            "ok": False,
            "error": "No tests matching tags found",
        }

    # Create test run
    test_run_id = str(uuid.uuid4())
    create_test_run(test_run_id, workflow_id, len(tests))

    background_tasks.add_task(execute_test_run, test_run_id, workflow_id, tests)

    return {
        "ok": True,
        "test_run_id": test_run_id,
        "test_count": len(tests),
    }


@router.get("/results/{test_run_id}")
async def get_test_result(
    test_run_id: str,
) -> Dict[str, Any]:
    """
    Get results of a test run.

    Poll this endpoint until status is 'completed' or 'failed'.
    """
    run = get_test_run(test_run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    return run


@router.get("/workflows/{workflow_id}/report")
async def get_test_report(
    workflow_id: str,
    limit: int = Query(default=10, le=50),
) -> Dict[str, Any]:
    """
    Get test report for a workflow.

    Shows recent test runs and overall stats.
    """
    # Filter runs for this workflow
    workflow_runs = get_workflow_runs(workflow_id)

    # Sort by completion time
    workflow_runs.sort(key=lambda x: x.get("completed_at", ""), reverse=True)
    recent_runs = workflow_runs[:limit]

    # Calculate stats
    total_runs = len(workflow_runs)
    passed_runs = sum(1 for r in workflow_runs if r.get("all_passed", False))

    return {
        "workflow_id": workflow_id,
        "total_runs": total_runs,
        "passed_runs": passed_runs,
        "failed_runs": total_runs - passed_runs,
        "pass_rate": (passed_runs / total_runs * 100) if total_runs > 0 else 0,
        "recent_runs": recent_runs,
    }
