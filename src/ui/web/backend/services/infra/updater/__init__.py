"""
Hot Updater Package

Three-layer hot update for flyto desktop app:
- Core: PyPI wheel -> ~/.flyto/core/
- Frontend: GitHub release -> ~/.flyto/frontend/
- Backend: Cloud API proxy (always current)
"""

from services.infra.updater.models import CoreVersion, FrontendVersion, UpdateStatus
from services.infra.updater.constants import (
    PYPI_PACKAGE_NAME,
    PYPI_API_URL,
    GITHUB_OWNER,
    GITHUB_REPO,
    GITHUB_API_BASE,
    UPDATE_CHECK_INTERVAL,
    utc_now,
)
from services.infra.updater.config import load_config, save_config
from services.infra.updater.version import compare_versions, check_pypi_latest, check_for_updates
from services.infra.updater.download import download_version, install_symlink, resolve_current_path
from services.infra.updater.reload import reload_modules, notify_frontend_update
from services.infra.updater.frontend import FrontendUpdater
from services.infra.updater.service import (
    HotUpdater,
    CoreUpdater,  # backward-compatible alias
    get_core_updater,
    get_hot_updater,
    init_core_updater,
)

__all__ = [
    # Models
    "CoreVersion",
    "FrontendVersion",
    "UpdateStatus",
    # Constants
    "PYPI_PACKAGE_NAME",
    "PYPI_API_URL",
    "GITHUB_OWNER",
    "GITHUB_REPO",
    "GITHUB_API_BASE",
    "UPDATE_CHECK_INTERVAL",
    "utc_now",
    # Config
    "load_config",
    "save_config",
    # Version
    "compare_versions",
    "check_pypi_latest",
    "check_for_updates",
    # Download
    "download_version",
    "install_symlink",
    "resolve_current_path",
    # Reload
    "reload_modules",
    "notify_frontend_update",
    # Frontend
    "FrontendUpdater",
    # Service
    "HotUpdater",
    "CoreUpdater",
    "get_core_updater",
    "get_hot_updater",
    "init_core_updater",
]
