#!/usr/bin/env python3
"""Verify every release surface uses the root VERSION value."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def check(root: Path, expected_tag: str | None = None) -> list[str]:
    failures: list[str] = []
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not SEMVER_PATTERN.fullmatch(version):
        failures.append(f"VERSION is not strict SemVer: {version!r}")

    for relative in (
        "src/ui/web/frontend/package.json",
        "src/ui/web/frontend/package-lock.json",
    ):
        data = json.loads((root / relative).read_text(encoding="utf-8"))
        if data.get("version") != version:
            failures.append(f"{relative} version {data.get('version')!r} != {version!r}")
        root_package = data.get("packages", {}).get("")
        if root_package is not None and root_package.get("version") != version:
            failures.append(
                f"{relative} root package version {root_package.get('version')!r} != {version!r}"
            )

    if expected_tag and expected_tag != f"v{version}":
        failures.append(f"release tag {expected_tag!r} does not match VERSION v{version}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--tag")
    args = parser.parse_args()
    failures = check(Path(args.root).resolve(), args.tag)
    if failures:
        print("Version contract failed:", file=sys.stderr)
        for failure in failures:
            print(f" - {failure}", file=sys.stderr)
        return 1
    print("Version contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
