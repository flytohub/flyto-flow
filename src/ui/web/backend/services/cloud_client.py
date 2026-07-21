"""Disabled hosted-client compatibility surface for CE-only code paths."""

from typing import Any, Dict, Optional


async def cloud_get(
    path: str,
    params: Optional[Dict[str, Any]] = None,
    auth_header: Optional[str] = None,
) -> None:
    del path, params, auth_header
    return None


async def cloud_post(
    path: str,
    json: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    auth_header: Optional[str] = None,
) -> None:
    del path, json, params, auth_header
    return None


async def cloud_put(
    path: str,
    json: Optional[Dict[str, Any]] = None,
    auth_header: Optional[str] = None,
) -> None:
    del path, json, auth_header
    return None
