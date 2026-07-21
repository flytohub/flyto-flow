"""
Testing API - Workflow test framework

This package provides workflow testing capabilities:
- Test definition and execution
- Snapshot testing
- Coverage analysis
"""

from fastapi import APIRouter

from api.testing.routes_tests import router as tests_router
from api.testing.routes_snapshots import router as snapshots_router
from api.testing.routes_coverage import router as coverage_router

# DEPRECATED: Not used by frontend. Retained for potential future use.
# Combined router
router = APIRouter()
router.include_router(tests_router)
router.include_router(snapshots_router)
router.include_router(coverage_router)

# Re-export models for convenience
from api.testing.models import (
    TestDefinition,
    TestResult,
    TestRunResponse,
    SnapshotInfo,
    RunTestsRequest,
    RunTestsByTagsRequest,
)

__all__ = [
    'router',
    'TestDefinition',
    'TestResult',
    'TestRunResponse',
    'SnapshotInfo',
    'RunTestsRequest',
    'RunTestsByTagsRequest',
]
