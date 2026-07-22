"""
Evidence API Routes

Provides REST endpoints for accessing workflow execution evidence:
- List executions with evidence
- Get evidence for a specific execution
- Get screenshot/DOM for a specific step
- Delete evidence

This is a capability n8n lacks - full execution evidence with visual debugging.
"""
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from capabilities import Feature, require_feature
from local.storage_paths import evidence_path

logger = logging.getLogger(__name__)

_SAFE_EVIDENCE_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")

# DEPRECATED: Not used by frontend. Retained for potential future use.
router = APIRouter(
    dependencies=[
        Depends(require_feature(Feature.EVIDENCE_VIEW)),
    ],
)

def get_evidence_path() -> Path:
    """Get the local evidence directory."""
    return evidence_path()


def _validate_evidence_component(value: object, label: str) -> str:
    """Allow only one opaque evidence directory/file component."""
    if not isinstance(value, str) or not _SAFE_EVIDENCE_COMPONENT.fullmatch(value):
        raise HTTPException(status_code=400, detail=f"Invalid {label}")
    return value


def _find_child(parent: Path, expected_name: str) -> Path | None:
    """Return a contained filesystem entry selected from an allowed directory."""
    try:
        for candidate in parent.iterdir():
            if candidate.name != expected_name:
                continue
            resolved = candidate.resolve()
            resolved.relative_to(parent.resolve())
            return resolved
    except (OSError, ValueError):
        return None
    return None


def _get_execution_dir(evidence_path: Path, execution_id: str) -> tuple[Path, str]:
    """Resolve an execution directory without allowing traversal or symlink escape."""
    safe_execution_id = _validate_evidence_component(execution_id, "execution id")
    evidence_root = evidence_path.resolve()
    execution_dir = _find_child(evidence_root, safe_execution_id)
    if execution_dir is None or not execution_dir.is_dir():
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution_dir, safe_execution_id


# =============================================================================
# Response Models
# =============================================================================

class StepEvidenceResponse(BaseModel):
    """Single step evidence response"""
    step_id: str
    execution_id: str
    timestamp: str
    duration_ms: int
    status: str
    module_id: Optional[str] = None
    step_index: Optional[int] = None
    error_message: Optional[str] = None
    has_screenshot: bool = False
    has_dom_snapshot: bool = False
    screenshot_url: Optional[str] = None
    dom_url: Optional[str] = None


class ExecutionEvidenceResponse(BaseModel):
    """Execution evidence response"""
    execution_id: str
    step_count: int
    steps: List[StepEvidenceResponse]
    total_duration_ms: int = 0
    success_count: int = 0
    error_count: int = 0


class ExecutionListItem(BaseModel):
    """Execution list item"""
    execution_id: str
    step_count: int
    total_duration_ms: int
    has_errors: bool
    first_step_timestamp: Optional[str] = None


# =============================================================================
# API Endpoints
# =============================================================================

@router.get("/")
async def list_executions(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    """
    List all executions with evidence.

    Returns a paginated list of execution IDs with summary info.
    """
    evidence_path = get_evidence_path()

    if not evidence_path.exists():
        return {
            "executions": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
        }

    # Get all execution directories
    executions = []
    evidence_root = evidence_path.resolve()
    for entry in evidence_root.iterdir():
        if not entry.is_dir():
            continue
        try:
            exec_dir = entry.resolve()
            exec_dir.relative_to(evidence_root)
        except (OSError, ValueError):
            continue

        jsonl_path = _find_child(exec_dir, "evidence.jsonl")
        if jsonl_path is None or not jsonl_path.is_file():
            continue

        # Read evidence summary
        try:
            step_count = 0
            total_duration = 0
            has_errors = False
            first_timestamp = None

            with open(jsonl_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        step_count += 1
                        total_duration += data.get('duration_ms', 0)
                        if data.get('status') == 'error':
                            has_errors = True
                        if first_timestamp is None:
                            first_timestamp = data.get('timestamp')
                    except json.JSONDecodeError:
                        continue

            executions.append(ExecutionListItem(
                execution_id=exec_dir.name,
                step_count=step_count,
                total_duration_ms=total_duration,
                has_errors=has_errors,
                first_step_timestamp=first_timestamp,
            ))

        except Exception as e:
            logger.warning(f"Failed to read evidence for {exec_dir.name}: {e}")
            continue

    # Sort by timestamp (most recent first)
    executions.sort(
        key=lambda x: x.first_step_timestamp or "",
        reverse=True
    )

    # Apply pagination
    total = len(executions)
    paginated = executions[offset:offset + limit]

    return {
        "executions": [e.dict() for e in paginated],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{execution_id}")
async def get_execution_evidence(
    execution_id: str,
    include_context: bool = Query(default=False),
) -> ExecutionEvidenceResponse:
    """
    Get all evidence for a specific execution.

    Args:
        execution_id: Execution ID
        include_context: Whether to include full context snapshots (large)

    Returns:
        Full evidence for the execution
    """
    evidence_path = get_evidence_path()
    exec_dir, safe_execution_id = _get_execution_dir(evidence_path, execution_id)

    if not exec_dir.exists():
        raise HTTPException(status_code=404, detail="Execution not found")

    jsonl_path = _find_child(exec_dir, "evidence.jsonl")
    if jsonl_path is None or not jsonl_path.is_file():
        raise HTTPException(status_code=404, detail="No evidence found for execution")

    steps = []
    total_duration = 0
    success_count = 0
    error_count = 0

    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)

                    step_id = _validate_evidence_component(
                        data.get('step_id', 'unknown'), "step id"
                    )

                    # Check for screenshot/DOM files
                    has_screenshot = _find_child(exec_dir, f"{step_id}.png") is not None
                    has_dom = _find_child(exec_dir, f"{step_id}.html") is not None

                    step = StepEvidenceResponse(
                        step_id=step_id,
                        execution_id=safe_execution_id,
                        timestamp=data.get('timestamp', ''),
                        duration_ms=data.get('duration_ms', 0),
                        status=data.get('status', 'unknown'),
                        module_id=data.get('module_id'),
                        step_index=data.get('step_index'),
                        error_message=data.get('error_message'),
                        has_screenshot=has_screenshot,
                        has_dom_snapshot=has_dom,
                        screenshot_url=f"/api/evidence/{safe_execution_id}/steps/{step_id}/screenshot" if has_screenshot else None,
                        dom_url=f"/api/evidence/{safe_execution_id}/steps/{step_id}/dom" if has_dom else None,
                    )

                    steps.append(step)
                    total_duration += data.get('duration_ms', 0)

                    if data.get('status') == 'error':
                        error_count += 1
                    else:
                        success_count += 1

                except (HTTPException, json.JSONDecodeError):
                    logger.warning("Skipping malformed evidence record")
                    continue

    except Exception as e:
        logger.exception("Failed to read evidence")
        raise HTTPException(status_code=500, detail="Failed to read evidence") from e

    return ExecutionEvidenceResponse(
        execution_id=safe_execution_id,
        step_count=len(steps),
        steps=steps,
        total_duration_ms=total_duration,
        success_count=success_count,
        error_count=error_count,
    )


@router.get("/{execution_id}/steps/{step_id}")
async def get_step_evidence(
    execution_id: str,
    step_id: str,
    include_context: bool = Query(default=True),
) -> Dict[str, Any]:
    """
    Get detailed evidence for a specific step.

    Includes full context before/after if requested.
    """
    evidence_path = get_evidence_path()
    exec_dir, safe_execution_id = _get_execution_dir(evidence_path, execution_id)
    safe_step_id = _validate_evidence_component(step_id, "step id")
    jsonl_path = _find_child(exec_dir, "evidence.jsonl")

    if jsonl_path is None or not jsonl_path.is_file():
        raise HTTPException(status_code=404, detail="Execution not found")

    # Find the specific step
    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    if data.get('step_id') == safe_step_id:
                        # Remove context if not requested
                        if not include_context:
                            data.pop('context_before', None)
                            data.pop('context_after', None)

                        # Add file availability info
                        data['has_screenshot'] = _find_child(exec_dir, f"{safe_step_id}.png") is not None
                        data['has_dom_snapshot'] = _find_child(exec_dir, f"{safe_step_id}.html") is not None

                        return data

                except json.JSONDecodeError:
                    continue

    except Exception as e:
        logger.exception("Failed to read step evidence")
        raise HTTPException(status_code=500, detail="Failed to read evidence") from e

    raise HTTPException(status_code=404, detail="Step not found")


@router.get("/{execution_id}/steps/{step_id}/screenshot")
async def get_step_screenshot(
    execution_id: str,
    step_id: str,
) -> FileResponse:
    """
    Get screenshot for a specific step.

    Returns PNG image.
    """
    evidence_path = get_evidence_path()
    exec_dir, safe_execution_id = _get_execution_dir(evidence_path, execution_id)
    safe_step_id = _validate_evidence_component(step_id, "step id")
    screenshot_path = _find_child(exec_dir, f"{safe_step_id}.png")

    if screenshot_path is None or not screenshot_path.is_file():
        raise HTTPException(status_code=404, detail="Screenshot not found")

    return FileResponse(
        path=screenshot_path,
        media_type="image/png",
        filename=f"{safe_execution_id}_{safe_step_id}.png",
    )


@router.get("/{execution_id}/steps/{step_id}/dom")
async def get_step_dom(
    execution_id: str,
    step_id: str,
) -> HTMLResponse:
    """
    Get DOM snapshot for a specific step.

    Returns HTML content.
    """
    evidence_path = get_evidence_path()
    exec_dir, _ = _get_execution_dir(evidence_path, execution_id)
    safe_step_id = _validate_evidence_component(step_id, "step id")
    dom_path = _find_child(exec_dir, f"{safe_step_id}.html")

    if dom_path is None or not dom_path.is_file():
        raise HTTPException(status_code=404, detail="DOM snapshot not found")

    try:
        with open(dom_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HTMLResponse(content=content)
    except Exception as e:
        logger.exception("Failed to read DOM evidence")
        raise HTTPException(status_code=500, detail="Failed to read DOM evidence") from e


@router.delete("/{execution_id}")
async def delete_execution_evidence(
    execution_id: str,
) -> Dict[str, Any]:
    """
    Delete all evidence for an execution.

    This permanently removes all screenshots, DOM snapshots, and metadata.
    """
    import shutil

    evidence_path = get_evidence_path()
    exec_dir, safe_execution_id = _get_execution_dir(evidence_path, execution_id)

    if not exec_dir.exists():
        raise HTTPException(status_code=404, detail="Execution not found")

    try:
        shutil.rmtree(exec_dir)
        return {
            "ok": True,
            "message": "Evidence deleted",
        }
    except Exception as e:
        logger.exception("Failed to delete evidence")
        raise HTTPException(status_code=500, detail="Failed to delete evidence") from e


@router.get("/{execution_id}/context-diff")
async def get_context_diff(
    execution_id: str,
    step_id: str,
) -> Dict[str, Any]:
    """
    Get context difference for a step.

    Shows what changed in the context between before and after execution.
    Useful for debugging data flow issues.
    """
    evidence_path = get_evidence_path()
    exec_dir, _ = _get_execution_dir(evidence_path, execution_id)
    safe_step_id = _validate_evidence_component(step_id, "step id")
    jsonl_path = _find_child(exec_dir, "evidence.jsonl")

    if jsonl_path is None or not jsonl_path.is_file():
        raise HTTPException(status_code=404, detail="Execution not found")

    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    if data.get('step_id') == safe_step_id:
                        before = data.get('context_before', {})
                        after = data.get('context_after', {})

                        # Calculate diff
                        added = {}
                        removed = {}
                        modified = {}

                        all_keys = set(before.keys()) | set(after.keys())
                        for key in all_keys:
                            if key not in before:
                                added[key] = after[key]
                            elif key not in after:
                                removed[key] = before[key]
                            elif before[key] != after[key]:
                                modified[key] = {
                                    "before": before[key],
                                    "after": after[key],
                                }

                        return {
                            "step_id": safe_step_id,
                            "added": added,
                            "removed": removed,
                            "modified": modified,
                            "unchanged_count": len(all_keys) - len(added) - len(removed) - len(modified),
                        }

                except json.JSONDecodeError:
                    continue

    except Exception as e:
        logger.exception("Failed to read context diff")
        raise HTTPException(status_code=500, detail="Failed to read evidence") from e

    raise HTTPException(status_code=404, detail="Step not found")
