"""
Testing Loader

Load test definitions from YAML files.
"""

import logging
from typing import List

from api.testing.models import TestDefinition
from api.testing.paths import get_tests_path, get_workflows_path

logger = logging.getLogger(__name__)


def load_tests_from_yaml(workflow_id: str) -> List[TestDefinition]:
    """
    Load test definitions from YAML file.

    Args:
        workflow_id: Workflow ID to load tests for

    Returns:
        List of TestDefinition objects

    Looks for tests in:
    1. {tests_path}/{workflow_id}/tests.yaml
    2. {workflows_path}/{workflow_id}/tests.yaml
    """
    import yaml

    tests_path = get_tests_path()
    test_file = tests_path / workflow_id / "tests.yaml"

    if not test_file.exists():
        # Also try workflow directory
        workflows_path = get_workflows_path()
        test_file = workflows_path / workflow_id / "tests.yaml"

    if not test_file.exists():
        return []

    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data or 'tests' not in data:
            return []

        tests = []
        for test_data in data['tests']:
            tests.append(TestDefinition(
                name=test_data.get('name', 'unnamed'),
                description=test_data.get('description'),
                tags=test_data.get('tags', []),
                inputs=test_data.get('inputs', {}),
                expected_outputs=test_data.get('expected_outputs', {}),
                assertions=test_data.get('assertions', []),
                timeout_seconds=test_data.get('timeout_seconds', 60),
            ))

        return tests

    except Exception as e:
        logger.error(f"Failed to load tests for {workflow_id}: {e}")
        return []
