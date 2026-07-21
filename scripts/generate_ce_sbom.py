#!/usr/bin/env python3
"""Generate a deterministic CycloneDX SBOM for a Flyto2 Cloud CE release tree."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
from urllib.parse import quote

from packaging.utils import canonicalize_name

from audit_ce_dependencies import _load_overrides, _locked_requirements, _python_dependencies


def _npm_components(root: Path) -> list[dict]:
    lock = json.loads((root / "src/ui/web/frontend/package-lock.json").read_text(encoding="utf-8"))
    components = []
    for package_path, package in sorted(lock.get("packages", {}).items()):
        if not package_path:
            continue
        name = str(package.get("name") or package_path.rsplit("node_modules/", 1)[-1])
        version = str(package.get("version") or "unknown")
        component = {
            "type": "library",
            "bom-ref": f"pkg:npm/{quote(name, safe='@/')}@{quote(version, safe='')}",
            "name": name,
            "version": version,
            "purl": f"pkg:npm/{quote(name, safe='@/')}@{quote(version, safe='')}",
        }
        license_name = package.get("license")
        if license_name:
            component["licenses"] = [{"expression": str(license_name)}]
        integrity = str(package.get("integrity") or "")
        if integrity.startswith("sha512-"):
            try:
                digest = base64.b64decode(integrity[7:]).hex()
                component["hashes"] = [{"alg": "SHA-512", "content": digest}]
            except ValueError:
                pass
        components.append(component)
    return components


def _python_components(root: Path, *, installed_closure: bool) -> list[dict]:
    components = []
    if installed_closure:
        for _, name, version, license_name in _python_dependencies(root, _load_overrides(root)):
            normalized = canonicalize_name(name)
            purl = f"pkg:pypi/{quote(normalized, safe='')}@{quote(version, safe='')}"
            components.append(
                {
                    "type": "library",
                    "bom-ref": purl,
                    "name": name,
                    "version": version,
                    "purl": purl,
                    "licenses": [{"expression": license_name}],
                }
            )
        return components

    lock_path = root / "src/ui/web/backend/requirements-ce.lock"
    for requirement in _locked_requirements(lock_path):
        name = canonicalize_name(requirement.name)
        version = str(requirement.specifier).removeprefix("==") or "unresolved"
        purl = f"pkg:pypi/{quote(name, safe='')}@{quote(version, safe='') }"
        components.append(
            {
                "type": "library",
                "bom-ref": purl,
                "name": requirement.name,
                "version": version,
                "purl": purl,
                "properties": [
                    {"name": "flyto:declared_constraint", "value": str(requirement.specifier) or "*"}
                ],
            }
        )
    return components


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="generated CE tree")
    parser.add_argument("--output", default="sbom.cdx.json")
    parser.add_argument(
        "--python-installed",
        action="store_true",
        help="include the installed transitive Python dependency closure",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve()
    release = json.loads((root / "CE_EXPORT.json").read_text(encoding="utf-8"))
    components = _npm_components(root) + _python_components(
        root,
        installed_closure=args.python_installed,
    )
    components.sort(key=lambda item: item["bom-ref"])
    serial_seed = f"{release['source_commit']}:{release['tree_sha256']}".encode("utf-8")
    serial_hex = hashlib.sha256(serial_seed).hexdigest()[:32]
    serial = f"urn:uuid:{serial_hex[:8]}-{serial_hex[8:12]}-4{serial_hex[13:16]}-a{serial_hex[17:20]}-{serial_hex[20:32]}"
    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": serial,
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "bom-ref": "pkg:github/flytohub/flyto-cloud-ce",
                "name": "flyto-cloud-ce",
                "version": release["source_commit"][:12],
            },
            "properties": [
                {"name": "flyto:source_commit", "value": release["source_commit"]},
                {"name": "flyto:tree_sha256", "value": release["tree_sha256"]},
            ],
        },
        "components": components,
    }
    (root / args.output).write_text(json.dumps(sbom, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {args.output} with {len(components)} components")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
