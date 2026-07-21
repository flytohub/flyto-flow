"""
Package Definitions and Constants

System package registry, auto-update settings, and shared constants
used by the Package Manager API.

Extracted from helpers.py for maintainability.
"""

import sys
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

_IS_FROZEN = getattr(sys, 'frozen', False)

# In frozen mode, pip packages go here instead of system site-packages
_PIP_TARGET_DIR = Path.home() / ".flyto" / "pip_packages"

# Temporary download cache
_CACHE_DIR = Path.home() / ".flyto" / "cache"

# =============================================================================
# Package Definitions
# =============================================================================

SYSTEM_PACKAGES = [
    {
        'id': 'flyto-core',
        'name': 'Flyto2 Core',
        'description': 'Workflow execution engine & module registry',
        'pip_name': 'flyto-core',
        'pypi_url': 'https://pypi.org/pypi/flyto-core/json',
        'icon': 'cpu',
        'color': '#8B5CF6',
        'category': 'engine',
        'removable': False,
        'hot_update': True,
    },
    {
        'id': 'flyto-ai',
        'name': 'Flyto2 AI',
        'description': 'AI browser agent & automation intelligence',
        'pip_name': 'flyto-ai',
        'pypi_url': 'https://pypi.org/pypi/flyto-ai/json',
        'icon': 'brain',
        'color': '#EC4899',
        'category': 'ai',
        'removable': True,
    },
    {
        'id': 'playwright',
        'name': 'Playwright',
        'description': 'Browser automation framework',
        'pip_name': 'playwright',
        'pypi_url': 'https://pypi.org/pypi/playwright/json',
        'icon': 'globe',
        'color': '#2563EB',
        'category': 'browser',
        'removable': True,
    },
    {
        'id': 'chromium',
        'name': 'Chromium Browser',
        'description': 'Headless browser for web automation',
        'pip_name': None,
        'pypi_url': None,
        'icon': 'chrome',
        'color': '#F59E0B',
        'category': 'browser',
        'removable': True,
    },
    {
        'id': 'pyngrok',
        'name': 'ngrok Tunnel',
        'description': 'Public URL tunnel for webhook callbacks',
        'pip_name': 'pyngrok',
        'pypi_url': 'https://pypi.org/pypi/pyngrok/json',
        'icon': 'link',
        'color': '#10B981',
        'category': 'network',
        'removable': True,
    },
    {
        'id': 'flyto-modules-pro',
        'name': 'Pro Modules',
        'description': 'Premium workflow modules (commercial)',
        'pip_name': 'flyto-modules-pro',
        'pypi_url': 'https://pypi.org/pypi/flyto-modules-pro/json',
        'icon': 'crown',
        'color': '#F97316',
        'category': 'engine',
        'removable': True,
    },
]

_PACKAGES_BY_ID = {p['id']: p for p in SYSTEM_PACKAGES}

# Auto-update settings file
_SETTINGS_DIR = Path(__file__).parent.parent.parent / 'data'
_AUTO_UPDATE_FILE = _SETTINGS_DIR / 'auto_update.json'


def _load_auto_update_settings() -> dict:
    """Load per-package auto-update settings from disk."""
    try:
        if _AUTO_UPDATE_FILE.exists():
            return json.loads(_AUTO_UPDATE_FILE.read_text())
    except Exception:
        pass
    return {}


def _save_auto_update_settings(settings: dict) -> None:
    """Persist per-package auto-update settings to disk."""
    try:
        _SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        _AUTO_UPDATE_FILE.write_text(json.dumps(settings, indent=2))
    except Exception as e:
        logger.warning("Failed to save auto-update settings: %s", e)


# =============================================================================
# Version Detection
# =============================================================================


def _get_installed_version(pkg: dict) -> "str | None":
    """Get installed version for a package."""
    if pkg['id'] == 'chromium':
        return _get_chromium_version()

    pip_name = pkg.get('pip_name')
    if not pip_name:
        return None

    # flyto-core in frozen mode: check HotUpdater first
    if pip_name == 'flyto-core' and _IS_FROZEN:
        try:
            from services.infra.updater import get_core_updater
            hot_version = get_core_updater().current_version
            if hot_version:
                return hot_version
        except Exception:
            pass

    # Check pip_packages target dir (frozen mode installs)
    if _PIP_TARGET_DIR.exists():
        version = _get_version_from_dist_info(pip_name)
        if version:
            return version

    # Standard importlib.metadata (dev mode or bundled)
    try:
        from importlib.metadata import version as pkg_version
        return pkg_version(pip_name)
    except Exception:
        pass

    return None


def _get_version_from_dist_info(pip_name: str) -> "str | None":
    """
    Read version from .dist-info directory in pip_packages target dir.
    This is more reliable than importlib.metadata under PyInstaller.
    """
    if not _PIP_TARGET_DIR.exists():
        return None
    normalized = pip_name.replace('-', '_').lower()
    try:
        for item in _PIP_TARGET_DIR.iterdir():
            if item.is_dir() and item.name.endswith('.dist-info'):
                # e.g., flyto_ai-0.9.27.dist-info
                prefix = item.name[:-len('.dist-info')]
                parts = prefix.rsplit('-', 1)
                if len(parts) == 2:
                    name = parts[0].lower().replace('-', '_')
                    if name == normalized:
                        return parts[1]
    except Exception:
        pass
    return None


def _get_chromium_version() -> "str | None":
    """Check if Chromium is installed via Playwright."""
    try:
        import os
        home = Path.home()
        # Persistent browser path set in main_local.py
        flyto_browsers = Path(os.environ.get(
            "PLAYWRIGHT_BROWSERS_PATH",
            str(home / '.flyto' / 'browsers'),
        ))
        # Default Playwright cache paths
        ms_pw = home / '.cache' / 'ms-playwright'
        ms_pw_mac = home / 'Library' / 'Caches' / 'ms-playwright'

        for browser_dir in (flyto_browsers, ms_pw, ms_pw_mac):
            if browser_dir.exists():
                chromium_dirs = [d for d in browser_dir.iterdir() if d.name.startswith('chromium')]
                if chromium_dirs:
                    try:
                        from importlib.metadata import version as pkg_version
                        return pkg_version('playwright')
                    except Exception:
                        return "installed"
        return None
    except Exception:
        return None
