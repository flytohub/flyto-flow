#!/usr/bin/env python3
"""Verify Signed-off-by trailers for every commit in a Git revision range."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys


SIGNOFF_RE = re.compile(r"(?mi)^Signed-off-by:\s+.+\s+<[^<>\s]+@[^<>\s]+>\s*$")


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="exclusive base revision")
    parser.add_argument("--head", default="HEAD", help="inclusive head revision")
    args = parser.parse_args()

    commits = _git("rev-list", "--reverse", f"{args.base}..{args.head}").splitlines()
    missing = []
    for commit in commits:
        message = _git("show", "-s", "--format=%B", commit)
        if not SIGNOFF_RE.search(message):
            subject = _git("show", "-s", "--format=%s", commit)
            missing.append(f"{commit[:12]} {subject}")

    if missing:
        print("DCO check failed; commits missing a valid Signed-off-by trailer:", file=sys.stderr)
        for item in missing:
            print(f"  {item}", file=sys.stderr)
        return 1

    print(f"DCO check passed for {len(commits)} commit(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
