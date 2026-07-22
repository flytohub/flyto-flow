"""Turn local file paths in execution output into local download URLs."""

from pathlib import Path
from typing import Any, Dict, Optional


_FILE_PATH_FIELDS = ("path", "filepath", "file_path", "output_path", "saved_to")
_DOWNLOADABLE_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
    ".csv", ".json", ".xml", ".txt", ".md", ".html",
    ".xlsx", ".docx", ".zip", ".tar", ".gz",
    ".mp4", ".webm", ".mp3", ".wav", ".mhtml",
}


async def process_execution_outputs(
    result: Any,
    node_outputs: Optional[Dict[str, Any]] = None,
    base_url: str = "/api/files/download",
    workspace_id: Optional[str] = None,
) -> None:
    """Add same-origin download metadata to local output dictionaries in place."""
    del workspace_id

    if isinstance(result, dict):
        _inject_download_url(result, base_url)
        steps_context = result.get("steps")
        if isinstance(steps_context, dict):
            for step_output in steps_context.values():
                if isinstance(step_output, dict):
                    _inject_download_url(step_output, base_url)
                    data = step_output.get("data")
                    if isinstance(data, dict):
                        _inject_download_url(data, base_url)

    if isinstance(node_outputs, dict):
        for output in node_outputs.values():
            if isinstance(output, dict):
                _inject_download_url(output, base_url)
                data = output.get("data")
                if isinstance(data, dict):
                    _inject_download_url(data, base_url)


def _inject_download_url(output: dict, base_url: str) -> None:
    if "download_url" in output:
        return

    for field in _FILE_PATH_FIELDS:
        filepath = output.get(field)
        if not filepath or not isinstance(filepath, str):
            continue

        path = Path(filepath)
        if path.suffix.lower() not in _DOWNLOADABLE_EXTENSIONS:
            continue

        resolved = path if path.is_absolute() else Path.cwd() / path
        if not resolved.exists() or not resolved.is_file():
            continue

        resolved = resolved.resolve()
        output["download_url"] = f"{base_url}?path={_url_encode(str(resolved))}"
        output["download_filename"] = resolved.name
        output["download_size"] = resolved.stat().st_size
        return


def _url_encode(path: str) -> str:
    from urllib.parse import quote

    return quote(path, safe="")
