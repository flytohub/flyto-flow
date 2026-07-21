"""
GitHub Service for Translation Management.

Provides async functions for interacting with the flyto-i18n GitHub repository:
file listing, content retrieval, branch/PR creation, and file updates.
"""

import asyncio
import base64
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException

env_path = Path(__file__).parent.parent.parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
FLYTO_I18N_REPO = os.getenv("FLYTO_I18N_REPO", "flytohub/flyto-i18n")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# =============================================================================
# Cache
# =============================================================================

_github_cache: Dict[str, Any] = {}
_cache_ttl = 300  # 5 minutes


# Bounded retry/backoff for flaky GitHub API calls (rate limits + transient 5xx).
_RETRY_MAX_ATTEMPTS = 3
_RETRY_BASE_DELAY = 1.0  # seconds; doubled each attempt (1s, 2s, ...)
_RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})


async def _request_with_retry(
    send: Callable[[httpx.AsyncClient], Awaitable[httpx.Response]]
) -> httpx.Response:
    """Run an httpx request with bounded exponential backoff.

    Retries on connection/timeout errors and on retryable status codes
    (429 + 5xx). Returns the final response (success or last attempt) for the
    caller to inspect; raising/normal handling stays in the caller so existing
    status-code logic is unchanged.
    """
    last_exc: Exception | None = None
    response: httpx.Response | None = None

    for attempt in range(_RETRY_MAX_ATTEMPTS):
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await send(client)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_exc = exc
                response = None
            else:
                if response.status_code not in _RETRYABLE_STATUSES:
                    return response

        # Last attempt: return whatever we have, or re-raise the transport error.
        if attempt == _RETRY_MAX_ATTEMPTS - 1:
            if response is not None:
                return response
            raise last_exc  # type: ignore[misc]

        delay = _RETRY_BASE_DELAY * (2 ** attempt)
        logger.warning(
            "GitHub request failed (attempt %d/%d), retrying in %.1fs",
            attempt + 1, _RETRY_MAX_ATTEMPTS, delay
        )
        await asyncio.sleep(delay)

    # Unreachable, but keeps type checkers happy.
    return response  # type: ignore[return-value]


# =============================================================================
# GitHub API Functions
# =============================================================================


async def github_get(path: str, use_cache: bool = True) -> dict:
    """Make a GitHub API request."""
    cache_key = f"github:{path}"
    now = time.time()

    if use_cache and cache_key in _github_cache:
        cached = _github_cache[cache_key]
        if cached["expires"] > now:
            return cached["data"]

    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GitHub token not configured")

    url = f"https://api.github.com/repos/{FLYTO_I18N_REPO}/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = await _request_with_retry(
        lambda client: client.get(url, headers=headers)
    )
    if response.status_code != 200:
        logger.error(f"GitHub API error: {response.status_code} - {response.text}")
        raise HTTPException(
            status_code=response.status_code,
            detail=f"GitHub API error: {response.text}"
        )
    data = response.json()

    if use_cache:
        _github_cache[cache_key] = {"data": data, "expires": now + _cache_ttl}

    return data


async def github_get_file_content(locale: str, filename: str) -> dict:
    """Get content of a translation file from GitHub."""
    path = f"contents/locales/{locale}/{filename}"
    data = await github_get(path, use_cache=False)

    if data.get("encoding") == "base64":
        content = base64.b64decode(data["content"]).decode("utf-8")
        return {
            "sha": data["sha"],
            "content": json.loads(content)
        }
    return {"sha": None, "content": {}}


async def github_list_files(locale: str) -> List[dict]:
    """List all JSON files in a locale directory."""
    path = f"contents/locales/{locale}"
    try:
        files = await github_get(path)
        return [f for f in files if f["name"].endswith(".json")]
    except HTTPException as e:
        if e.status_code == 404:
            return []
        raise


async def github_create_branch(branch_name: str, base_sha: str) -> bool:
    """Create a new branch from the given SHA."""
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GitHub token not configured")

    url = f"https://api.github.com/repos/{FLYTO_I18N_REPO}/git/refs"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "ref": f"refs/heads/{branch_name}",
        "sha": base_sha
    }

    response = await _request_with_retry(
        lambda client: client.post(url, headers=headers, json=payload)
    )
    if response.status_code in [201, 422]:  # 422 = already exists
        return True
    logger.error(f"Create branch error: {response.status_code} - {response.text}")
    return False


async def github_update_file(
    filepath: str,
    content: str,
    message: str,
    sha: str,
    branch: str
) -> dict:
    """Update or create a file in the repository."""
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GitHub token not configured")

    url = f"https://api.github.com/repos/{FLYTO_I18N_REPO}/contents/{filepath}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": branch
    }
    if sha:
        payload["sha"] = sha

    response = await _request_with_retry(
        lambda client: client.put(url, headers=headers, json=payload)
    )
    if response.status_code not in [200, 201]:
        logger.error(f"Update file error: {response.status_code} - {response.text}")
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to update file: {response.text}"
        )
    return response.json()


async def github_create_pr(
    title: str,
    body: str,
    head_branch: str,
    base_branch: str = "main"
) -> dict:
    """Create a pull request."""
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GitHub token not configured")

    url = f"https://api.github.com/repos/{FLYTO_I18N_REPO}/pulls"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "title": title,
        "body": body,
        "head": head_branch,
        "base": base_branch
    }

    response = await _request_with_retry(
        lambda client: client.post(url, headers=headers, json=payload)
    )
    if response.status_code != 201:
        logger.error(f"Create PR error: {response.status_code} - {response.text}")
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to create PR: {response.text}"
        )
    return response.json()


async def github_get_pr(pr_number: int) -> dict:
    """Get PR details."""
    path = f"pulls/{pr_number}"
    return await github_get(path, use_cache=False)


async def github_list_prs(state: str = "open") -> List[dict]:
    """List pull requests."""
    path = f"pulls?state={state}"
    return await github_get(path, use_cache=False)


async def github_get_main_sha() -> str:
    """Get the SHA of the main branch."""
    path = "git/refs/heads/main"
    data = await github_get(path, use_cache=False)
    return data["object"]["sha"]


# =============================================================================
# Translation Helpers
# =============================================================================


def calculate_stats(en_content: dict, locale_content: dict) -> dict:
    """Calculate translation statistics."""
    en_translations = en_content.get("translations", {})
    locale_translations = locale_content.get("translations", {})

    total = len(en_translations)
    translated = sum(1 for k in en_translations if locale_translations.get(k))

    return {
        "key_count": total,
        "translated_count": translated,
        "completion": round((translated / total * 100) if total > 0 else 0, 1)
    }
