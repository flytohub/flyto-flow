"""
Testing Path Utilities

Path resolution for workflows, tests, and snapshots directories.
"""

import os
from pathlib import Path


# Default directories
WORKFLOWS_PATH = Path("./workflows")
TESTS_PATH = Path("./tests")
SNAPSHOTS_PATH = Path("./snapshots")


def get_workflows_path() -> Path:
    """Get workflows base path"""
    custom_path = os.getenv("FLYTO_WORKFLOWS_PATH")
    if custom_path:
        return Path(custom_path)
    return WORKFLOWS_PATH


def get_tests_path() -> Path:
    """Get tests base path"""
    custom_path = os.getenv("FLYTO_TESTS_PATH")
    if custom_path:
        return Path(custom_path)

    # Find tests directory relative to this file (in backend/)
    current = Path(__file__).resolve().parent.parent.parent  # -> backend/
    tests_dir = current / "tests"
    if tests_dir.exists():
        return tests_dir

    return TESTS_PATH


def get_snapshots_path() -> Path:
    """Get snapshots base path"""
    custom_path = os.getenv("FLYTO_SNAPSHOTS_PATH")
    if custom_path:
        return Path(custom_path)

    # Find snapshots directory relative to this file (in backend/)
    current = Path(__file__).resolve().parent.parent.parent  # -> backend/
    snapshots_dir = current / "snapshots"
    if snapshots_dir.exists():
        return snapshots_dir

    return SNAPSHOTS_PATH
