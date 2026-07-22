#!/usr/bin/env python3
"""Fail when hosted product source crosses into the Flyto2 Flow upstream."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_FILES = (
    "FLOW_BOUNDARY.json",
    "README.md",
    "docs/ce-cloud-boundary.md",
    "docs/open-core.md",
    "install/Dockerfile.ce",
    "install/docker-compose.ce.yml",
    "src/ui/web/frontend/src/edition/ce.js",
)

FORBIDDEN_PATH_PARTS = (
    "api/auth",
    "api/user_mgmt",
    "components/collaboration",
    "components/creator",
    "components/dashboard",
    "components/login",
    "components/marketplace",
    "components/messaging",
    "components/notifications",
    "components/settings",
    "components/wallet",
    "composables/marketplace",
    "composables/userprofile",
    "services/cloud",
    "services/collaboration",
    "services/telemetry",
    "stores/collaboration",
    "stores/organization",
    "stores/user",
    "utils/telemetry",
    "views/login.vue",
    "views/messages.vue",
    "views/usersettings.vue",
)

FORBIDDEN_FILENAMES = {
    "dashboardstore.js",
    "marketplacestore.js",
    "messaging.js",
    "organizationstore.js",
    "userstore.js",
    "walletstore.js",
}

FORBIDDEN_SOURCE_MARKERS = (
    "firebase",
    "firestore",
    "posthog",
    "amplitude",
    "segment_write_key",
    "sentry_dsn",
    "flyto-cloud",
    "user@localhost",
    "provisioning title",
    "provisioning hint",
    "/api/auth",
    "/marketplace",
    "/messages",
)

SOURCE_SUFFIXES = {".cjs", ".css", ".html", ".js", ".jsx", ".mjs", ".py", ".ts", ".tsx", ".vue"}
SKIP_PARTS = {".git", "dist", "node_modules", "__pycache__"}
ALLOWED_FRONTEND_ROUTES = {
    "/",
    "/my-templates",
    "/templates/:id",
    "/templates/builder",
    "/templates/builder/:id",
    "/templates/runner/:id",
    "/executions/:id",
    "/variables",
    "/observability",
    "/:pathMatch(.*)*",
    "",
    "alerts",
    "metrics",
    "traces",
    "traces/:traceId",
}


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _source_files(root: Path):
    for source_root in (root / "src", root / "install"):
        if not source_root.exists():
            continue
        for path in source_root.rglob("*"):
            if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
                continue
            yield path


def check(root: Path) -> list[str]:
    failures: list[str] = []
    for rel in REQUIRED_FILES:
        if not (root / rel).is_file():
            failures.append(f"missing required boundary file: {rel}")

    boundary_path = root / "FLOW_BOUNDARY.json"
    if boundary_path.is_file():
        try:
            boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
            if boundary.get("schema") != "flyto.flow-boundary.v1":
                failures.append("FLOW_BOUNDARY.json has the wrong schema")
            if boundary.get("implicit_outbound_network") is not False:
                failures.append("Flow boundary must deny implicit outbound network access")
            edition_seam = boundary.get("frontend_edition_seam", {})
            if edition_seam.get("mode") != "additive_slots":
                failures.append("Frontend edition seam must use additive slots")
            for rel in edition_seam.get("shared_shells", []):
                if not (root / rel).is_file():
                    failures.append(f"missing shared UI shell: {rel}")
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"FLOW_BOUNDARY.json is invalid: {exc}")

    source_files = list(_source_files(root))
    for path in source_files:
        rel = _relative(path, root)
        lowered_rel = rel.lower()
        if path.name == "__pycache__" or path.suffix == ".pyc":
            failures.append(f"generated Python file in source tree: {rel}")
        if path.name.lower() in FORBIDDEN_FILENAMES:
            failures.append(f"hosted product file in Flow: {rel}")
        if any(part in lowered_rel for part in FORBIDDEN_PATH_PARTS):
            failures.append(f"hosted product path in Flow: {rel}")
        if path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        try:
            body = path.read_text(encoding="utf-8").lower()
        except (OSError, UnicodeDecodeError):
            continue
        for marker in FORBIDDEN_SOURCE_MARKERS:
            if marker in body:
                failures.append(f"forbidden hosted marker {marker!r}: {rel}")
        if "user_id" in body and not lowered_rel.endswith(("gateway/storage/offline_db.py", "gateway/storage/database.py")):
            failures.append(f"identity-scoped field remains outside compatibility migration: {rel}")

    router_path = root / "src/ui/web/frontend/src/router.js"
    if router_path.is_file():
        body = router_path.read_text(encoding="utf-8")
        routes = set(re.findall(r"\bpath:\s*['\"]([^'\"]+)['\"]", body))
        unexpected = sorted(route for route in routes if route not in ALLOWED_FRONTEND_ROUTES)
        if unexpected:
            failures.append(f"unexpected frontend routes: {', '.join(unexpected)}")

    app_path = root / "src/ui/web/frontend/src/App.vue"
    if app_path.is_file():
        app_body = app_path.read_text(encoding="utf-8")
        for shell in ("<AppNavbar", "<AppFooter"):
            if shell not in app_body:
                failures.append(f"shared UI shell is not mounted directly: {shell}")

    dockerfile = root / "install/Dockerfile.ce"
    if dockerfile.is_file():
        body = dockerfile.read_text(encoding="utf-8").lower()
        for marker in ("flyto-core", "playwright==", "playwright install --with-deps chromium", "flyto_require_bundled_runtime=1"):
            if marker not in body:
                failures.append(f"Docker image does not bundle required runtime marker: {marker}")

    header = root / "src/ui/web/frontend/src/components/layout/AppNavbar.vue"
    footer = root / "src/ui/web/frontend/src/components/layout/AppFooter.vue"
    for path in (header, footer):
        if path.is_file() and "height: 3.5rem" not in path.read_text(encoding="utf-8"):
            failures.append(f"brand logo height is not 3.5rem: {_relative(path, root)}")

    return sorted(set(failures))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    failures = check(root)
    if failures:
        print("Flyto2 Flow purity check failed:", file=sys.stderr)
        for failure in failures:
            print(f" - {failure}", file=sys.stderr)
        return 1
    print("Flyto2 Flow purity check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
