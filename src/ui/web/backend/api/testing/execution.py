"""
Testing Execution

Test execution logic including running single tests and test batches.
"""

import asyncio
import logging
import time
import random
from datetime import datetime, timezone
from typing import Any, Dict, List

from api.testing.models import TestDefinition, TestResult
from api.testing.assertions import evaluate_assertion

logger = logging.getLogger(__name__)

# In-memory test run storage (would be database in production)
test_runs: Dict[str, Dict[str, Any]] = {}


async def run_single_test(
    workflow_id: str,
    test: TestDefinition,
) -> TestResult:
    """
    Run a single test.

    Args:
        workflow_id: The workflow being tested
        test: Test definition to run

    Returns:
        TestResult with pass/fail status and details
    """
    start_time = time.time()

    try:
        # Simulate execution time (50-200ms)
        await asyncio.sleep(random.uniform(0.05, 0.2))

        # Build simulated outputs based on test inputs and expected patterns
        # In production, this would call ExecutionManager to run the actual workflow
        actual_outputs = test.inputs.copy()

        # Simulate successful execution results
        actual_outputs["result"] = {
            "ok": True,
            "data": test.inputs,
        }
        actual_outputs["status"] = "success"
        actual_outputs["duration_ms"] = int((time.time() - start_time) * 1000)

        # Simulate browser-specific outputs
        if test.inputs.get("url"):
            actual_outputs["result"]["url"] = test.inputs["url"]

        # Simulate loop outputs
        if test.inputs.get("times"):
            actual_outputs["result"]["iterations"] = test.inputs["times"]

        # Evaluate assertions
        assertion_details = []
        assertions_passed = 0
        assertions_failed = 0

        for assertion in test.assertions:
            result = evaluate_assertion(assertion, actual_outputs)
            assertion_details.append(result)
            if result["passed"]:
                assertions_passed += 1
            else:
                assertions_failed += 1

        # Check expected outputs if no explicit assertions
        if not test.assertions and test.expected_outputs:
            for key, expected in test.expected_outputs.items():
                actual = actual_outputs.get(key)
                passed = actual == expected
                assertion_details.append({
                    "field": key,
                    "type": "equals",
                    "expected": expected,
                    "actual": actual,
                    "passed": passed,
                    "message": "" if passed else f"Expected {expected}, got {actual}",
                })
                if passed:
                    assertions_passed += 1
                else:
                    assertions_failed += 1

        duration_ms = int((time.time() - start_time) * 1000)

        return TestResult(
            test_name=test.name,
            passed=assertions_failed == 0,
            duration_ms=duration_ms,
            assertions_passed=assertions_passed,
            assertions_failed=assertions_failed,
            assertion_details=assertion_details,
            actual_outputs=actual_outputs,
            expected_outputs=test.expected_outputs,
        )

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return TestResult(
            test_name=test.name,
            passed=False,
            duration_ms=duration_ms,
            error=str(e),
        )


async def execute_test_run(
    test_run_id: str,
    workflow_id: str,
    tests: List[TestDefinition]
):
    """
    Execute tests in background.

    Args:
        test_run_id: Unique ID for this test run
        workflow_id: Workflow being tested
        tests: List of tests to run
    """
    test_runs[test_run_id]["status"] = "running"

    results = []
    for test in tests:
        result = await run_single_test(workflow_id, test)
        results.append(result)

    passed_count = sum(1 for r in results if r.passed)

    test_runs[test_run_id].update({
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "results": [r.dict() for r in results],
        "total_tests": len(results),
        "passed_tests": passed_count,
        "failed_tests": len(results) - passed_count,
        "all_passed": passed_count == len(results),
    })


def get_test_run(test_run_id: str) -> Dict[str, Any]:
    """Get a test run by ID"""
    return test_runs.get(test_run_id)


def create_test_run(
    test_run_id: str,
    workflow_id: str,
    test_count: int
) -> Dict[str, Any]:
    """Create a new test run record"""
    test_runs[test_run_id] = {
        "test_run_id": test_run_id,
        "workflow_id": workflow_id,
        "status": "pending",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "results": [],
        "total_tests": test_count,
        "passed_tests": 0,
        "failed_tests": 0,
        "all_passed": False,
    }
    return test_runs[test_run_id]


def get_workflow_runs(workflow_id: str) -> List[Dict[str, Any]]:
    """Get all completed test runs for a workflow"""
    return [
        run for run in test_runs.values()
        if run["workflow_id"] == workflow_id and run["status"] == "completed"
    ]
