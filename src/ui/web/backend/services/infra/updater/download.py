"""
Hot Updater Download

Download and install flyto-core from PyPI wheel.
"""

import hashlib
import shutil
import zipfile
import logging
import platform
from pathlib import Path
from typing import Optional

import aiohttp

from services.infra.updater.models import CoreVersion

logger = logging.getLogger(__name__)


async def download_version(
    version: CoreVersion,
    core_dir: Path,
    cache_dir: Path
) -> Optional[Path]:
    """
    Download a flyto-core wheel from PyPI and extract it.

    .whl files are standard zip archives. We download, verify SHA256,
    then extract the `core/` package directory to ~/.flyto/core/{version}/.

    Args:
        version: CoreVersion with download_url and sha256_digest
        core_dir: Directory for core versions (~/.flyto/core/)
        cache_dir: Directory for temporary downloads (~/.flyto/cache/)

    Returns:
        Path to extracted version directory, or None if failed
    """
    logger.info("Downloading flyto-core %s from PyPI...", version.version)

    target_dir = core_dir / version.version
    if target_dir.exists():
        logger.info("Version %s already downloaded", version.version)
        return target_dir

    try:
        timeout = aiohttp.ClientTimeout(total=300, connect=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(version.download_url) as resp:
                if resp.status != 200:
                    logger.error("Failed to download: HTTP %d", resp.status)
                    return None

                whl_path = cache_dir / version.filename
                sha256 = hashlib.sha256()

                with open(whl_path, 'wb') as f:
                    while True:
                        chunk = await resp.content.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        sha256.update(chunk)

        # Verify SHA256
        if version.sha256_digest:
            actual_hash = sha256.hexdigest()
            if actual_hash != version.sha256_digest:
                logger.error(
                    "SHA256 mismatch! Expected %s, got %s",
                    version.sha256_digest, actual_hash
                )
                whl_path.unlink(missing_ok=True)
                return None
            logger.info("SHA256 verified: %s", actual_hash[:16])

        # Extract wheel (.whl is a zip)
        temp_dir = cache_dir / "extract_{}".format(version.version)
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

        with zipfile.ZipFile(whl_path, 'r') as zf:
            zf.extractall(temp_dir)

        # Find the core package directory inside the wheel
        # Wheel layout: core/ (the package), *.dist-info/
        core_pkg = temp_dir / "core"
        if not core_pkg.exists():
            # Try alternative: package might be under a different name
            for item in temp_dir.iterdir():
                if item.is_dir() and not item.name.endswith('.dist-info'):
                    core_pkg = item
                    break

        if not core_pkg.exists():
            logger.error("Could not find core package in wheel")
            shutil.rmtree(temp_dir, ignore_errors=True)
            whl_path.unlink(missing_ok=True)
            return None

        # Move to final location
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(core_pkg, target_dir / "core", dirs_exist_ok=True)

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        whl_path.unlink(missing_ok=True)

        logger.info("Successfully installed flyto-core %s", version.version)
        return target_dir

    except Exception as e:
        logger.error("Error downloading %s: %s", version.version, e)
        # Cleanup partial downloads
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        return None


def install_symlink(
    version: str,
    core_dir: Path
) -> bool:
    """
    Activate a version by creating symlink (Unix) or pointer file (Windows).

    Args:
        version: Version string (e.g., "1.0.0")
        core_dir: Directory for core versions

    Returns:
        True if successful
    """
    version_dir = core_dir / version
    if not version_dir.exists():
        logger.error("Version %s not downloaded", version)
        return False

    current_link = core_dir / "current"

    try:
        if platform.system() == "Windows":
            return _install_pointer_file(version, core_dir)

        # Unix: use symlink
        if current_link.exists() or current_link.is_symlink():
            current_link.unlink()

        current_link.symlink_to(version_dir)
        logger.info("Created symlink to %s", version)
        return True

    except OSError:
        # Symlink failed (e.g., permissions) — fallback to pointer file
        logger.warning("Symlink failed, using pointer file fallback")
        return _install_pointer_file(version, core_dir)


def _install_pointer_file(version: str, core_dir: Path) -> bool:
    """
    Windows fallback: write active version to current.txt.

    Args:
        version: Version string
        core_dir: Directory for core versions

    Returns:
        True if successful
    """
    pointer_file = core_dir / "current.txt"
    try:
        pointer_file.write_text(version, encoding="utf-8")
        logger.info("Created pointer file for %s", version)
        return True
    except Exception as e:
        logger.error("Error creating pointer file for %s: %s", version, e)
        return False


def resolve_current_path(core_dir: Path) -> Optional[Path]:
    """
    Resolve the active core version path.

    Checks symlink first, then pointer file (Windows fallback).

    Returns:
        Path to active version directory, or None
    """
    current_link = core_dir / "current"

    # Try symlink first
    if current_link.is_symlink():
        target = current_link.resolve()
        if target.exists():
            return target

    # Try pointer file (Windows fallback)
    pointer_file = core_dir / "current.txt"
    if pointer_file.exists():
        version = pointer_file.read_text(encoding="utf-8").strip()
        version_dir = core_dir / version
        if version_dir.exists():
            return version_dir

    return None
