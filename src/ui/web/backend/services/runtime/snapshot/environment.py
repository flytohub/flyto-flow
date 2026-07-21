"""
Environment Capture

Functions for capturing environment and dependency information.
"""

import logging
import os
import platform
import subprocess
import sys
from typing import Dict

from services.runtime.snapshot.models import EnvironmentSnapshot

logger = logging.getLogger(__name__)


def get_environment_snapshot() -> EnvironmentSnapshot:
    """
    Capture current environment information.

    Returns:
        EnvironmentSnapshot with OS, Python, and Flyto2 version info
    """
    flyto_version = "unknown"
    try:
        import importlib.metadata
        flyto_version = importlib.metadata.version("flyto-core")
    except Exception:
        pass

    return EnvironmentSnapshot(
        os_name=platform.system(),
        os_version=platform.release(),
        python_version=platform.python_version(),
        flyto_version=flyto_version,
        hostname=platform.node(),
        working_directory=os.getcwd(),
    )


def collect_dependencies(full_snapshot: bool = True) -> Dict[str, Dict[str, str]]:
    """
    Collect installed package versions.

    Args:
        full_snapshot: If True, capture ALL installed packages.
                       If False, only capture key packages.

    Returns:
        Dictionary of package names to version info
    """
    dependencies = {}

    try:
        import importlib.metadata

        if full_snapshot:
            # Capture ALL installed packages
            try:
                for dist in importlib.metadata.distributions():
                    try:
                        name = dist.metadata["Name"]
                        version = dist.version
                        if name and version:
                            dependencies[name.lower()] = {"version": version}
                    except Exception:
                        continue
            except Exception as e:
                logger.warning(f"Failed to enumerate all packages: {e}")
                # Fallback to pip freeze
                _collect_via_pip_freeze(dependencies)
        else:
            # Get key packages that affect execution
            key_packages = [
                "playwright",
                "aiohttp",
                "pydantic",
                "pyyaml",
                "httpx",
                "fastapi",
                "flyto-core",
                "openai",
                "anthropic",
            ]

            for pkg in key_packages:
                try:
                    version = importlib.metadata.version(pkg)
                    dependencies[pkg] = {"version": version}
                except importlib.metadata.PackageNotFoundError:
                    pass

    except Exception as e:
        logger.warning(f"Failed to collect dependencies: {e}")

    return dependencies


def _collect_via_pip_freeze(dependencies: Dict[str, Dict[str, str]]) -> None:
    """
    Fallback method to collect dependencies via pip freeze.

    Args:
        dependencies: Dictionary to populate with package info
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if "==" in line:
                    name, version = line.split("==", 1)
                    dependencies[name.lower()] = {"version": version}
    except Exception as e:
        logger.warning(f"Failed to run pip freeze: {e}")
