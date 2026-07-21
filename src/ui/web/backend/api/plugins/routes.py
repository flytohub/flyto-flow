"""
Plugins API - HuggingFace Model Browser & Local Plugin Manager

Architecture:
- Search/Info: Direct HuggingFace API calls
- Install/Uninstall: Local ~/.flyto/plugins folder management
- No external dependencies - graceful degradation when nothing installed
"""
import json
import shutil
import logging
import aiohttp
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Query, HTTPException

from services.huggingface_models import (
    get_installed_model_provider,
    InstalledModel,
    DownloadStatus,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plugins", tags=["Plugins"])

# Configuration
PLUGINS_DIR = Path.home() / ".flyto" / "plugins"
HF_API_URL = "https://huggingface.co/api"
REQUEST_TIMEOUT = 30

# Ensure plugins directory exists
PLUGINS_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Root & Status Endpoints
# =============================================================================


@router.get("/")
async def plugins_status():
    """Get plugins system status."""
    return {
        "ok": True,
        "status": "active",
        "service": "plugins",
        "features": ["local_plugins", "huggingface"],
    }


@router.get("/tasks")
async def plugins_tasks():
    """Get running plugin tasks."""
    return {
        "ok": True,
        "tasks": [],
        "running": 0,
        "completed": 0,
    }


# =============================================================================
# Helper Functions
# =============================================================================

def model_id_to_dir_name(model_id: str) -> str:
    """Convert model_id (author/name) to safe directory name"""
    return model_id.replace("/", "__")


def dir_name_to_model_id(dir_name: str) -> str:
    """Convert directory name back to model_id"""
    return dir_name.replace("__", "/")


def parse_model_id(model_id: str) -> tuple[str, str]:
    """Extract author and name from model_id"""
    if "/" in model_id:
        parts = model_id.split("/", 1)
        return parts[0], parts[1]
    return "", model_id


def format_model_response(model: Dict[str, Any]) -> Dict[str, Any]:
    """Transform HuggingFace API response to frontend format"""
    model_id = model.get("id") or model.get("modelId") or ""
    author, name = parse_model_id(model_id)

    return {
        "model_id": model_id,
        "id": model_id,
        "name": name,
        "author": author,
        "downloads": model.get("downloads", 0),
        "likes": model.get("likes", 0),
        "tags": model.get("tags", []),
        "pipeline_tag": model.get("pipeline_tag"),
        "library_name": model.get("library_name"),
        "trending_score": model.get("trendingScore", 0),
    }


async def hf_request(endpoint: str, params: dict = None) -> Dict[str, Any]:
    """Make request to HuggingFace API"""
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{HF_API_URL}{endpoint}", params=params) as resp:
                if resp.status == 200:
                    return {"ok": True, "data": await resp.json()}
                if resp.status == 404:
                    return {"ok": False, "error": "Model not found"}

                logger.error(f"HuggingFace API {resp.status}: {await resp.text()[:200]}")
                return {"ok": False, "error": f"HuggingFace API error: {resp.status}"}

    except aiohttp.ClientError as e:
        logger.error(f"HuggingFace API error: {e}")
        return {"ok": False, "error": str(e)}


def scan_installed_plugins() -> List[Dict[str, Any]]:
    """Scan local plugins folder"""
    plugins = []

    if not PLUGINS_DIR.exists():
        return plugins

    for plugin_dir in PLUGINS_DIR.iterdir():
        if not plugin_dir.is_dir():
            continue

        meta_file = plugin_dir / "plugin.json"

        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text())
                meta["installed_path"] = str(plugin_dir)
                # Ensure model_id exists
                if "model_id" not in meta and "id" in meta:
                    meta["model_id"] = meta["id"]
                plugins.append(meta)
            except Exception as e:
                logger.warning(f"Invalid plugin.json in {plugin_dir}: {e}")
                model_id = dir_name_to_model_id(plugin_dir.name)
                plugins.append({
                    "model_id": model_id,
                    "id": model_id,
                    "name": plugin_dir.name,
                    "installed_path": str(plugin_dir),
                    "error": "Invalid plugin.json"
                })

    return plugins


# =============================================================================
# API Routes
# =============================================================================

@router.get("/search")
async def search_models(
    query: str = Query(..., description="Search query"),
    task: Optional[str] = Query(None, description="Filter by task type"),
    limit: int = Query(20, ge=1, le=100, description="Max results")
) -> Dict[str, Any]:
    """
    Search models on HuggingFace Hub.

    """


    params = {"search": query, "limit": limit}
    if task:
        params["filter"] = task

    result = await hf_request("/models", params)

    if not result["ok"]:
        raise HTTPException(502, result.get("error", "HuggingFace API error"))

    data = result.get("data", [])
    if not isinstance(data, list):
        data = [data] if data else []

    return {
        "ok": True,
        "data": [format_model_response(m) for m in data]
    }


@router.get("/info/{model_id:path}")
async def get_model_info(model_id: str) -> Dict[str, Any]:
    """
    Get model details from HuggingFace.

    """


    result = await hf_request(f"/models/{model_id}")

    if not result["ok"]:
        status = 404 if "not found" in result.get("error", "").lower() else 502
        raise HTTPException(status, result.get("error"))

    return {"ok": True, "data": result.get("data", {})}


@router.get("/installed")
async def list_installed(
    category: Optional[str] = Query(None),
    task: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """List installed plugins"""
    plugins = scan_installed_plugins()

    if category:
        plugins = [p for p in plugins if p.get("category") == category]
    if task:
        plugins = [p for p in plugins if p.get("pipeline_tag") == task]

    return {"ok": True, "data": plugins}


@router.post("/install/{model_id:path}")
async def install_model(model_id: str) -> Dict[str, Any]:
    """
    Install a model from HuggingFace.

    This does two things:
    1. Saves model metadata to ~/.flyto/plugins/{model_dir}/plugin.json (legacy)
    2. Adds model to installed_models.json via InstalledModelProvider (new)

    """


    provider = get_installed_model_provider()

    # Check if already installed in new system
    if provider.is_installed(model_id):
        return {
            "ok": True,
            "data": {"model_id": model_id, "status": "already_installed"}
        }

    # Fetch model info from HuggingFace
    result = await hf_request(f"/models/{model_id}")
    if not result["ok"]:
        raise HTTPException(404, f"Model {model_id} not found on HuggingFace")

    info = result.get("data", {})
    author, name = parse_model_id(model_id)

    # Determine task from pipeline_tag
    task = info.get("pipeline_tag") or "inference"

    # Create InstalledModel and add to provider
    installed_model = InstalledModel(
        model_id=model_id,
        task=task,
        name=name,
        author=info.get("author") or author,
        downloads=info.get("downloads", 0),
        likes=info.get("likes", 0),
        tags=info.get("tags", []),
        pipeline_tag=info.get("pipeline_tag"),
        library_name=info.get("library_name"),
    )
    provider.add(installed_model)

    # Also save to legacy plugin.json for backward compatibility
    plugin_dir = PLUGINS_DIR / model_id_to_dir_name(model_id)
    plugin_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "model_id": model_id,
        "id": model_id,
        "name": name,
        "author": info.get("author") or author,
        "downloads": info.get("downloads", 0),
        "likes": info.get("likes", 0),
        "pipeline_tag": info.get("pipeline_tag"),
        "tags": info.get("tags", []),
        "library_name": info.get("library_name"),
        "source": "huggingface",
        "source_url": f"https://huggingface.co/{model_id}"
    }

    (plugin_dir / "plugin.json").write_text(json.dumps(meta, indent=2))

    logger.info(f"Installed HuggingFace model: {model_id} (task: {task})")

    return {
        "ok": True,
        "data": {
            "model_id": model_id,
            "task": task,
            "status": "installed",
            "path": str(plugin_dir)
        }
    }


@router.delete("/uninstall/{model_id:path}")
async def uninstall_model(model_id: str) -> Dict[str, Any]:
    """
    Uninstall a model.

    This does two things:
    1. Removes from installed_models.json via InstalledModelProvider
    2. Removes legacy plugin directory if exists
    """
    provider = get_installed_model_provider()
    plugin_dir = PLUGINS_DIR / model_id_to_dir_name(model_id)

    # Check if installed in either system
    is_in_provider = provider.is_installed(model_id)
    is_in_legacy = plugin_dir.exists()

    if not is_in_provider and not is_in_legacy:
        raise HTTPException(404, f"Model {model_id} is not installed")

    try:
        # Remove from new system
        if is_in_provider:
            provider.remove(model_id)

        # Remove legacy directory
        if is_in_legacy:
            shutil.rmtree(plugin_dir)

        logger.info(f"Uninstalled HuggingFace model: {model_id}")
        return {"ok": True, "data": {"model_id": model_id, "status": "uninstalled"}}
    except Exception as e:
        logger.error(f"Failed to uninstall {model_id}: {e}")
        raise HTTPException(500, str(e))


@router.get("/status/{model_id:path}")
async def get_status(model_id: str) -> Dict[str, Any]:
    """Get model installation and download status"""
    provider = get_installed_model_provider()
    model = provider.get(model_id)

    if model is None:
        return {
            "ok": True,
            "data": {
                "model_id": model_id,
                "installed": False,
                "downloaded": False,
            }
        }

    return {
        "ok": True,
        "data": {
            "model_id": model_id,
            "installed": True,
            "task": model.task,
            "download_status": model.download_status,
            "downloaded": model.download_status == DownloadStatus.DOWNLOADED.value,
            "local_path": model.local_path,
            "preferred_runtime": model.preferred_runtime,
        }
    }


@router.get("/models")
async def list_installed_models(
    task: Optional[str] = Query(None, description="Filter by task type")
) -> Dict[str, Any]:
    """
    List installed models from the new InstalledModelProvider.

    This is the preferred endpoint for getting installed models.
    """
    provider = get_installed_model_provider()

    if task:
        models = provider.list_by_task(task)
    else:
        models = provider.list_installed()

    return {
        "ok": True,
        "data": [m.to_dict() for m in models],
        "total": len(models)
    }


@router.get("/models/statistics")
async def get_model_statistics() -> Dict[str, Any]:
    """Get statistics about installed models"""
    provider = get_installed_model_provider()
    return {
        "ok": True,
        "data": provider.get_statistics()
    }


@router.get("/cache/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    plugins = scan_installed_plugins()

    total_size = sum(
        f.stat().st_size
        for p in plugins
        for f in Path(p.get("installed_path", "")).rglob("*")
        if f.is_file()
    )

    return {
        "ok": True,
        "data": {
            "plugins_dir": str(PLUGINS_DIR),
            "installed_count": len(plugins),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
    }
