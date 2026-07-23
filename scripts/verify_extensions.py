#!/usr/bin/env python3
"""Verify Flyto2 extension manifests, artifact digests, and signatures."""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "src/ui/web/backend"
sys.path.insert(0, str(BACKEND))

from services.extensions.manifest import ExtensionPolicy, discover_extensions
from services.extensions.templates import load_template_packs


def _trusted_keys() -> dict[str, str]:
    raw = os.environ.get("FLYTO_EXTENSION_TRUSTED_KEYS", "").strip()
    if not raw:
        return {}
    parsed = json.loads(raw)
    if not isinstance(parsed, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in parsed.items()
    ):
        raise ValueError("FLYTO_EXTENSION_TRUSTED_KEYS must be a JSON object")
    for value in parsed.values():
        base64.b64decode(value, validate=True)
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=str(ROOT / "extensions"))
    parser.add_argument(
        "--allow-unsigned",
        action="store_true",
        help="Allow unsigned development bundles; production should omit this option.",
    )
    args = parser.parse_args()
    policy = (
        ExtensionPolicy.ALLOW_UNSIGNED
        if args.allow_unsigned
        else ExtensionPolicy.REQUIRE_SIGNATURE
    )
    try:
        extensions = discover_extensions(
            Path(args.root).resolve(),
            policy=policy,
            trusted_keys=_trusted_keys(),
        )
        load_template_packs(extensions)
    except Exception as exc:
        print(f"Extension verification failed: {exc}", file=sys.stderr)
        return 1
    for extension in extensions:
        print(
            f"{extension.manifest.id}@{extension.manifest.version} "
            f"kind={extension.manifest.kind.value} signed={extension.signed}"
        )
    print(f"Verified {len(extensions)} extension bundle(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
