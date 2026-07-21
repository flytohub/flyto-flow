"""
Post-execution file output processor.

Scans workflow step outputs for file paths and converts them to download URLs.
- Desktop mode: /api/files/download?path=... (local file)
- Cloud mode: uploads through the configured storage provider

Recognized output patterns:
- {"path": "/path/to/file.pdf"} or {"filepath": "..."} — single file
- {"status": "success", "path": "..."} — common module output format
"""

from io import BytesIO
import logging
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Fields that may contain file paths in step outputs
_FILE_PATH_FIELDS = ("path", "filepath", "file_path", "output_path", "saved_to")

# File extensions that indicate a downloadable output
_DOWNLOADABLE_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
    ".csv", ".json", ".xml", ".txt", ".md", ".html",
    ".xlsx", ".docx", ".zip", ".tar", ".gz",
    ".mp4", ".webm", ".mp3", ".wav",
    ".mhtml",
}


async def process_execution_outputs(
    result: Any,
    node_outputs: Optional[Dict[str, Any]] = None,
    base_url: str = "/api/files/download",
    user_id: Optional[str] = None,
) -> None:
    """Scan execution result and node outputs for file paths, add download_url.

    Desktop mode: download_url = /api/files/download?path=...
    Cloud mode: uploads file to configured storage provider.

    Modifies dicts in-place.
    """
    is_cloud = bool(os.environ.get("K_SERVICE"))

    if isinstance(result, dict):
        await _inject_download_url(result, base_url, is_cloud, user_id)

        # Engine returns step outputs under result['steps'] (keyed by step_id)
        steps_context = result.get("steps")
        if isinstance(steps_context, dict):
            for step_id, step_output in steps_context.items():
                if isinstance(step_output, dict):
                    await _inject_download_url(step_output, base_url, is_cloud, user_id)
                    # Also check nested .data dict
                    data = step_output.get("data")
                    if isinstance(data, dict):
                        await _inject_download_url(data, base_url, is_cloud, user_id)

    # Also process node_outputs if populated by hooks
    if isinstance(node_outputs, dict):
        for node_id, output in node_outputs.items():
            if isinstance(output, dict):
                await _inject_download_url(output, base_url, is_cloud, user_id)
                data = output.get("data")
                if isinstance(data, dict):
                    await _inject_download_url(data, base_url, is_cloud, user_id)


async def _inject_download_url(
    output: dict,
    base_url: str,
    is_cloud: bool,
    user_id: Optional[str],
) -> None:
    """If output dict has a file path field, add download_url."""
    if "download_url" in output:
        return

    for field in _FILE_PATH_FIELDS:
        filepath = output.get(field)
        if not filepath or not isinstance(filepath, str):
            continue

        path = Path(filepath)
        if path.suffix.lower() not in _DOWNLOADABLE_EXTENSIONS:
            continue

        # Resolve the file
        resolved = None
        if path.is_absolute() and path.exists():
            resolved = path
        else:
            cwd_path = Path.cwd() / path
            if cwd_path.exists():
                resolved = cwd_path

        if not resolved:
            continue

        if is_cloud:
            cloud_url = await _upload_to_cloud_storage(resolved, user_id)
            if cloud_url:
                output["download_url"] = cloud_url
                output["download_filename"] = resolved.name
                output["download_size"] = resolved.stat().st_size
                return
        else:
            # Desktop: local download endpoint
            output["download_url"] = f"{base_url}?path={_url_encode(str(resolved))}"
            output["download_filename"] = resolved.name
            output["download_size"] = resolved.stat().st_size
            return


async def _upload_to_cloud_storage(
    filepath: Path,
    user_id: Optional[str],
) -> Optional[str]:
    """Upload a workflow output file through the configured storage provider."""
    if not user_id:
        logger.debug("Cloud storage upload skipped for %s: missing user_id", filepath.name)
        return None

    try:
        from gateway.providers.hub import get_data_provider

        provider = get_data_provider()
        storage = getattr(provider, "storage", None) if provider else None
        if storage is None:
            return None

        content_type, _ = mimetypes.guess_type(str(filepath))
        upload = await storage.upload_file(
            user_id=user_id,
            file_data=BytesIO(filepath.read_bytes()),
            filename=filepath.name,
            content_type=content_type or "application/octet-stream",
            purpose="execution_output",
        )

        logger.info("Uploaded %s to cloud storage (%d bytes)", filepath.name, filepath.stat().st_size)
        return upload.url

    except Exception as e:
        logger.warning("Cloud storage upload failed for %s: %s", filepath.name, e)
        return None


def _url_encode(path: str) -> str:
    """URL-encode a file path for query parameter."""
    from urllib.parse import quote
    return quote(path, safe="")
