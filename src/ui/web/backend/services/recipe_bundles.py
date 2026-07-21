"""Warroom recipe bundle import planning.

The service persists MCP recipe assets as private templates for a user. It does
not import flyto-core at runtime, and it never stores runtime credentials.
"""

from __future__ import annotations

import re
import hashlib
import hmac
import os
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from gateway.providers.data.models import TemplateCreateDTO, TemplateUpdateDTO


WARROOM_BUNDLE_ID = "flyto2-warroom-smoke"
WARROOM_BUNDLE_MANIFEST = "flyto-bundle.yaml"
WARROOM_BUNDLE_KIND = "flyto.warroom.bundle.v1"
WARROOM_IMPORT_DIR_ENV = "FLYTO_WARROOM_IMPORT_DIR"
WARROOM_BUNDLE_HMAC_SECRET_ENV = "FLYTO_WARROOM_BUNDLE_HMAC_SECRET"
WARROOM_ROOT_FOLDER = "Warroom"
CREATED_TAB = "created"
_BUNDLE_SNAPSHOT_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "recipe_bundles"
    / f"{WARROOM_BUNDLE_ID}.yaml"
)

_PROJECT_SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
_TEMPLATE_RE = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}")
_SCENARIO_METADATA_KEYS = {"scenario_id", "display_name", "runtime_required_args"}
_FORBIDDEN_FIELD_FRAGMENTS = {
    "password",
    "token",
    "pat",
    "authorization",
    "cookie",
    "firebase_session",
}


class RecipeBundleImportError(ValueError):
    """Raised when a recipe bundle import cannot be safely completed."""


def sign_warroom_bundle_manifest(manifest: dict[str, Any], secret: str) -> str:
    """Return the canonical HMAC signature for a signed Warroom bundle."""
    if not secret:
        raise RecipeBundleImportError("Warroom bundle signing secret is required")
    payload = _signed_manifest_payload(manifest)
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"hmac-sha256:{digest}"


def load_signed_warroom_bundle_manifest(
    source_path: Path | str,
    *,
    secret: str | None = None,
) -> dict[str, Any]:
    """Load and verify a dropped signed Warroom bundle manifest."""
    manifest_path = Path(source_path).expanduser()
    if manifest_path.name != WARROOM_BUNDLE_MANIFEST:
        raise RecipeBundleImportError("Signed Warroom bundle source must be flyto-bundle.yaml")
    if not manifest_path.exists() or not manifest_path.is_file():
        raise RecipeBundleImportError("Signed Warroom bundle manifest not found")
    if manifest_path.is_symlink():
        raise RecipeBundleImportError("Signed Warroom bundle manifest must not be a symlink")

    bundle_root = manifest_path.parent.resolve()
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise RecipeBundleImportError("Signed Warroom bundle manifest must be a mapping")
    _validate_signed_bundle_envelope(manifest)
    _verify_signed_bundle_signature(manifest, secret=secret)
    _verify_signed_bundle_assets(manifest, bundle_root)

    forbidden = _forbidden_fields(manifest)
    _assert_no_stored_secrets(manifest, path=("bundle",), forbidden=forbidden)
    manifest["_source_path"] = str(manifest_path.resolve())
    return manifest


def scan_warroom_bundle_inbox(
    import_dir: Path | str | None = None,
    *,
    secret: str | None = None,
) -> dict[str, Any]:
    """Scan the local Warroom import directory and return valid pending bundles."""
    import_dir_value = import_dir or os.getenv(WARROOM_IMPORT_DIR_ENV, "")
    if not import_dir_value:
        return {"ok": True, "import_dir": None, "pending": [], "rejected": []}

    root = Path(import_dir_value).expanduser()
    if not root.exists():
        return {"ok": True, "import_dir": str(root), "pending": [], "rejected": []}
    if not root.is_dir():
        raise RecipeBundleImportError("FLYTO_WARROOM_IMPORT_DIR must be a directory")

    manifest_paths = []
    direct_manifest = root / WARROOM_BUNDLE_MANIFEST
    if direct_manifest.exists():
        manifest_paths.append(direct_manifest)
    manifest_paths.extend(sorted(root.glob(f"*/{WARROOM_BUNDLE_MANIFEST}")))

    pending = []
    rejected = []
    for manifest_path in manifest_paths:
        try:
            manifest = load_signed_warroom_bundle_manifest(manifest_path, secret=secret)
            pending.append(_pending_bundle_summary(manifest))
        except RecipeBundleImportError as exc:
            rejected.append({"source_path": str(manifest_path), "error": str(exc)})

    return {
        "ok": True,
        "import_dir": str(root),
        "pending": pending,
        "rejected": rejected,
    }


def load_warroom_bundle_manifest(path: Path | None = None) -> dict[str, Any]:
    """Load the packaged Warroom bundle snapshot."""

    manifest_path = path or _BUNDLE_SNAPSHOT_PATH
    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = yaml.safe_load(handle)
    if not isinstance(manifest, dict):
        raise RecipeBundleImportError("Recipe bundle manifest must be a mapping")
    if manifest.get("bundle_id") != WARROOM_BUNDLE_ID:
        raise RecipeBundleImportError("Unsupported recipe bundle manifest")
    return manifest


def list_public_recipe_bundles() -> list[dict[str, Any]]:
    """Return official recipe bundles that can be installed from Marketplace."""

    manifest = load_warroom_bundle_manifest()
    plan = build_warroom_bundle_plan("flyto2", "https://app.flyto2.com", manifest=manifest)
    security = deepcopy(plan.get("security", {}))
    export_contract = deepcopy(plan.get("export_contract", {}))
    return [
        {
            "bundle_id": manifest["bundle_id"],
            "display_name": manifest.get("display_name", manifest["bundle_id"]),
            "description": manifest.get(
                "description",
                "Official Flyto2 Warroom starter pack with reusable flyto-core smoke recipes.",
            ),
            "asset_kind": "mcp_recipe_bundle",
            "official_bundle": True,
            "install_target": "private_warroom",
            "pricing": "free",
            "category": "testing",
            "folder_count": plan["folder_count"],
            "template_count": plan["template_count"],
            "scenario_ids": plan["scenario_ids"],
            "folder_paths": plan["folder_paths"],
            "runtime_required_args": sorted({
                arg
                for asset in plan.get("recipe_assets", [])
                for arg in asset.get("runtime_required_args", [])
            }),
            "security": security,
            "export_contract": export_contract,
        }
    ]


def build_warroom_bundle_plan(
    project_slug: str,
    base_url: str,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the deterministic folder/template plan for a Warroom project."""

    project_slug = _validate_project_slug(project_slug)
    base_url = _validate_base_url(base_url)
    args = {"project_slug": project_slug, "base_url": base_url}
    manifest = deepcopy(manifest or load_warroom_bundle_manifest())
    _require_keys(manifest, ["bundle_id", "cloud_target", "recipes"])
    _validate_required_args(manifest, args)
    forbidden = _forbidden_fields(manifest)
    _assert_no_stored_secrets(manifest.get("recipes"), path=("recipes",), forbidden=forbidden)

    cloud_target = manifest["cloud_target"]
    root_folder = _render(cloud_target.get("root_folder", WARROOM_ROOT_FOLDER), args)
    project_folder = _render_list(
        cloud_target.get("default_folder_path", [root_folder, "{{project_slug}}"]),
        args,
    )
    security = deepcopy(manifest.get("security", {}))
    export_contract = deepcopy(manifest.get("export_contract", {}))
    folders = [
        {"path": [root_folder]},
        {"path": project_folder},
    ]
    assets = []

    for recipe in manifest.get("recipes", []):
        if not isinstance(recipe, dict):
            raise RecipeBundleImportError("Recipe bundle recipes must be mappings")
        _require_keys(recipe, ["recipe_id", "source", "folder_path"])

        folder_path = _render_list(recipe["folder_path"], args)
        folders.append({"path": folder_path})
        recipe_runtime_args = recipe.get("runtime_required_args", [])
        if not isinstance(recipe_runtime_args, list):
            raise RecipeBundleImportError("runtime_required_args must be a list")

        for scenario in recipe.get("scenarios", []):
            if not isinstance(scenario, dict):
                raise RecipeBundleImportError("Recipe bundle scenarios must be mappings")
            _require_keys(scenario, ["scenario_id"])
            runtime_required_args = scenario.get("runtime_required_args", recipe_runtime_args)
            if not isinstance(runtime_required_args, list):
                raise RecipeBundleImportError("runtime_required_args must be a list")
            default_args = {
                key: _render(value, args)
                for key, value in scenario.items()
                if key not in _SCENARIO_METADATA_KEYS
            }
            _assert_no_stored_secrets(
                default_args,
                path=("recipes", recipe["recipe_id"], "scenarios", scenario["scenario_id"]),
                forbidden=forbidden,
            )
            asset = {
                "bundle_id": manifest["bundle_id"],
                "scenario_id": scenario["scenario_id"],
                "recipe_id": recipe["recipe_id"],
                "display_name": scenario.get(
                    "display_name",
                    _humanize_scenario_id(scenario["scenario_id"]),
                ),
                "source": recipe["source"],
                "folder_path": folder_path,
                "default_args": default_args,
                "runtime_required_args": list(runtime_required_args),
                "security": security,
                "export_contract": export_contract,
            }
            _assert_no_stored_secrets(asset, path=("assets", scenario["scenario_id"]), forbidden=forbidden)
            assets.append(asset)

    plan = {
        "bundle_id": manifest["bundle_id"],
        "display_name": manifest.get("display_name", manifest["bundle_id"]),
        "root_folder": root_folder,
        "project_folder": project_folder,
        "project_slug": project_slug,
        "base_url": base_url,
        "folders": _unique_folders(folders),
        "recipe_assets": assets,
        "security": security,
        "export_contract": export_contract,
    }
    plan.update(_plan_summary(plan))
    return plan


class WarroomRecipeBundleImporter:
    """Import Warroom recipe bundle plans into a user's private templates."""

    def __init__(self, provider: Any):
        self.provider = provider
        self.templates = getattr(provider, "templates", provider)

    async def import_bundle(
        self,
        *,
        user_id: str,
        project_slug: str,
        base_url: str,
        source_path: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        manifest = load_signed_warroom_bundle_manifest(source_path) if source_path else None
        plan = build_warroom_bundle_plan(project_slug, base_url, manifest=manifest)
        summary = _plan_summary(plan)
        if dry_run:
            return {
                "ok": True,
                "dry_run": True,
                "plan": plan,
                "folders": [],
                "templates": [],
                "warnings": [],
                "created_count": 0,
                "updated_count": 0,
                "source_path": source_path,
                **summary,
            }

        folder_results = await self._ensure_folders(user_id, plan["folders"])
        folder_ids = {tuple(item["path"]): item["id"] for item in folder_results}

        existing_templates = await self._load_existing_bundle_templates(user_id)
        template_results = []
        for asset in plan["recipe_assets"]:
            folder_id = folder_ids.get(tuple(asset["folder_path"]))
            if not folder_id:
                raise RecipeBundleImportError("Recipe bundle folder resolution failed")
            template_results.append(
                await self._upsert_asset_template(user_id, asset, folder_id, existing_templates)
            )

        return {
            "ok": True,
            "dry_run": False,
            "bundle_id": plan["bundle_id"],
            "project_slug": plan["project_slug"],
            "root_folder": plan["root_folder"],
            "source_path": source_path,
            "folders": folder_results,
            "templates": template_results,
            "warnings": [],
            "created_count": sum(1 for item in template_results if item["action"] == "created"),
            "updated_count": sum(1 for item in template_results if item["action"] == "updated"),
            **summary,
        }

    async def _ensure_folders(self, user_id: str, folders: list[dict[str, Any]]) -> list[dict[str, Any]]:
        listed = await self.templates.list_folders(user_id, CREATED_TAB)
        folder_index = {
            (folder.name, folder.parent_id): folder
            for folder in listed
            if getattr(folder, "id", None) != "_settings"
        }

        results = []
        known_ids_by_path: dict[tuple[str, ...], str] = {}
        for folder in folders:
            parent_id = None
            path_so_far: list[str] = []
            for segment in folder["path"]:
                path_so_far.append(segment)
                existing = folder_index.get((segment, parent_id))
                created = False
                if existing is None:
                    existing = await self.templates.create_folder(
                        user_id=user_id,
                        name=segment,
                        tab=CREATED_TAB,
                        parent_id=parent_id,
                    )
                    folder_index[(segment, parent_id)] = existing
                    created = True
                parent_id = existing.id
                known_ids_by_path[tuple(path_so_far)] = existing.id
                result = {
                    "id": existing.id,
                    "path": list(path_so_far),
                    "created": created,
                }
                if result not in results:
                    results.append(result)

        return [
            {
                "id": folder_id,
                "path": list(path),
                "created": next(
                    (item["created"] for item in results if item["path"] == list(path)),
                    False,
                ),
            }
            for path, folder_id in known_ids_by_path.items()
        ]

    async def _load_existing_bundle_templates(self, user_id: str) -> dict[str, Any]:
        existing: dict[str, Any] = {}
        page = 1
        while page <= 10:
            result = await self.templates.list_user_templates(user_id=user_id, page=page, page_size=100)
            for template in getattr(result, "items", []):
                tags = set(getattr(template, "tags", []) or [])
                if f"bundle:{WARROOM_BUNDLE_ID}" not in tags:
                    continue
                for tag in tags:
                    if tag.startswith("scenario:"):
                        existing[tag.removeprefix("scenario:")] = template
            if not getattr(result, "has_next", False):
                break
            page += 1
        return existing

    async def _upsert_asset_template(
        self,
        user_id: str,
        asset: dict[str, Any],
        folder_id: str,
        existing_templates: dict[str, Any],
    ) -> dict[str, Any]:
        scenario_id = asset["scenario_id"]
        existing = existing_templates.get(scenario_id)
        payload = _template_payload(asset, folder_id)
        if existing:
            updated = await self.templates.update_template(
                user_id=user_id,
                template_id=existing.id,
                data=TemplateUpdateDTO(**payload),
            )
            template_id = getattr(updated, "id", existing.id)
            return {
                "id": template_id,
                "scenario_id": scenario_id,
                "action": "updated",
                "folder_id": folder_id,
            }

        created = await self.templates.create_template(
            user_id=user_id,
            data=TemplateCreateDTO(**payload),
        )
        return {
            "id": created.id,
            "scenario_id": scenario_id,
            "action": "created",
            "folder_id": folder_id,
        }


def _template_payload(asset: dict[str, Any], folder_id: str) -> dict[str, Any]:
    tool_name = _mcp_tool_name(asset)
    input_fields = _mcp_input_fields(asset)
    workflow_data = {
        "kind": "mcp_recipe_asset",
        "bundle_id": asset["bundle_id"],
        "scenario_id": asset["scenario_id"],
        "mcp_tool_name": tool_name,
        "recipe_id": asset["recipe_id"],
        "source": asset["source"],
        "default_args": asset["default_args"],
        "runtime_required_args": asset["runtime_required_args"],
        "security": deepcopy(asset.get("security", {})),
        "export_contract": deepcopy(asset.get("export_contract", {})),
    }
    _assert_no_stored_secrets(workflow_data)
    return {
        "name": asset["display_name"],
        "description": (
            "Reusable Flyto2 Warroom MCP recipe asset. "
            "Runtime credentials must be supplied only when executing the recipe."
        ),
        "category": "testing",
        "visibility": "private",
        "pricing": "free",
        "tags": [
            "warroom",
            "flyto2",
            "mcp-recipe",
            f"bundle:{asset['bundle_id']}",
            f"scenario:{asset['scenario_id']}",
        ],
        "steps": [
            {
                "id": "mcp-trigger",
                "module": "flow.trigger",
                "name": "MCP trigger",
                "params": {
                    "trigger_type": "mcp",
                    "tool_name": tool_name,
                    "tool_description": asset["display_name"],
                    "config": {"input_fields": input_fields},
                },
            },
            {
                "id": "run-recipe",
                "module": "mcp.recipe",
                "name": "Run MCP recipe",
                "params": {
                    "recipe_id": asset["recipe_id"],
                    "scenario_id": asset["scenario_id"],
                    "default_args": asset["default_args"],
                    "runtime_required_args": asset["runtime_required_args"],
                },
            }
        ],
        "workflow_data": workflow_data,
        "params_schema": _runtime_args_schema(asset),
        "required_permissions": ["workflow.execute"],
        "required_secrets": [],
        "folder_id": folder_id,
    }


def _mcp_tool_name(asset: dict[str, Any]) -> str:
    raw = f"warroom_{asset['bundle_id']}_{asset['scenario_id']}"
    tool_name = re.sub(r"[^A-Za-z0-9_]+", "_", raw).strip("_").lower()
    return tool_name[:96] or "warroom_recipe"


def _mcp_input_fields(asset: dict[str, Any]) -> list[dict[str, Any]]:
    schema = _runtime_args_schema(asset)
    required = set(schema.get("required", []))
    fields = []
    for name, spec in schema.get("properties", {}).items():
        field = {
            "name": name,
            "type": spec.get("type", "string"),
            "description": spec.get("description", ""),
            "required": name in required,
        }
        if spec.get("writeOnly"):
            field["writeOnly"] = True
        fields.append(field)
    return fields


def _runtime_args_schema(asset: dict[str, Any]) -> dict[str, Any]:
    properties = {
        "base_url": {"type": "string", "description": "Flyto2 base URL"},
    }
    required = ["base_url"]
    for arg in asset.get("runtime_required_args", []):
        properties[arg] = {
            "type": "string",
            "description": f"Runtime-only {arg}",
            "writeOnly": arg in {"username", "password"},
        }
        required.append(arg)
    return {
        "type": "object",
        "required": required,
        "properties": properties,
        "additionalProperties": True,
    }


def _require_keys(value: dict[str, Any], keys: list[str]) -> None:
    missing = [key for key in keys if key not in value]
    if missing:
        raise RecipeBundleImportError(f"Recipe bundle is missing required keys: {', '.join(missing)}")


def _validate_required_args(manifest: dict[str, Any], args: dict[str, Any]) -> None:
    required = manifest.get("required_args", [])
    if not isinstance(required, list):
        raise RecipeBundleImportError("required_args must be a list")
    missing = [key for key in required if args.get(key) in (None, "")]
    if missing:
        raise RecipeBundleImportError(f"Recipe bundle args are missing: {', '.join(missing)}")


def _forbidden_fields(manifest: dict[str, Any]) -> set[str]:
    fields = manifest.get("security", {}).get(
        "forbidden_stored_fields",
        sorted(_FORBIDDEN_FIELD_FRAGMENTS),
    )
    if not isinstance(fields, list):
        raise RecipeBundleImportError("security.forbidden_stored_fields must be a list")
    return {str(field).lower().replace("-", "_") for field in fields}


def _validate_project_slug(value: str) -> str:
    value = (value or "").strip()
    if not _PROJECT_SLUG_RE.match(value):
        raise RecipeBundleImportError("project_slug must be 1-80 characters using letters, numbers, dot, dash, or underscore")
    return value


def _validate_signed_bundle_envelope(manifest: dict[str, Any]) -> None:
    _require_keys(
        manifest,
        [
            "kind",
            "producer",
            "bundle_id",
            "created_at",
            "assets",
            "hashes",
            "signature",
            "required_runtime_args",
            "secrets_policy",
            "cloud_target",
            "recipes",
        ],
    )
    if manifest.get("kind") != WARROOM_BUNDLE_KIND:
        raise RecipeBundleImportError("Unsupported Warroom bundle kind")
    if manifest.get("bundle_id") != WARROOM_BUNDLE_ID:
        raise RecipeBundleImportError("Unsupported recipe bundle manifest")
    if manifest.get("secrets_policy") != "runtime_args_only":
        raise RecipeBundleImportError("Signed Warroom bundle secrets_policy must be runtime_args_only")
    if not isinstance(manifest.get("assets"), list):
        raise RecipeBundleImportError("Signed Warroom bundle assets must be a list")
    if not isinstance(manifest.get("hashes"), dict):
        raise RecipeBundleImportError("Signed Warroom bundle hashes must be a mapping")
    if not isinstance(manifest.get("required_runtime_args"), list):
        raise RecipeBundleImportError("Signed Warroom bundle required_runtime_args must be a list")


def _signed_manifest_payload(manifest: dict[str, Any]) -> bytes:
    payload = deepcopy(manifest)
    payload.pop("signature", None)
    payload.pop("_source_path", None)
    return yaml.safe_dump(payload, sort_keys=True, allow_unicode=False).encode("utf-8")


def _verify_signed_bundle_signature(manifest: dict[str, Any], *, secret: str | None = None) -> None:
    signing_secret = secret or os.getenv(WARROOM_BUNDLE_HMAC_SECRET_ENV, "")
    if not signing_secret:
        raise RecipeBundleImportError("FLYTO_WARROOM_BUNDLE_HMAC_SECRET is required")
    expected = sign_warroom_bundle_manifest(manifest, signing_secret)
    actual = str(manifest.get("signature") or "")
    if not hmac.compare_digest(actual, expected):
        raise RecipeBundleImportError("Signed Warroom bundle signature mismatch")


def _verify_signed_bundle_assets(manifest: dict[str, Any], bundle_root: Path) -> None:
    hashes = manifest.get("hashes", {})
    for raw_asset in manifest.get("assets", []):
        if not isinstance(raw_asset, str) or not raw_asset:
            raise RecipeBundleImportError("Signed Warroom bundle asset paths must be strings")
        asset_path = _resolve_bundle_asset(bundle_root, raw_asset)
        if not asset_path.exists() or not asset_path.is_file():
            raise RecipeBundleImportError(f"Signed Warroom bundle asset is missing: {raw_asset}")
        if asset_path.is_symlink():
            raise RecipeBundleImportError(f"Signed Warroom bundle asset must not be a symlink: {raw_asset}")
        expected_hash = hashes.get(raw_asset)
        if not expected_hash:
            raise RecipeBundleImportError(f"Signed Warroom bundle hash missing for asset: {raw_asset}")
        actual_hash = hashlib.sha256(asset_path.read_bytes()).hexdigest()
        if not hmac.compare_digest(str(expected_hash), actual_hash):
            raise RecipeBundleImportError(f"Signed Warroom bundle hash mismatch for asset: {raw_asset}")


def _resolve_bundle_asset(bundle_root: Path, raw_asset: str) -> Path:
    candidate = Path(raw_asset)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise RecipeBundleImportError(f"Signed Warroom bundle asset path is unsafe: {raw_asset}")
    resolved = (bundle_root / candidate).resolve()
    if bundle_root not in resolved.parents and resolved != bundle_root:
        raise RecipeBundleImportError(f"Signed Warroom bundle asset escapes bundle root: {raw_asset}")
    return resolved


def _pending_bundle_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    scenario_ids = [
        scenario.get("scenario_id")
        for recipe in manifest.get("recipes", [])
        if isinstance(recipe, dict)
        for scenario in recipe.get("scenarios", [])
        if isinstance(scenario, dict) and scenario.get("scenario_id")
    ]
    return {
        "bundle_id": manifest["bundle_id"],
        "producer": manifest["producer"],
        "created_at": manifest["created_at"],
        "source_path": manifest["_source_path"],
        "asset_count": len(manifest.get("assets", [])),
        "scenario_ids": scenario_ids,
        "required_runtime_args": list(manifest.get("required_runtime_args", [])),
        "secrets_policy": manifest["secrets_policy"],
        "kind": manifest["kind"],
    }


def _validate_base_url(value: str) -> str:
    value = (value or "").strip().rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RecipeBundleImportError("base_url must be an absolute http(s) URL")
    if parsed.query or parsed.fragment:
        raise RecipeBundleImportError("base_url must not contain query strings or fragments")
    return value


def _render(value: Any, args: dict[str, str]) -> Any:
    if isinstance(value, str):
        def replace(match: re.Match[str]) -> str:
            key = match.group(1)
            if key not in args:
                raise RecipeBundleImportError(f"Recipe bundle template arg is missing: {key}")
            return str(args[key])

        return _TEMPLATE_RE.sub(replace, value)
    if isinstance(value, list):
        return [_render(item, args) for item in value]
    if isinstance(value, dict):
        return {key: _render(nested, args) for key, nested in value.items()}
    return value


def _render_list(value: Any, args: dict[str, str]) -> list[str]:
    rendered = _render(value, args)
    if not isinstance(rendered, list) or not all(isinstance(item, str) for item in rendered):
        raise RecipeBundleImportError("Recipe bundle folder paths must be string lists")
    return rendered


def _unique_folders(folders: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    unique = []
    for folder in folders:
        path = tuple(folder["path"])
        if path in seen:
            continue
        seen.add(path)
        unique.append(folder)
    return unique


def _plan_summary(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "folder_count": len(plan.get("folders", [])),
        "template_count": len(plan.get("recipe_assets", [])),
        "scenario_ids": [asset["scenario_id"] for asset in plan.get("recipe_assets", [])],
        "folder_paths": [folder["path"] for folder in plan.get("folders", [])],
        "security": deepcopy(plan.get("security", {})),
        "export_contract": deepcopy(plan.get("export_contract", {})),
    }


def _humanize_scenario_id(value: str) -> str:
    return " ".join(part.capitalize() for part in value.replace("_", "-").split("-"))


def _assert_no_stored_secrets(
    value: Any,
    path: tuple[str, ...] = (),
    forbidden: set[str] | None = None,
) -> None:
    forbidden = forbidden or _FORBIDDEN_FIELD_FRAGMENTS
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            next_path = (*path, key_text)
            if _is_forbidden_key(key_text, forbidden) and nested not in (None, "", [], {}):
                raise RecipeBundleImportError(
                    f"Recipe bundle stores a forbidden field at {'.'.join(next_path)}"
                )
            _assert_no_stored_secrets(nested, next_path, forbidden)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_stored_secrets(item, (*path, str(index)), forbidden)


def _is_forbidden_key(key: str, forbidden: set[str]) -> bool:
    normalized = key.lower().replace("-", "_")
    for field in forbidden:
        if field == "pat":
            if normalized in {"pat", "personal_access_token"}:
                return True
            continue
        if field in normalized:
            return True
    return False
