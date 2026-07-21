"""
Path Resolution Utility

Provides paths for flyto-cloud project directories.
flyto-core modules are imported from pip package, not local files.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PathResolver:
    """
    Path resolution for flyto-cloud project directories.

    Note: flyto-core is installed via pip (core.modules).
    No local path detection needed for core modules.
    """

    def __init__(self):
        """Initialize with lazy cloud root resolution."""
        self._cloud_root: Optional[Path] = None

    @property
    def cloud_root(self) -> Path:
        """Get flyto-cloud root directory"""
        if self._cloud_root is None:
            self._cloud_root = self._find_cloud_root()
        return self._cloud_root

    @property
    def is_docker(self) -> bool:
        """Check if running in Docker/containerized environment"""
        return (
            Path('/app/flyto-server').exists() or
            Path('/app/static').exists() or
            Path('/app/backend').exists()
        )

    @property
    def backend_root(self) -> Path:
        """Get backend directory"""
        if self.is_docker:
            # Standalone deployment: everything is in /app
            if Path('/app/flyto-server').exists():
                return Path('/app')
            return Path('/app/backend')
        return self.cloud_root / 'src' / 'ui' / 'web' / 'backend'

    @property
    def frontend_root(self) -> Path:
        """Get frontend directory"""
        if self.is_docker:
            # Standalone deployment: static is in /app
            if Path('/app/static').exists():
                return Path('/app')
            return Path('/app/frontend')  # May not exist in backend-only Docker
        return self.cloud_root / 'src' / 'ui' / 'web' / 'frontend'

    @property
    def frontend_dist(self) -> Path:
        """
        Get frontend build output directory.

        Priority:
        1. Hot-updated: ~/.flyto/frontend/dist/ (if exists and has index.html)
        2. PyInstaller: sys._MEIPASS/static (frozen standalone build)
        3. Docker: /app/static
        4. Dev: frontend/dist/
        """
        # Hot-updated frontend takes priority
        hot_frontend = Path.home() / ".flyto" / "frontend" / "dist"
        if hot_frontend.exists() and (hot_frontend / "index.html").exists():
            return hot_frontend

        # PyInstaller frozen build
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            meipass = Path(sys._MEIPASS)
            # --onedir: data files are alongside the executable
            frozen_static = meipass / 'static'
            if frozen_static.exists():
                return frozen_static
            # macOS .app bundle: data files go to Contents/Resources/
            resources_static = meipass.parent / 'Resources' / 'static'
            if resources_static.exists():
                return resources_static

        if self.is_docker:
            if Path('/app/static').exists():
                return Path('/app/static')
            return Path('/app/frontend/dist')
        return self.frontend_root / 'dist'

    def _find_cloud_root(self) -> Path:
        """Find flyto-cloud root from current file location"""
        # PyInstaller frozen binary: use _MEIPASS as root
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            return Path(sys._MEIPASS)

        # Standalone/Docker deployment: /app/flyto-server or /app/static
        if Path('/app/flyto-server').exists() or Path('/app/static').exists():
            return Path('/app')

        # Traditional Docker deployment: /app/backend structure
        if Path('/app/backend').exists():
            return Path('/app')

        # backend/config/paths.py -> backend -> web -> ui -> src -> flyto-cloud
        current = Path(__file__).resolve()
        cloud_root = current.parent.parent.parent.parent.parent.parent

        # Verify by checking for characteristic files
        if (cloud_root / 'src' / 'ui' / 'web' / 'backend').exists():
            return cloud_root

        # Fallback: search upward for flyto-cloud marker
        for parent in current.parents:
            if (parent / 'src' / 'ui' / 'web' / 'backend').exists():
                return parent

        raise RuntimeError('Could not find flyto-cloud root directory')


# Singleton instance
_resolver: Optional[PathResolver] = None


def get_path_resolver() -> PathResolver:
    """Get or create path resolver singleton"""
    global _resolver
    if _resolver is None:
        _resolver = PathResolver()
    return _resolver
