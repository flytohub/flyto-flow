"""Resolve the application version from the repository release contract."""

from __future__ import annotations

import os
import re
from pathlib import Path


SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def _version_candidates() -> list[Path]:
    configured = os.environ.get("FLYTO_VERSION_FILE", "").strip()
    candidates = [Path(configured).expanduser()] if configured else []
    candidates.append(Path("/app/VERSION"))
    candidates.extend(
        parent / "VERSION" for parent in Path(__file__).resolve().parents
    )
    return list(dict.fromkeys(candidates))


def read_app_version() -> str:
    """Read and validate the first available authoritative VERSION file."""
    for candidate in _version_candidates():
        if not candidate.is_file():
            continue
        version = candidate.read_text(encoding="utf-8").strip()
        if not SEMVER_PATTERN.fullmatch(version):
            raise RuntimeError(f"Invalid semantic version in {candidate}: {version!r}")
        return version
    checked = ", ".join(str(candidate) for candidate in _version_candidates())
    raise RuntimeError(f"Flyto2 Flow VERSION file not found; checked: {checked}")


APP_VERSION = read_app_version()
