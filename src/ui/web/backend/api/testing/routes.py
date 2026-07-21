"""
Testing API Routes

DEPRECATED: This file is maintained for backwards compatibility.
Please import from api.testing instead:

    from api.testing import router

All functionality has been split into:
- api/testing/models.py - Pydantic models
- api/testing/paths.py - Path utilities
- api/testing/assertions.py - Assertion evaluation
- api/testing/loader.py - Test loading from YAML
- api/testing/execution.py - Test execution logic
- api/testing/routes_tests.py - Test run endpoints
- api/testing/routes_snapshots.py - Snapshot endpoints
- api/testing/routes_coverage.py - Coverage endpoints
"""

# Re-export router for backwards compatibility
from api.testing import router

# Re-export models for backwards compatibility
from api.testing.models import (
    TestDefinition,
    TestResult,
    TestRunResponse,
    SnapshotInfo,
    RunTestsRequest,
    RunTestsByTagsRequest,
)

__all__ = [
    "router",
    "TestDefinition",
    "TestResult",
    "TestRunResponse",
    "SnapshotInfo",
    "RunTestsRequest",
    "RunTestsByTagsRequest",
]
