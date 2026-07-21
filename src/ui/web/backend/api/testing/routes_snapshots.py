"""
Testing Routes - Snapshot Endpoints

Snapshot testing for workflow outputs.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from api.testing.models import SnapshotInfo
from api.testing.paths import get_snapshots_path

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/workflows/{workflow_id}/snapshots")
async def list_snapshots(
    workflow_id: str,
) -> Dict[str, Any]:
    """
    List all snapshots for a workflow.
    """
    snapshots_path = get_snapshots_path() / workflow_id

    if not snapshots_path.exists():
        return {
            "workflow_id": workflow_id,
            "snapshots": [],
        }

    snapshots = []
    for snapshot_file in snapshots_path.glob("*.json"):
        try:
            stat = snapshot_file.stat()
            snapshots.append(SnapshotInfo(
                name=snapshot_file.stem,
                workflow_id=workflow_id,
                created_at=datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
                updated_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                size_bytes=stat.st_size,
            ))
        except Exception:
            continue

    return {
        "workflow_id": workflow_id,
        "snapshots": [s.dict() for s in snapshots],
    }


def find_differences(expected: Any, actual: Any, path: str = "") -> list:
    """
    Find differences between expected and actual values.

    Args:
        expected: Expected value from snapshot
        actual: Actual value to compare
        path: Current path in the object tree

    Returns:
        List of difference dicts
    """
    differences = []

    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in set(expected.keys()) | set(actual.keys()):
            new_path = f"{path}.{key}" if path else key
            if key not in expected:
                differences.append({
                    "path": new_path,
                    "type": "added",
                    "actual": actual[key],
                })
            elif key not in actual:
                differences.append({
                    "path": new_path,
                    "type": "removed",
                    "expected": expected[key],
                })
            else:
                differences.extend(find_differences(expected[key], actual[key], new_path))
    elif isinstance(expected, list) and isinstance(actual, list):
        for i, (e, a) in enumerate(zip(expected, actual)):
            differences.extend(find_differences(e, a, f"{path}[{i}]"))
        if len(expected) != len(actual):
            differences.append({
                "path": f"{path}.length",
                "type": "changed",
                "expected": len(expected),
                "actual": len(actual),
            })
    elif expected != actual:
        differences.append({
            "path": path or "root",
            "type": "changed",
            "expected": expected,
            "actual": actual,
        })

    return differences


@router.post("/workflows/{workflow_id}/snapshots/{snapshot_name}/match")
async def match_snapshot(
    workflow_id: str,
    snapshot_name: str,
    actual: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Match actual data against a saved snapshot.

    Returns match result and differences.
    """
    snapshots_path = get_snapshots_path() / workflow_id
    snapshot_file = snapshots_path / f"{snapshot_name}.json"

    if not snapshot_file.exists():
        return {
            "matched": False,
            "error": "Snapshot not found",
            "snapshot_name": snapshot_name,
        }

    try:
        with open(snapshot_file, 'r', encoding='utf-8') as f:
            expected = json.load(f)

        # Deep comparison
        matched = expected == actual

        # Calculate differences
        differences = []
        if not matched:
            differences = find_differences(expected, actual)

        return {
            "matched": matched,
            "snapshot_name": snapshot_name,
            "differences": differences,
        }

    except Exception as e:
        logger.error(f"Failed to match snapshot {snapshot_name}: {e}", exc_info=True)
        return {
            "matched": False,
            "error": "Failed to match snapshot",
            "snapshot_name": snapshot_name,
        }


@router.post("/workflows/{workflow_id}/snapshots/{snapshot_name}/update")
async def update_snapshot(
    workflow_id: str,
    snapshot_name: str,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Update or create a snapshot.
    """
    snapshots_path = get_snapshots_path() / workflow_id
    snapshots_path.mkdir(parents=True, exist_ok=True)

    snapshot_file = snapshots_path / f"{snapshot_name}.json"

    try:
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return {
            "ok": True,
            "snapshot_name": snapshot_name,
            "created": not snapshot_file.exists(),
        }

    except Exception as e:
        logger.error(f"Failed to save snapshot {snapshot_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save snapshot")


@router.delete("/workflows/{workflow_id}/snapshots/{snapshot_name}")
async def delete_snapshot(
    workflow_id: str,
    snapshot_name: str,
) -> Dict[str, Any]:
    """
    Delete a snapshot.
    """
    snapshots_path = get_snapshots_path() / workflow_id
    snapshot_file = snapshots_path / f"{snapshot_name}.json"

    if not snapshot_file.exists():
        raise HTTPException(status_code=404, detail="Snapshot not found")

    try:
        snapshot_file.unlink()
        return {
            "ok": True,
            "deleted": snapshot_name,
        }
    except Exception as e:
        logger.error(f"Failed to delete snapshot {snapshot_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete snapshot")
