"""
Hot Updater Constants

PyPI (core) and GitHub (frontend) configuration.
"""

from datetime import timedelta, timezone
from datetime import datetime


# PyPI (flyto-core hot update)
PYPI_PACKAGE_NAME = "flyto-core"
PYPI_API_URL = "https://pypi.org/pypi/flyto-core/json"

# GitHub (frontend hot update + app version check)
GITHUB_OWNER = "flytohub"
GITHUB_REPO = "flyto2"
GITHUB_API_BASE = "https://api.github.com"

# Update check interval
UPDATE_CHECK_INTERVAL = timedelta(hours=1)


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)
