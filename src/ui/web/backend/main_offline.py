"""
Offline Runner Entry Point

Fully self-contained FastAPI server for offline operation.
- No cloud dependency — all data and execution handled locally
- Local JWT auth for self-hosted CE; explicit loopback bypass for desktop mode
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

# === SSL certificates for packaged mode ===
if getattr(sys, 'frozen', False):
    try:
        import certifi
        os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    except ImportError:
        pass

# === Path Setup ===
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    _backend_dir = Path(sys._MEIPASS)
    os.chdir(Path.home() / ".flyto")
else:
    _backend_dir = Path(__file__).resolve().parent
    os.chdir(_backend_dir)

if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

if not getattr(sys, 'frozen', False):
    _project_root = _backend_dir.parent.parent.parent.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))

# === Hot-updated packages bootstrap (packaged mode only) ===
if getattr(sys, 'frozen', False):
    _pip_packages = Path.home() / ".flyto" / "pip_packages"
    if _pip_packages.exists() and str(_pip_packages) not in sys.path:
        sys.path.insert(0, str(_pip_packages))

    _core_current = Path.home() / ".flyto" / "core" / "current"
    if _core_current.exists():
        _resolved = _core_current.resolve()
        if str(_resolved) not in sys.path:
            sys.path.insert(0, str(_resolved))
    else:
        _pointer = Path.home() / ".flyto" / "core" / "current.txt"
        if _pointer.exists():
            _version = _pointer.read_text(encoding="utf-8").strip()
            _version_dir = Path.home() / ".flyto" / "core" / _version
            if _version_dir.exists() and str(_version_dir) not in sys.path:
                sys.path.insert(0, str(_version_dir))

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from config.settings import get_settings
from config.paths import get_path_resolver
from config.constants import APP_NAME, APP_VERSION
from api import create_offline_router
from middleware.common import setup_cors, setup_common_middleware

from local.browser_bootstrap import (
    configure_playwright_browsers_path,
    ensure_node_binary,
    ensure_playwright_chromium,
)
from local.websocket_routes import register_websocket_routes
from local.static_files import mount_static_files
from local.lifespan_local import (
    init_capabilities, init_breakpoint_manager, cleanup_stale_browser_locks,
)

logger = logging.getLogger(__name__)

# File logging for offline debugging
try:
    _log_dir = Path.home() / ".flyto"
    _log_dir.mkdir(parents=True, exist_ok=True)
    _file_handler = logging.FileHandler(_log_dir / "offline.log", encoding="utf-8")
    _file_handler.setLevel(logging.INFO)
    _file_handler.setFormatter(logging.Formatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    ))
    logging.getLogger().addHandler(_file_handler)
except Exception:
    pass

settings = get_settings()
paths = get_path_resolver()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown for Offline Runner."""
    configure_playwright_browsers_path()
    from services.observability.log_manager import get_log_manager
    get_log_manager().install_handler()

    await init_capabilities()

    logger.info("=" * 60)
    logger.info(f"Flyto2 Offline Runner v{APP_VERSION}")
    logger.info("Mode: offline (no cloud dependency)")
    logger.info("=" * 60)

    # Initialize offline SQLite database
    from gateway.storage.offline_db import init_offline_db
    init_offline_db()
    from gateway.providers.auth.offline import validate_offline_auth_configuration
    validate_offline_auth_configuration()
    logger.info("Offline database initialized")

    cleanup_stale_browser_locks()

    # Mark startup complete
    from api.health import mark_startup_complete
    mark_startup_complete()
    init_breakpoint_manager()

    logger.info("Server ready, loading modules in background...")

    # Deferred heavy init (modules, browser)
    async def _run_deferred():
        # Scan modules
        from services.infra.module_scanner import ModuleScanner
        scanner = ModuleScanner()
        result = scanner.scan_modules()
        if result['status'] == 'success':
            logger.info(f"Loaded {result['count']} modules from {len(result['categories'])} categories")
        else:
            logger.warning(f"Module scan failed: {result['message']}")

        # Browser bootstrap (Playwright + Node)
        try:
            await asyncio.gather(
                ensure_node_binary(),
                ensure_playwright_chromium(),
                return_exceptions=True,
            )
        except Exception as e:
            logger.warning(f"Background browser setup skipped: {e}")

        # Alert scheduler (SQLite-backed)
        try:
            from services.observability.alerts.scheduler import start_alert_scheduler
            await start_alert_scheduler()
        except (ImportError, Exception):
            pass

        # Tracing (SQLite-backed)
        try:
            from services.observability.tracing import get_tracer, SqliteTraceExporter
            exporter = SqliteTraceExporter()
            get_tracer(exporter=exporter)
        except (ImportError, Exception):
            pass

        logger.info("=" * 60)
        logger.info("Offline Runner fully initialized")
        logger.info("=" * 60)

    task = asyncio.create_task(_run_deferred())
    task.add_done_callback(
        lambda t: logger.error(f"Deferred init failed: {t.exception()}") if t.exception() else None
    )

    yield

    # --- Shutdown ---

    # Stop alert scheduler
    try:
        from services.observability.alerts.scheduler import stop_alert_scheduler
        await stop_alert_scheduler()
    except (ImportError, Exception):
        pass

    # Close offline database
    try:
        from gateway.storage.offline_db import close_offline_db
        close_offline_db()
    except Exception:
        pass

    # Close execution database
    try:
        from gateway.storage.database import close_db
        close_db()
    except Exception:
        pass

    logger.info("Offline Runner shut down")


app = FastAPI(
    title=f"{APP_NAME} Offline Runner",
    version=APP_VERSION,
    description="Fully offline runner with local JWT auth, SQLite data, and execution engine",
    redirect_slashes=True,
    lifespan=lifespan,
)

# --- Middleware ---

HEADER_SIDECAR_AUTH = "X-Flyto2-" + "Secret"
LEGACY_HEADER_SIDECAR_AUTH = "X-" + "Flyto-" + "Secret"

setup_cors(
    app,
    origins=settings.cors_origins,
    extra_headers=[HEADER_SIDECAR_AUTH, LEGACY_HEADER_SIDECAR_AUTH],
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


# --- Mount Offline Routes (local execution + auth + CRUD) ---

offline_router = create_offline_router()
app.include_router(offline_router)


# --- WebSocket endpoints ---

register_websocket_routes(app, sidecar_secret="")


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

    parser = argparse.ArgumentParser(description="Flyto2 Offline Runner")
    parser.add_argument("--port", type=int, default=None, help="Override server port")
    parser.add_argument("--host", type=str, default=None, help="Override server host")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload in dev mode")
    args = parser.parse_args()

    _host = args.host or settings.api_host
    _port = args.port or settings.api_port
    _is_dev = not getattr(sys, 'frozen', False)

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
