#!/usr/bin/env python3
"""Audit the Flyto2 Cloud CE source controls or a generated release tree."""

from __future__ import annotations

import argparse
import ast
import fnmatch
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Iterable


MANIFEST_NAME = "OPEN_CORE_MANIFEST.json"
EXPORT_MANIFEST_NAME = "CE_EXPORT.json"
SOURCE_REQUIRED_FILES = [
    MANIFEST_NAME,
    "LICENSES.md",
    "docs/open-core.md",
    "docs/edition-matrix.md",
    "install/Dockerfile.ce",
    "install/docker-compose.ce.yml",
    "install/.env.ce.example",
    "scripts/export_cloud_ce.py",
]
TEXT_SUFFIXES = {
    "",
    ".cjs",
    ".css",
    ".env",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".vue",
    ".yaml",
    ".yml",
}
SECRET_ASSIGNMENT = re.compile(
    r"(?im)^\s*(?:export\s+)?(?:STRIPE_SECRET_KEY|STRIPE_WEBHOOK_SECRET|"
    r"SENTRY_AUTH_TOKEN|SEGMENT_WRITE_KEY|POSTHOG_API_KEY|AMPLITUDE_API_KEY)\s*[:=]\s*"
    r"[^\s$<{][^\r\n]*$"
)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _matches(path: str, patterns: Iterable[str]) -> bool:
    for pattern in patterns:
        normalized = pattern.rstrip("/")
        if fnmatch.fnmatchcase(path, normalized):
            return True
        if normalized.endswith("/**") and path == normalized[:-3]:
            return True
    return False


def _load_manifest(root: Path, blockers: list[str]) -> dict:
    path = root / MANIFEST_NAME
    try:
        manifest = json.loads(_read_text(path))
    except json.JSONDecodeError as exc:
        blockers.append(f"{MANIFEST_NAME} is invalid JSON: {exc}")
        return {}
    if manifest.get("schema") != "flyto.open-core-export.v2":
        blockers.append(f"{MANIFEST_NAME} must use flyto.open-core-export.v2")
    if manifest.get("license", {}).get("ce_license") != "Apache-2.0":
        blockers.append("CE license must be exactly Apache-2.0")
    for key in (
        "required_release_files",
        "ce_include_patterns",
        "ce_ignore_path_patterns",
        "ce_deny_path_patterns",
        "ce_deny_content_markers",
        "ce_override_paths",
        "ce_replacement_paths",
    ):
        if not isinstance(manifest.get(key), list) or not manifest[key]:
            blockers.append(f"manifest field {key!r} must be a non-empty list")
    return manifest


def _audit_source_tree(root: Path, manifest: dict, blockers: list[str]) -> None:
    for rel in SOURCE_REQUIRED_FILES:
        if not (root / rel).is_file():
            blockers.append(f"missing source control file: {rel}")
    body = _read_text(root / "docs/open-core.md")
    for marker in (
        "Flyto2 Cloud CE is the self-hosted workflow and MCP control plane",
        "Dropped folders are never executed directly.",
        "flyto.editions.v1",
        "scripts/export_cloud_ce.py",
    ):
        if marker not in body:
            blockers.append(f"docs/open-core.md missing boundary marker: {marker}")

    include_patterns = manifest.get("ce_include_patterns", [])
    if not any("backend" in item for item in include_patterns):
        blockers.append("CE include patterns do not contain backend source")
    if not any("frontend" in item for item in include_patterns):
        blockers.append("CE include patterns do not contain frontend source")

    deny_patterns = manifest.get("ce_deny_path_patterns", [])
    override_paths = set(manifest.get("ce_override_paths", []))
    overlay = root / manifest.get("overlay_directory", "ce")
    ignore_patterns = manifest.get("ce_ignore_path_patterns", [])
    for rel in sorted(override_paths):
        if not (root / rel).is_file() or not (overlay / rel).is_file():
            blockers.append(f"CE override must exist in source and overlay: {rel}")
    for path in overlay.rglob("*") if overlay.is_dir() else ():
        if not path.is_file() and not path.is_symlink():
            continue
        rel = path.relative_to(overlay).as_posix()
        if _matches(rel, ignore_patterns):
            continue
        if (root / rel).is_file() and rel not in override_paths:
            blockers.append(f"CE overlay contains undeclared source override: {rel}")
    for rel in manifest.get("ce_replacement_paths", []):
        if rel not in override_paths:
            blockers.append(f"CE replacement is not a declared override: {rel}")
        if not _matches(rel, deny_patterns):
            blockers.append(f"CE replacement is not protected by a deny rule: {rel}")
        if not (root / manifest.get("overlay_directory", "ce") / rel).is_file():
            blockers.append(f"CE replacement overlay is missing: {rel}")


def _release_paths(root: Path):
    """Yield release contents while ignoring the checkout's own Git directory."""
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if rel == ".git" or rel.startswith(".git/"):
            continue
        yield path


def _inventory(root: Path) -> tuple[dict[str, str], str]:
    hashes: dict[str, str] = {}
    digest = hashlib.sha256()
    for path in _release_paths(root):
        if not path.is_file() or path.name == EXPORT_MANIFEST_NAME:
            continue
        rel = path.relative_to(root).as_posix()
        file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        hashes[rel] = file_hash
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hash.encode("ascii"))
        digest.update(b"\n")
    return hashes, digest.hexdigest()


def _audit_export_manifest(root: Path, blockers: list[str]) -> None:
    path = root / EXPORT_MANIFEST_NAME
    try:
        release = json.loads(_read_text(path))
    except json.JSONDecodeError as exc:
        blockers.append(f"{EXPORT_MANIFEST_NAME} is invalid JSON: {exc}")
        return
    if release.get("schema") != "flyto.ce-release.v1":
        blockers.append(f"{EXPORT_MANIFEST_NAME} has unsupported schema")
    expected_hashes, expected_tree_hash = _inventory(root)
    if release.get("files") != expected_hashes:
        blockers.append(f"{EXPORT_MANIFEST_NAME} file inventory does not match release tree")
    if release.get("tree_sha256") != expected_tree_hash:
        blockers.append(f"{EXPORT_MANIFEST_NAME} tree_sha256 does not match release tree")
    if not re.fullmatch(r"[0-9a-f]{40}", str(release.get("source_commit", ""))):
        blockers.append(f"{EXPORT_MANIFEST_NAME} source_commit is not a Git SHA")


def _local_module_exists(backend: Path, module: str) -> bool:
    path = backend.joinpath(*module.split("."))
    return path.with_suffix(".py").is_file() or path.is_dir()


def _audit_local_python_imports(root: Path, blockers: list[str]) -> None:
    """Reject imports that still point at removed private backend modules."""
    backend = root / "src/ui/web/backend"
    if not backend.is_dir():
        return
    local_roots = {
        path.name
        for path in backend.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    }
    for path in backend.rglob("*.py"):
        rel = path.relative_to(root).as_posix()
        try:
            tree = ast.parse(_read_text(path), filename=rel)
        except SyntaxError as exc:
            blockers.append(f"{rel}: invalid Python syntax: {exc.msg}")
            continue
        package = list(path.relative_to(backend).parent.parts)
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    keep = max(0, len(package) - (node.level - 1))
                    parts = package[:keep]
                    if node.module:
                        parts.extend(node.module.split("."))
                    if parts:
                        modules.append(".".join(parts))
                elif node.module:
                    modules.append(node.module)
            for module in modules:
                if module.split(".", 1)[0] not in local_roots:
                    continue
                if not _local_module_exists(backend, module):
                    blockers.append(f"{rel}: unresolved local import {module}")


def _audit_release_tree(root: Path, manifest: dict, blockers: list[str]) -> None:
    for rel in manifest.get("required_release_files", []):
        if not (root / rel).is_file():
            blockers.append(f"missing required CE release file: {rel}")

    for path in _release_paths(root):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            blockers.append(f"CE release contains symlink: {rel}")
        if ".git" in path.relative_to(root).parts:
            blockers.append(f"CE release contains Git metadata: {rel}")
        if path.name == "__pycache__" or path.suffix == ".pyc":
            blockers.append(f"CE release contains generated Python bytecode: {rel}")

    replacements = set(manifest.get("ce_replacement_paths", []))
    for pattern in manifest.get("ce_deny_path_patterns", []):
        matches = [
            path.relative_to(root).as_posix()
            for path in _release_paths(root)
            if _matches(path.relative_to(root).as_posix(), [pattern])
            and path.relative_to(root).as_posix() not in replacements
        ]
        if matches:
            blockers.append(f"private path escaped into CE tree: {pattern} ({matches[0]})")

    denied_markers = [str(item) for item in manifest.get("ce_deny_content_markers", [])]
    for path in _release_paths(root):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        rel = path.relative_to(root).as_posix()
        if rel in {MANIFEST_NAME, EXPORT_MANIFEST_NAME}:
            continue
        body = _read_text(path)
        if SECRET_ASSIGNMENT.search(body):
            blockers.append(f"{rel}: CE release contains an assigned hosted secret")
        if rel.startswith(("src/", "install/")):
            lowered = body.lower()
            for marker in denied_markers:
                if marker and marker.lower() in lowered:
                    blockers.append(f"{rel}: denied CE implementation marker {marker!r}")

    license_body = _read_text(root / "LICENSE")
    if "Apache License" not in license_body or "Version 2.0, January 2004" not in license_body:
        blockers.append("generated CE LICENSE is not Apache License 2.0")
    _audit_local_python_imports(root, blockers)
    _audit_export_manifest(root, blockers)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="source workspace or generated CE tree")
    parser.add_argument(
        "--release-tree",
        action="store_true",
        help="validate a generated CE release including its content inventory",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve()
    blockers: list[str] = []
    manifest = _load_manifest(root, blockers)
    if manifest:
        if args.release_tree:
            _audit_release_tree(root, manifest, blockers)
        else:
            _audit_source_tree(root, manifest, blockers)
    if blockers:
        for blocker in blockers:
            print("BLOCKED: " + blocker, file=sys.stderr)
        return 2
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
