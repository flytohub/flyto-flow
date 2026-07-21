"""
Hot Updater Version Checking

Version checking and comparison utilities.
Uses PyPI JSON API for flyto-core versions.
"""

import logging
import random
import asyncio
from typing import Any, Dict, Optional

import aiohttp

from services.infra.updater.constants import PYPI_API_URL, PYPI_PACKAGE_NAME, utc_now
from services.infra.updater.models import CoreVersion

logger = logging.getLogger(__name__)


def compare_versions(v1: str, v2: str) -> int:
    """
    Compare semantic versions.
    Returns: 1 if v1 > v2, -1 if v1 < v2, 0 if equal
    """
    def normalize(v):
        v = v.lstrip('v')
        parts = []
        for part in v.split('.'):
            try:
                parts.append(int(part.split('-')[0].split('+')[0]))
            except ValueError:
                parts.append(0)
        return parts

    p1, p2 = normalize(v1), normalize(v2)

    max_len = max(len(p1), len(p2))
    p1.extend([0] * (max_len - len(p1)))
    p2.extend([0] * (max_len - len(p2)))

    for a, b in zip(p1, p2):
        if a > b:
            return 1
        if a < b:
            return -1
    return 0


async def check_pypi_latest(max_retries: int = 3) -> Optional[str]:
    """
    Get latest version string from PyPI.

    Returns:
        Version string (e.g., "1.2.3") or None if failed
    """
    timeout = aiohttp.ClientTimeout(total=10, connect=5)
    last_error = None

    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(PYPI_API_URL) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("info", {}).get("version")
                    elif resp.status >= 500:
                        last_error = "PyPI returned {}".format(resp.status)
                        logger.warning("PyPI returned %d, retry %d/%d", resp.status, attempt + 1, max_retries)
                    else:
                        return None

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            last_error = str(e)
            logger.warning("PyPI request failed (attempt %d/%d): %s", attempt + 1, max_retries, e)

        if attempt < max_retries - 1:
            delay = (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(delay)

    logger.error("Error fetching PyPI version after %d attempts: %s", max_retries, last_error)
    return None


async def get_pypi_wheel_info(version: Optional[str] = None) -> Optional[CoreVersion]:
    """
    Get wheel download URL and SHA256 from PyPI JSON API.

    Args:
        version: Specific version to look up. If None, uses latest.

    Returns:
        CoreVersion with download_url, filename, sha256_digest, or None if failed
    """
    try:
        if version:
            url = "https://pypi.org/pypi/{}/{}/json".format(PYPI_PACKAGE_NAME, version)
        else:
            url = PYPI_API_URL

        timeout = aiohttp.ClientTimeout(total=15, connect=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.warning("PyPI API returned %d for wheel info", resp.status)
                    return None

                data = await resp.json()
                info = data.get("info", {})
                ver = info.get("version", "")
                urls = data.get("urls", [])

                # Prefer bdist_wheel, fallback to sdist
                wheel_info = None
                for u in urls:
                    if u.get("packagetype") == "bdist_wheel":
                        wheel_info = u
                        break

                if not wheel_info:
                    # Fallback to any available distribution
                    for u in urls:
                        if u.get("packagetype") == "sdist":
                            wheel_info = u
                            break

                if not wheel_info:
                    logger.warning("No wheel or sdist found for %s %s", PYPI_PACKAGE_NAME, ver)
                    return None

                digests = wheel_info.get("digests", {})
                sha256 = digests.get("sha256", "")

                return CoreVersion(
                    version=ver,
                    download_url=wheel_info["url"],
                    filename=wheel_info["filename"],
                    sha256_digest=sha256,
                    published_at=wheel_info.get("upload_time_iso_8601", ""),
                )

    except aiohttp.ClientError as e:
        logger.error("Network error fetching PyPI wheel info: %s", e)
        return None
    except Exception as e:
        logger.error("Error fetching PyPI wheel info: %s", e)
        return None


async def check_for_updates(
    config: Dict[str, Any],
    current_version: Optional[str],
    force: bool = False
) -> Optional[CoreVersion]:
    """
    Check PyPI for new flyto-core releases.

    Args:
        config: User configuration dict
        current_version: Currently installed version
        force: Skip cache and check immediately

    Returns:
        CoreVersion if update available, None otherwise
    """
    from datetime import timedelta, datetime

    # Check if we should skip (already checked recently)
    if not force and config.get("last_check"):
        last_check = datetime.fromisoformat(config["last_check"])
        interval = timedelta(hours=config.get("check_interval_hours", 1))
        if utc_now() - last_check < interval:
            logger.debug("Skipping update check (checked recently)")
            return None

    logger.info("Checking for flyto-core updates on PyPI...")

    try:
        latest_version = await check_pypi_latest()
        if not latest_version:
            return None

        # Check if update is needed
        if current_version and compare_versions(latest_version, current_version) <= 0:
            logger.info("Already on latest version: %s", current_version)
            return None

        # Check version pin
        pinned = config.get("pinned_version")
        if pinned and compare_versions(latest_version, pinned) > 0:
            logger.info("Version pinned at %s, skipping %s", pinned, latest_version)
            return None

        # Get wheel info for download
        core_version = await get_pypi_wheel_info(latest_version)
        if not core_version:
            logger.warning("Could not get wheel info for %s", latest_version)
            return None

        logger.info("Update available: %s -> %s", current_version, latest_version)
        return core_version

    except Exception as e:
        logger.error("Error checking for updates: %s", e)
        return None
