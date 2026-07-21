"""
Validation and registry helpers for packages — PyPI version checks.
"""

import logging
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


async def _check_pypi_latest(pypi_url: str) -> Optional[str]:
    """Fetch latest version from a PyPI JSON endpoint."""
    if not pypi_url:
        return None
    try:
        timeout = aiohttp.ClientTimeout(total=10, connect=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(pypi_url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("info", {}).get("version")
    except Exception as e:
        logger.debug("PyPI check failed for %s: %s", pypi_url, e)
    return None
