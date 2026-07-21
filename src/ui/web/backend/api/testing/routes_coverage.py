"""
Testing Routes - Coverage Endpoints

Test coverage analysis for workflows.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter

from api.testing.loader import load_tests_from_yaml
from api.testing.paths import get_workflows_path

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/workflows/{workflow_id}/coverage")
async def get_test_coverage(
    workflow_id: str,
) -> Dict[str, Any]:
    """
    Get test coverage for a workflow.

    Analyzes which workflow steps are covered by tests.

    Note: This is a basic implementation. Full coverage analysis
    would require tracking actual step executions during test runs.
    """
    import yaml

    # Load tests
    tests = load_tests_from_yaml(workflow_id)

    # Try to load workflow to get steps
    workflow_steps = []
    workflows_path = get_workflows_path()
    workflow_file = workflows_path / workflow_id / "workflow.yaml"

    if workflow_file.exists():
        try:
            with open(workflow_file, 'r', encoding='utf-8') as f:
                workflow_data = yaml.safe_load(f)
                workflow_steps = workflow_data.get('steps', [])
        except Exception:
            pass

    total_steps = len(workflow_steps)
    total_tests = len(tests)

    # Basic coverage estimate based on test count
    # In a real implementation, this would track actual step execution during tests
    if total_steps == 0:
        coverage_percent = 0
    elif total_tests == 0:
        coverage_percent = 0
    else:
        # Estimate: each test covers ~1-3 steps on average
        estimated_covered = min(total_steps, total_tests * 2)
        coverage_percent = round((estimated_covered / total_steps) * 100, 1)

    # Get step IDs for reporting
    step_ids = [step.get('id', f'step_{i}') for i, step in enumerate(workflow_steps)]

    return {
        "workflow_id": workflow_id,
        "total_steps": total_steps,
        "total_tests": total_tests,
        "coverage_percent": coverage_percent,
        "step_ids": step_ids,
        "covered_steps": step_ids[:len(tests) * 2] if tests else [],
        "uncovered_steps": step_ids[len(tests) * 2:] if len(tests) * 2 < total_steps else [],
        "note": "Coverage is estimated. Actual step-level coverage tracking requires test execution instrumentation.",
    }
