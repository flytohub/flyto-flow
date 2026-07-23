#!/usr/bin/env python3
"""Verify direct CE dependencies remain exactly pinned in the hash lock."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PIN_PATTERN = re.compile(
    r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]+\])?=="
    r"(?P<version>[A-Za-z0-9][A-Za-z0-9.!+_-]*)$"
)
LOCK_PATTERN = re.compile(
    r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)=="
    r"(?P<version>[A-Za-z0-9][A-Za-z0-9.!+_-]*)\s*(?:\\)?$"
)


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def check(input_path: Path, lock_path: Path) -> list[str]:
    failures: list[str] = []
    direct: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        input_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = PIN_PATTERN.fullmatch(line)
        if not match:
            failures.append(
                f"{input_path}: line {line_number} is not an exact NAME==VERSION pin"
            )
            continue
        name = _normalize(match.group("name"))
        if name in direct:
            failures.append(f"{input_path}: duplicate direct dependency {name}")
        direct[name] = match.group("version")

    locked: dict[str, str] = {}
    for raw_line in lock_path.read_text(encoding="utf-8").splitlines():
        match = LOCK_PATTERN.fullmatch(raw_line.strip())
        if match:
            locked[_normalize(match.group("name"))] = match.group("version")

    for name, version in sorted(direct.items()):
        locked_version = locked.get(name)
        if locked_version is None:
            failures.append(f"{name} is pinned in the input but absent from the lock")
        elif locked_version != version:
            failures.append(
                f"{name} input version {version} does not match lock {locked_version}"
            )

    if "--generate-hashes" not in lock_path.read_text(encoding="utf-8"):
        failures.append(f"{lock_path} does not record hash generation")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=Path("src/ui/web/backend/requirements-ce.in"),
    )
    parser.add_argument(
        "lock",
        nargs="?",
        type=Path,
        default=Path("src/ui/web/backend/requirements-ce.lock"),
    )
    args = parser.parse_args()
    failures = check(args.input.resolve(), args.lock.resolve())
    if failures:
        print("Dependency lock contract failed:", file=sys.stderr)
        for failure in failures:
            print(f" - {failure}", file=sys.stderr)
        return 1
    print("Dependency lock contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
