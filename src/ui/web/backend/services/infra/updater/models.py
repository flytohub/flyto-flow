"""
Hot Updater Models

Dataclasses for version and update status.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CoreVersion:
    """Represents a flyto-core version from PyPI."""
    version: str
    download_url: str
    filename: str
    sha256_digest: str
    published_at: str = ""
    release_notes: str = ""
    is_prerelease: bool = False


@dataclass
class FrontendVersion:
    """Represents a frontend release from GitHub."""
    version: str
    download_url: str
    published_at: str = ""


@dataclass
class UpdateStatus:
    """Current update status for all components."""
    # Core (PyPI wheel)
    core_current: str = "not installed"
    core_latest: str = "unknown"
    core_update_available: bool = False
    # Frontend (GitHub release asset)
    frontend_current: str = "unknown"
    frontend_latest: str = "unknown"
    frontend_update_available: bool = False
    # App (overall desktop binary)
    app_version: str = "unknown"
    app_update_available: bool = False
    # Meta
    last_check: str = "never"
    auto_update: bool = True
