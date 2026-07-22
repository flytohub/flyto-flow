"""Path resolution for Flyto2 Flow without relying on a repository name."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional


class PathResolver:
    """Resolve packaged, container, and source-tree paths from local markers."""

    def __init__(self):
        self._project_root: Optional[Path] = None

    @property
    def project_root(self) -> Path:
        if self._project_root is None:
            self._project_root = self._find_project_root()
        return self._project_root

    @property
    def is_docker(self) -> bool:
        return Path("/app/backend").is_dir() or Path("/app/static").is_dir()

    @property
    def backend_root(self) -> Path:
        if Path("/app/backend").is_dir():
            return Path("/app/backend")
        return self.project_root / "src" / "ui" / "web" / "backend"

    @property
    def frontend_root(self) -> Path:
        if self.is_docker:
            return Path("/app/static")
        return self.project_root / "src" / "ui" / "web" / "frontend"

    @property
    def frontend_dist(self) -> Path:
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            packaged = Path(sys._MEIPASS) / "static"
            if packaged.is_dir():
                return packaged
        if self.is_docker:
            return Path("/app/static")
        return self.frontend_root / "dist"

    @staticmethod
    def _is_project_root(path: Path) -> bool:
        return (
            (path / "src" / "ui" / "web" / "backend").is_dir()
            and (path / "src" / "ui" / "web" / "frontend").is_dir()
            and (path / "install").is_dir()
        )

    def _find_project_root(self) -> Path:
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)
        if self.is_docker:
            return Path("/app")
        for candidate in Path(__file__).resolve().parents:
            if self._is_project_root(candidate):
                return candidate
        raise RuntimeError("Could not find the Flyto2 Flow project root")


_resolver: Optional[PathResolver] = None


def get_path_resolver() -> PathResolver:
    global _resolver
    if _resolver is None:
        _resolver = PathResolver()
    return _resolver
