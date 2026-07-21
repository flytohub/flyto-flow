"""
Testing API Models

Pydantic models for test definitions, results, and responses.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class TestDefinition(BaseModel):
    """Test definition from YAML"""
    name: str
    description: Optional[str] = None
    tags: List[str] = []
    inputs: Dict[str, Any] = {}
    expected_outputs: Dict[str, Any] = {}
    assertions: List[Dict[str, Any]] = []
    timeout_seconds: int = 60


class TestResult(BaseModel):
    """Single test result"""
    test_name: str
    passed: bool
    duration_ms: int
    error: Optional[str] = None
    assertions_passed: int = 0
    assertions_failed: int = 0
    assertion_details: List[Dict[str, Any]] = []
    actual_outputs: Dict[str, Any] = {}
    expected_outputs: Dict[str, Any] = {}


class TestRunResponse(BaseModel):
    """Test run response"""
    test_run_id: str
    workflow_id: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    started_at: str
    completed_at: Optional[str] = None
    results: List[TestResult] = []
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    all_passed: bool = False


class SnapshotInfo(BaseModel):
    """Snapshot information"""
    name: str
    workflow_id: str
    created_at: str
    updated_at: str
    size_bytes: int


class RunTestsRequest(BaseModel):
    """Request body for running tests"""
    test_names: List[str] = []


class RunTestsByTagsRequest(BaseModel):
    """Request body for running tests by tags"""
    tags: List[str] = []
