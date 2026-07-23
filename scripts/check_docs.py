#!/usr/bin/env python3
"""Validate the public repository documentation contract."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


REQUIRED_FILES = (
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "PROJECT.md",
    "ARCHITECTURE.md",
    "STATE.md",
    "ROADMAP.md",
    "tasks.md",
    "DECISIONS.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "docs/README.md",
    "docs/FEATURES.md",
    "docs/documentation-manifest.json",
    "docs/getting-started.md",
    "docs/mcp-studio.md",
    "docs/use-cases.md",
    "docs/ce-cloud-boundary.md",
    "docs/flow-cloud-sync.md",
    "docs/edition-matrix.md",
    "src/README.md",
    "scripts/README.md",
    "tests/README.md",
    "workflows/idea-capture.md",
    "workflows/planning.md",
    "workflows/implementation.md",
    "workflows/bugfix.md",
    "workflows/refactor.md",
    "workflows/investigation.md",
    "workflows/wrap-up.md",
    "handoffs/_registry.md",
)

README_MARKERS = (
    "# Flyto2 Flow",
    "## Quick Start",
    "## Usage",
    "## Why Flyto2 Flow",
    "## MCP Studio",
    "## Local Means Local",
    "## Contributing",
    "## License and Trademark",
)

MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
STALE_BRAND = re.compile(r"\bFlyto(?!2|[-_/])\b")
TEXT_SUFFIXES = {".md", ".yml", ".yaml"}
IGNORED_DIRS = {
    ".audit-tools",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "vendor",
}


def public_text_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for current, directories, names in os.walk(root):
        directories[:] = [
            name
            for name in directories
            if name not in IGNORED_DIRS and (not name.startswith(".") or name == ".github")
        ]
        current_path = Path(current)
        files.extend(
            current_path / name
            for name in names
            if Path(name).suffix.lower() in TEXT_SUFFIXES
        )
    return sorted(files)


def check_required_files(root: Path) -> list[str]:
    return [f"missing required documentation: {name}" for name in REQUIRED_FILES if not (root / name).is_file()]


def check_readme_contract(root: Path) -> list[str]:
    readme = root / "README.md"
    if not readme.is_file():
        return []
    text = readme.read_text(encoding="utf-8")
    return [f"README.md is missing required section: {marker}" for marker in README_MARKERS if marker not in text]


def _local_link_target(source: Path, raw_target: str) -> Path | None:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    if not target or target.startswith("#"):
        return None
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return None
    path = unquote(parsed.path)
    if not path:
        return None
    return (source.parent / path).resolve()


def check_markdown_links(root: Path) -> list[str]:
    errors: list[str] = []
    for source in (path for path in public_text_files(root) if path.suffix.lower() == ".md"):
        text = source.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK.finditer(text):
            target = _local_link_target(source, match.group(1))
            if target is not None and not target.exists():
                relative_source = source.relative_to(root)
                errors.append(f"broken local link in {relative_source}: {match.group(1)}")
    return errors


def check_email_domains(root: Path) -> list[str]:
    errors: list[str] = []
    for source in public_text_files(root):
        text = source.read_text(encoding="utf-8")
        for match in EMAIL.finditer(text):
            if match.group(1).lower() != "flyto2.com":
                relative_source = source.relative_to(root)
                errors.append(f"non-Flyto2 email domain in {relative_source}: {match.group(0)}")
    return errors


def check_brand_name(root: Path) -> list[str]:
    errors: list[str] = []
    for source in public_text_files(root):
        for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
            if STALE_BRAND.search(line):
                relative_source = source.relative_to(root)
                errors.append(f"stale standalone Flyto brand in {relative_source}:{line_number}")
    return errors


def check_repository(root: Path) -> list[str]:
    root = root.resolve()
    return [
        *check_required_files(root),
        *check_readme_contract(root),
        *check_markdown_links(root),
        *check_email_domains(root),
        *check_brand_name(root),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", type=Path)
    args = parser.parse_args()
    errors = check_repository(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Documentation contract passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
