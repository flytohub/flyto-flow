#!/usr/bin/env python3
"""Validate Flyto2 Flow source-available licensing and contribution policy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


HISTORICAL_APACHE_BOUNDARY = "9398a622a2b53bde6df5e661d71735d1cefdbabc"


def check(root: Path) -> list[str]:
    failures: list[str] = []
    required = (
        "LICENSE",
        "LICENSE_HISTORY.md",
        "COMMERCIAL_LICENSE.md",
        "CONTRIBUTOR_LICENSE_AGREEMENT.md",
        "TRADEMARKS.md",
        "FLOW_CLOUD_SYNC.json",
    )
    for relative in required:
        if not (root / relative).is_file():
            failures.append(f"missing licensing file: {relative}")

    license_path = root / "LICENSE"
    if license_path.is_file():
        body = license_path.read_text(encoding="utf-8")
        for marker in (
            "Required Notice: Copyright 2024-2026 Flyto2 Team.",
            "Licensor Line of Business:",
            "# PolyForm Shield License 1.0.0",
            "## Noncompete",
            "Any purpose is a permitted purpose, except for providing any product that competes",
        ):
            if marker not in body:
                failures.append(f"LICENSE is missing required marker: {marker}")
        if "Apache License\n" in body or "Apache License\r\n" in body:
            failures.append("current LICENSE still contains Apache License terms")

    history_path = root / "LICENSE_HISTORY.md"
    if history_path.is_file():
        history = history_path.read_text(encoding="utf-8")
        if HISTORICAL_APACHE_BOUNDARY not in history:
            failures.append("LICENSE_HISTORY.md lacks the exact Apache boundary commit")
        if "not retroactive" not in history:
            failures.append("LICENSE_HISTORY.md must state that the change is not retroactive")

    readme_path = root / "README.md"
    if readme_path.is_file():
        readme = readme_path.read_text(encoding="utf-8").lower()
        if "source-available" not in readme or "polyform shield" not in readme:
            failures.append("README must identify the current source-available license")
        if "is an open-source" in readme:
            failures.append("README must not market the restricted license as open source")

    contributing_path = root / "CONTRIBUTING.md"
    if contributing_path.is_file():
        contributing = contributing_path.read_text(encoding="utf-8")
        if "Flyto2-CLA: accepted" not in contributing:
            failures.append("CONTRIBUTING.md lacks explicit CLA acceptance")

    sync_path = root / "FLOW_CLOUD_SYNC.json"
    if sync_path.is_file():
        try:
            sync = json.loads(sync_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"FLOW_CLOUD_SYNC.json is invalid: {exc}")
        else:
            policy = sync.get("license_policy", {})
            if policy.get("flow") != "PolyForm-Shield-1.0.0":
                failures.append("sync contract has the wrong Flow license")
            if policy.get("cloud") != "Flyto2-Source-Available-1.1":
                failures.append("sync contract has the wrong Cloud license")
            if policy.get("historical_flow_boundary") != HISTORICAL_APACHE_BOUNDARY:
                failures.append("sync contract has the wrong historical license boundary")

    return sorted(set(failures))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    root = Path(parser.parse_args().root).resolve()
    failures = check(root)
    if failures:
        print("Flyto2 Flow license policy failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1
    print("Flyto2 Flow license policy passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
