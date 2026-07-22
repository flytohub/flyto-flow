"""
Workflow output file download / open endpoints.

Security:
- Scoped to the fixed local workspace
- Path traversal: whitelist roots only, resolve symlinks, verify containment
- Cloud mode: only /download (no subprocess)
- Desktop mode: /open and /reveal via safe subprocess (no shell=True)
- Filename sanitization in Content-Disposition
"""

import logging
import mimetypes
import os
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse

from gateway.local_context import get_local_actor

get_workspace_context = get_local_actor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/files", tags=["Files"])

# Allowed workspace roots — files MUST be under one of these
_WORKSPACE_ROOTS = [
    Path.home() / ".flyto",
]

# Add cwd ONLY in local/desktop mode (not cloud)
if not os.environ.get("K_SERVICE"):  # K_SERVICE = Cloud Run
    _WORKSPACE_ROOTS.append(Path.cwd())


def _safe_resolve(filepath: str) -> Path:
    """Resolve filepath, strictly verified against workspace roots.

    Prevents:
    - Path traversal (../)
    - Symlink escape
    - Access outside workspace
    """
    if not filepath or not filepath.strip():
        raise HTTPException(400, "Empty file path")

    if "\x00" in filepath:
        raise HTTPException(400, "Invalid file path")

    # Reject traversal before parsing the native path. The final path is built
    # by walking entries discovered below an allowed root, so user input never
    # becomes a filesystem path passed directly to an operating-system sink.
    normalized = filepath.replace("\\", "/")
    if any(part in {".", ".."} for part in normalized.split("/")):
        raise HTTPException(403, "Access denied — invalid file path")

    path = Path(filepath)

    def walk_existing(root: Path, parts: tuple[str, ...]) -> Path | None:
        current = root.resolve()
        try:
            for part in parts:
                if part in {"", ".", ".."}:
                    return None
                current = next(
                    (entry for entry in current.iterdir() if entry.name == part),
                    None,
                )
                if current is None:
                    return None
        except OSError:
            return None

        resolved = current.resolve()
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            return None
        return resolved

    for root in _WORKSPACE_ROOTS:
        root_resolved = root.resolve()
        if path.is_absolute():
            root_parts = root_resolved.parts
            if path.parts[:len(root_parts)] != root_parts:
                continue
            relative_parts = path.parts[len(root_parts):]
        else:
            relative_parts = path.parts

        resolved = walk_existing(root_resolved, relative_parts)
        if resolved is not None and resolved.is_file():
            return resolved

    if path.is_absolute():
        raise HTTPException(403, "Access denied — file outside workspace")
    raise HTTPException(404, "File not found")


def _sanitize_filename(name: str) -> str:
    """Sanitize filename for Content-Disposition header."""
    # Remove anything that's not alphanumeric, dash, underscore, dot
    sanitized = re.sub(r'[^\w\-.]', '_', name)
    return sanitized or "download"


def _is_desktop() -> bool:
    """Check if running in Desktop mode (not Cloud Run)."""
    return not os.environ.get("K_SERVICE")


# ── Download (all modes) ──

@router.get("/download")
async def download_file(
    path: str = Query(..., description="File path from workflow output"),
    workspace_context: dict = Depends(get_workspace_context),
):
    """Download a file produced by a workflow execution."""
    resolved = _safe_resolve(path)

    if not resolved.is_file():
        raise HTTPException(404, "File not found")

    content_type, _ = mimetypes.guess_type(str(resolved))
    filename = _sanitize_filename(resolved.name)

    return FileResponse(
        path=str(resolved),
        media_type=content_type or "application/octet-stream",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Open / Reveal (Desktop only) ──

@router.post("/open")
async def open_file_locally(
    path: str = Query(..., description="File path to open"),
    workspace_context: dict = Depends(get_workspace_context),
):
    """Open a file with OS default app. Desktop mode only."""
    if not _is_desktop():
        raise HTTPException(403, "Only available in Desktop mode")

    import platform
    import subprocess

    resolved = _safe_resolve(path)
    if not resolved.is_file():
        raise HTTPException(404, "File not found")

    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.Popen(["open", str(resolved)])
        elif system == "Windows":
            # Use os.startfile instead of shell=True to avoid injection
            os.startfile(str(resolved))
        else:
            subprocess.Popen(["xdg-open", str(resolved)])
    except Exception:
        logger.exception("Failed to open file")
        raise HTTPException(500, "Failed to open file")

    return {"ok": True, "path": str(resolved)}


@router.post("/reveal")
async def reveal_in_finder(
    path: str = Query(..., description="File path to reveal"),
    workspace_context: dict = Depends(get_workspace_context),
):
    """Reveal file in Finder/Explorer. Desktop mode only."""
    if not _is_desktop():
        raise HTTPException(403, "Only available in Desktop mode")

    import platform
    import subprocess

    resolved = _safe_resolve(path)
    if not resolved.is_file():
        raise HTTPException(404, "File not found")

    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.Popen(["open", "-R", str(resolved)])
        elif system == "Windows":
            subprocess.Popen(["explorer", "/select,", str(resolved)])
        else:
            subprocess.Popen(["xdg-open", str(resolved.parent)])
    except Exception:
        logger.exception("Failed to reveal file")
        raise HTTPException(500, "Failed to reveal file")

    return {"ok": True, "path": str(resolved)}
