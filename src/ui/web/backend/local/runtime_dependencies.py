"""Fail-fast checks for dependencies baked into the CE artifact.

This module never installs or downloads anything. The image build owns initial
provisioning; runtime only verifies that the artifact is complete.
"""

from __future__ import annotations

import os
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


REQUIRED_PACKAGES = ("flyto-core", "playwright")


def verify_bundled_runtime() -> None:
    """Raise a clear error when a production CE image is incomplete."""
    if os.getenv("FLYTO_REQUIRE_BUNDLED_RUNTIME") != "1":
        return

    missing: list[str] = []
    for package in REQUIRED_PACKAGES:
        try:
            version(package)
        except PackageNotFoundError:
            missing.append(package)

    browser_root = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/ms-playwright"))
    browser_candidates = (
        list(browser_root.glob("chromium-*/chrome-linux/chrome"))
        + list(browser_root.glob("chromium-*/chrome-linux64/chrome"))
        + list(browser_root.glob("chromium-*/chrome-win/chrome.exe"))
        + list(browser_root.glob("chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell"))
    )
    if not any(path.is_file() for path in browser_candidates):
        missing.append("chromium")
    if os.getenv("HEADLESS", "").lower() not in {"1", "true", "yes"}:
        missing.append("HEADLESS=1")

    if missing:
        raise RuntimeError(
            "Incomplete CE artifact: "
            + ", ".join(missing)
            + " must be installed during image build; runtime downloads are disabled"
        )
