"""
SPA Static File Mounting

Mounts the frontend dist directory and sets up SPA fallback routing.
Includes Cache-Control headers for optimal browser caching.

Extracted from main_local.py.
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response


# --- Cache-Control constants ---
# Versioned assets use content-hash filenames (e.g. assets/abc123.js) —
# safe to cache forever since the URL changes on every build.
_IMMUTABLE_CACHE = "public, max-age=31536000, immutable"
# HTML must always be revalidated so users get the latest SPA entry point.
_NO_CACHE = "no-cache, must-revalidate"


def mount_static_files(app: FastAPI, frontend_dist: Path) -> None:
    """Mount static files and SPA fallback routes.

    Args:
        app: The FastAPI application instance.
        frontend_dist: Path to the frontend dist directory.
    """
    if not frontend_dist.exists():
        return

    # --- Cache-Control middleware for static assets ---
    @app.middleware("http")
    async def cache_control_middleware(request: Request, call_next):
        response: Response = await call_next(request)
        path = request.url.path
        if path.startswith("/assets/"):
            response.headers["Cache-Control"] = _IMMUTABLE_CACHE
        elif path == "/" or path.endswith(".html"):
            response.headers["Cache-Control"] = _NO_CACHE
        return response

    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # Root-level static files (favicon, logos, etc.) — must come before SPA fallback
    _ROOT_STATIC_EXTS = frozenset({".ico", ".png", ".svg", ".jpg", ".jpeg", ".webp", ".xml", ".webmanifest", ".txt"})

    @app.get("/")
    async def read_root():
        return FileResponse(str(frontend_dist / "index.html"))

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        from fastapi.responses import JSONResponse
        import re

        if full_path.startswith(("api/", "assets/", "ws/")):
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": "Not Found", "error_code": "NOT_FOUND"},
            )

        if ".." in full_path or "\x00" in full_path:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "Invalid path", "error_code": "BAD_REQUEST"},
            )

        sensitive_patterns = [
            r"^\.env", r"^\.git", r"^\.svn", r"^\.hg",
            r"^\.htaccess", r"^\.htpasswd", r"^\.DS_Store", r"^Thumbs\.db",
            r"^config/", r"^private/", r"^admin/", r"^debug/",
            r"^\.well-known/",
            r".*\.sql$", r".*\.log$", r".*\.bak$", r".*\.backup$",
            r".*\.swp$", r".*~$",
        ]
        for pattern in sensitive_patterns:
            if re.match(pattern, full_path, re.IGNORECASE):
                return JSONResponse(
                    status_code=404,
                    content={"ok": False, "error": "Not Found", "error_code": "NOT_FOUND"},
                )

        static_file = frontend_dist / full_path
        try:
            resolved = static_file.resolve()
            if not str(resolved).startswith(str(frontend_dist.resolve())):
                return JSONResponse(
                    status_code=400,
                    content={"ok": False, "error": "Invalid path", "error_code": "BAD_REQUEST"},
                )
        except (OSError, ValueError):
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "Invalid path", "error_code": "BAD_REQUEST"},
            )

        if static_file.exists() and static_file.is_file():
            return FileResponse(str(static_file))
        return FileResponse(str(frontend_dist / "index.html"))
