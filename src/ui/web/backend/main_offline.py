"""
Flyto2 Flow Entry Point

Fully self-contained FastAPI server for offline operation.
- No cloud dependency — all data and execution handled locally
- One fixed local workspace with no identity service
- Uses SQLite for workflows, templates, and execution history
- Does NOT proxy to any external service

Usage:
    python main_offline.py
    uvicorn main_offline:app --host 127.0.0.1 --port 9000
"""

import sys
import os
from pathlib import Path

# === Deployment mode ===
os.environ["DEPLOYMENT_MODE"] = "offline"

# === Persistent offline data directory ===
# CE containers mount this directory as a writable volume. Desktop builds
# continue to use ~/.flyto when no explicit database path is configured.
_configured_db_path = os.environ.get("FLYTO_OFFLINE_DB_PATH", "").strip()
if _configured_db_path:
    _offline_data_dir = Path(_configured_db_path).expanduser().parent
else:
    _offline_data_dir = Path.home() / ".flyto"
_offline_data_dir.mkdir(parents=True, exist_ok=True)

# === Persistent browser path for Playwright ===
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(_offline_data_dir / "browsers"))
# === SSL certificates for packaged mode ===
if getattr(sys, "frozen", False):
    try:
        import certifi

        os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    except ImportError:
        pass

# === Path Setup ===
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    _backend_dir = Path(sys._MEIPASS)
    os.chdir(_offline_data_dir)
else:
    _backend_dir = Path(__file__).resolve().parent
    os.chdir(_backend_dir)

if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

if not getattr(sys, "frozen", False):
    _project_root = _backend_dir.parent.parent.parent.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))

# A flyto-core wheel explicitly imported by the local administrator overrides
# the image baseline. This reads local files only and never checks a registry.
from local.core_wheel import activate_installed_core

activate_installed_core()

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from config.settings import get_settings
from config.paths import get_path_resolver
from config.constants import APP_NAME, APP_VERSION
from api import create_offline_router
from middleware.common import setup_cors, setup_common_middleware

from local.websocket_routes import register_websocket_routes
from local.static_files import mount_static_files
from local.lifespan_local import (
    init_capabilities,
    init_breakpoint_manager,
    cleanup_stale_browser_locks,
    seed_starter_templates,
)
from local.runtime_dependencies import verify_bundled_runtime

logger = logging.getLogger(__name__)

# File logging for offline debugging
try:
    _log_dir = _offline_data_dir
    _log_dir.mkdir(parents=True, exist_ok=True)
    _file_handler = logging.FileHandler(_log_dir / "offline.log", encoding="utf-8")
    _file_handler.setLevel(logging.INFO)
    _file_handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
    logging.getLogger().addHandler(_file_handler)
except Exception:
    pass

settings = get_settings()
paths = get_path_resolver()


def _scan_modules() -> None:
    from services.infra.module_scanner import ModuleScanner

    result = ModuleScanner().scan_modules()
    if result["status"] == "success":
        logger.info(f"Loaded {result['count']} modules from {len(result['categories'])} categories")
    else:
        logger.warning(f"Module scan failed: {result['message']}")


async def _start_alerts() -> None:
    try:
        from services.observability.alerts.scheduler import start_alert_scheduler

        await start_alert_scheduler()
    except (ImportError, Exception):
        pass


def _init_tracing() -> None:
    try:
        from services.observability.tracing import get_tracer, SqliteTraceExporter

        get_tracer(exporter=SqliteTraceExporter())
    except (ImportError, Exception):
        pass


async def _run_deferred() -> None:
    _scan_modules()
    await _start_alerts()
    _init_tracing()
    logger.info("=" * 60)
    logger.info("Flyto2 Flow fully initialized")
    logger.info("=" * 60)


async def _startup() -> asyncio.Task:
    verify_bundled_runtime()
    from services.observability.log_manager import get_log_manager

    get_log_manager().install_handler()
    await init_capabilities()
    logger.info("=" * 60)
    logger.info(f"Flyto2 Flow v{APP_VERSION}")
    logger.info("Mode: local offline")
    logger.info("=" * 60)

    from gateway.storage.offline_db import init_offline_db

    init_offline_db()
    logger.info("Offline database initialized")
    await seed_starter_templates()
    cleanup_stale_browser_locks()
    from api.health import mark_startup_complete

    mark_startup_complete()
    init_breakpoint_manager()
    logger.info("Server ready, loading modules in background...")
    task = asyncio.create_task(_run_deferred())
    task.add_done_callback(
        lambda completed: (
            logger.error(f"Deferred init failed: {completed.exception()}") if completed.exception() else None
        )
    )
    return task


async def _shutdown() -> None:
    try:
        from services.observability.alerts.scheduler import stop_alert_scheduler

        await stop_alert_scheduler()
    except (ImportError, Exception):
        pass
    try:
        from gateway.storage.offline_db import close_offline_db

        close_offline_db()
    except Exception:
        pass
    try:
        from gateway.storage.database import close_db

        close_db()
    except Exception:
        pass
    logger.info("Flyto2 Flow shut down")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start and stop the local Flyto2 Flow runtime."""
    await _startup()
    yield
    await _shutdown()


app = FastAPI(
    title="Flyto2 Flow",
    version=APP_VERSION,
    description="Local visual workflow builder, MCP server, and execution engine",
    redirect_slashes=True,
    lifespan=lifespan,
)

# --- Middleware ---

setup_cors(
    app,
    origins=settings.cors_origins,
)

# Production security hardening
from middleware.security_hardening import ErrorSanitizationMiddleware, RequestSizeLimitMiddleware

app.add_middleware(ErrorSanitizationMiddleware)
app.add_middleware(RequestSizeLimitMiddleware, max_body_size=50 * 1024 * 1024)  # 50MB

setup_common_middleware(
    app,
    extra_logging_excludes=["/metrics", "/ws/logs"],
    csrf_allowed_origins=list(settings.cors_origins),
)


# --- Health Check ---


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "mode": "offline",
    }


# --- Mount local CE routes ---

offline_router = create_offline_router()
app.include_router(offline_router)


# --- WebSocket endpoints ---

register_websocket_routes(app)


# --- Catch-all: No proxy — return 404 for unmatched /api/* routes ---


@app.api_route(
    "/api/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    include_in_schema=False,
)
async def _no_proxy(path: str):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=404,
        content={"ok": False, "error": f"Route /api/{path} not available in offline mode"},
    )


# --- Static files (frontend SPA) ---

mount_static_files(app, paths.frontend_dist)


# === Standalone Entry Point ===
if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="Flyto2 Flow")
    parser.add_argument("--port", type=int, default=None, help="Override server port")
    parser.add_argument("--host", type=str, default=None, help="Override server host")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload in dev mode")
    args = parser.parse_args()

    _host = args.host or settings.api_host
    _port = args.port or settings.api_port
    _is_dev = not getattr(sys, "frozen", False)

    if _is_dev and not args.no_reload:
        uvicorn.run(
            "main_offline:app",
            host=_host,
            port=_port,
            log_level="info",
            reload=True,
            reload_dirs=[str(Path(__file__).resolve().parent)],
        )
    else:
        uvicorn.run(
            app,
            host=_host,
            port=_port,
            log_level="info",
        )
