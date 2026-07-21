#!/usr/bin/env python3
"""Audit declared CE dependency licenses and write a third-party notice report."""

from __future__ import annotations

import argparse
import json
import re
import sys
from importlib import metadata
from pathlib import Path

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


FORBIDDEN_LICENSE_MARKERS = (
    "AGPL",
    "BUSL",
    "COMMONS CLAUSE",
    "ELASTIC LICENSE",
    "GPL-",
    "GPL ",
    "SERVER SIDE PUBLIC LICENSE",
    "SSPL",
)
CLASSIFIER_LICENSES = {
    "Apache Software License": "Apache-2.0",
    "BSD License": "BSD",
    "ISC License (ISCL)": "ISC",
    "MIT License": "MIT",
    "Mozilla Public License 2.0 (MPL 2.0)": "MPL-2.0",
    "Python Software Foundation License": "PSF-2.0",
    "The Unlicense (Unlicense)": "Unlicense",
}


def _load_overrides(root: Path) -> dict[str, str]:
    path = root / "dependency-license-overrides.json"
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read dependency license overrides: {exc}") from exc
    return {canonicalize_name(key): str(value) for key, value in body.items()}


def _is_forbidden(license_name: str) -> bool:
    upper = license_name.upper()
    return any(marker in upper for marker in FORBIDDEN_LICENSE_MARKERS)


def _npm_dependencies(root: Path, overrides: dict[str, str]) -> list[tuple[str, str, str, str]]:
    path = root / "src/ui/web/frontend/package-lock.json"
    lock = json.loads(path.read_text(encoding="utf-8"))
    dependencies: list[tuple[str, str, str, str]] = []
    for package_path, package in sorted(lock.get("packages", {}).items()):
        if not package_path:
            continue
        name = str(package.get("name") or package_path.rsplit("node_modules/", 1)[-1])
        version = str(package.get("version") or "unknown")
        license_name = str(package.get("license") or overrides.get(canonicalize_name(name), "UNKNOWN"))
        dependencies.append(("npm", name, version, license_name))
    return dependencies


def _locked_requirements(path: Path) -> list[Requirement]:
    requirements: list[Requirement] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "-")):
            continue
        declaration = stripped.removesuffix("\\").strip()
        requirements.append(Requirement(declaration))
    return requirements


def _requirement_names(path: Path) -> list[str]:
    return [canonicalize_name(item.name) for item in _locked_requirements(path)]


def _metadata_license(dist: metadata.Distribution, overrides: dict[str, str]) -> str:
    name = canonicalize_name(dist.metadata.get("Name", ""))
    if name in overrides:
        return overrides[name]
    expression = dist.metadata.get("License-Expression")
    if expression:
        return str(expression).strip()
    raw_license = str(dist.metadata.get("License") or "").strip()
    if raw_license and raw_license.upper() not in {"UNKNOWN", "NONE"} and len(raw_license) < 160:
        return re.sub(r"\s+", " ", raw_license)
    for classifier in dist.metadata.get_all("Classifier") or []:
        prefix = "License :: OSI Approved :: "
        if classifier.startswith(prefix):
            value = classifier[len(prefix) :]
            return CLASSIFIER_LICENSES.get(value, value)
    return "UNKNOWN"


def _python_dependencies(root: Path, overrides: dict[str, str]) -> list[tuple[str, str, str, str]]:
    installed = {
        canonicalize_name(dist.metadata.get("Name", "")): dist
        for dist in metadata.distributions()
        if dist.metadata.get("Name")
    }
    pending = _requirement_names(root / "src/ui/web/backend/requirements-ce.lock")
    selected: set[str] = set()
    environment = default_environment()
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        dist = installed.get(name)
        if dist is None:
            raise RuntimeError(f"required Python distribution is not installed: {name}")
        selected.add(name)
        for raw_requirement in dist.requires or []:
            requirement = Requirement(raw_requirement)
            if requirement.marker and not requirement.marker.evaluate(environment):
                continue
            dependency_name = canonicalize_name(requirement.name)
            if dependency_name in installed and dependency_name not in selected:
                pending.append(dependency_name)

    result: list[tuple[str, str, str, str]] = []
    for name in sorted(selected):
        dist = installed[name]
        result.append(
            (
                "pypi",
                str(dist.metadata.get("Name") or name),
                str(dist.version),
                _metadata_license(dist, overrides),
            )
        )
    return result


def _write_report(path: Path, dependencies: list[tuple[str, str, str, str]]) -> None:
    lines = [
        "# Third-Party Dependency Inventory",
        "",
        "Generated from the CE dependency manifests. Package authors retain all rights",
        "under their respective licenses.",
        "",
        "| Ecosystem | Package | Version | Declared license |",
        "| --- | --- | --- | --- |",
    ]
    for ecosystem, name, version, license_name in dependencies:
        safe = [value.replace("|", "\\|") for value in (ecosystem, name, version, license_name)]
        lines.append(f"| {safe[0]} | {safe[1]} | {safe[2]} | {safe[3]} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="generated CE tree")
    parser.add_argument("--python-installed", action="store_true", help="audit installed Python dependency closure")
    parser.add_argument("--report", default="THIRD_PARTY_DEPENDENCIES.md")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        overrides = _load_overrides(root)
        dependencies = _npm_dependencies(root, overrides)
        if args.python_installed:
            dependencies.extend(_python_dependencies(root, overrides))
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2

    blockers = []
    for ecosystem, name, version, license_name in dependencies:
        if license_name == "UNKNOWN":
            blockers.append(f"{ecosystem}:{name}@{version} has no declared license")
        elif _is_forbidden(license_name):
            blockers.append(f"{ecosystem}:{name}@{version} uses forbidden license {license_name!r}")
    if blockers:
        for blocker in blockers:
            print("BLOCKED: " + blocker, file=sys.stderr)
        return 2

    _write_report(root / args.report, sorted(dependencies, key=lambda item: (item[0], item[1].lower())))
    print(f"ok: audited {len(dependencies)} dependency licenses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
