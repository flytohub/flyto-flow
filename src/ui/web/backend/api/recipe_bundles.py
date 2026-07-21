"""Recipe bundle import routes."""

import logging
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from gateway.auth import get_current_user
from gateway.providers.hub import get_data_provider
from services.recipe_bundles import (
    WARROOM_BUNDLE_ID,
    RecipeBundleImportError,
    WarroomRecipeBundleImporter,
    list_public_recipe_bundles,
    scan_warroom_bundle_inbox,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recipe-bundles")


def _current_user_id(current_user: object) -> str:
    """Return a user id from gateway auth in cloud or offline mode."""
    if isinstance(current_user, dict):
        user_id = current_user.get("id")
    else:
        user_id = getattr(current_user, "id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authenticated user id missing")
    return user_id


class ImportWarroomBundleRequest(BaseModel):
    """Request to import the Flyto2 Warroom recipe bundle."""

    project_slug: str = Field(..., min_length=1, max_length=80)
    base_url: str = Field(..., min_length=8, max_length=500)
    bundle_id: Optional[str] = Field(default=WARROOM_BUNDLE_ID)
    source_path: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional pending signed bundle path from the local import inbox.",
    )
    dry_run: bool = False


class ImportWarroomBundleResponse(BaseModel):
    ok: bool
    bundle_id: Optional[str] = None
    project_slug: Optional[str] = None
    root_folder: Optional[str] = None
    dry_run: bool = False
    plan: Optional[dict] = None
    folders: list[dict] = Field(default_factory=list)
    templates: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    folder_count: int = 0
    template_count: int = 0
    created_count: int = 0
    updated_count: int = 0
    scenario_ids: list[str] = Field(default_factory=list)
    folder_paths: list[list[str]] = Field(default_factory=list)
    security: dict = Field(default_factory=dict)
    export_contract: dict = Field(default_factory=dict)
    error: Optional[str] = None


class PublicRecipeBundle(BaseModel):
    bundle_id: str
    display_name: str
    description: str
    asset_kind: str = "mcp_recipe_bundle"
    official_bundle: bool = True
    install_target: str = "private_warroom"
    pricing: str = "free"
    category: str = "testing"
    folder_count: int = 0
    template_count: int = 0
    scenario_ids: list[str] = Field(default_factory=list)
    folder_paths: list[list[str]] = Field(default_factory=list)
    runtime_required_args: list[str] = Field(default_factory=list)
    security: dict = Field(default_factory=dict)
    export_contract: dict = Field(default_factory=dict)


class PublicRecipeBundleListResponse(BaseModel):
    ok: bool = True
    bundles: list[PublicRecipeBundle] = Field(default_factory=list)


class PendingWarroomBundle(BaseModel):
    bundle_id: str
    producer: str
    created_at: str
    source_path: str
    asset_count: int = 0
    scenario_ids: list[str] = Field(default_factory=list)
    required_runtime_args: list[str] = Field(default_factory=list)
    secrets_policy: str
    kind: str


class RejectedWarroomBundle(BaseModel):
    source_path: str
    error: str


class WarroomBundleInboxResponse(BaseModel):
    ok: bool = True
    import_dir: Optional[str] = None
    pending: list[PendingWarroomBundle] = Field(default_factory=list)
    rejected: list[RejectedWarroomBundle] = Field(default_factory=list)


class InstallRecipeBundleRequest(BaseModel):
    """Request to install an official recipe bundle into a private Warroom tree."""

    project_slug: str = Field(..., min_length=1, max_length=80)
    base_url: str = Field(..., min_length=8, max_length=500)
    target: Literal["private_warroom"] = "private_warroom"
    dry_run: bool = False


class ApproveWarroomBundleRequest(BaseModel):
    """Approve a pending signed Warroom bundle and promote it into templates."""

    source_path: str = Field(..., min_length=1, max_length=1000)
    project_slug: str = Field(..., min_length=1, max_length=80)
    base_url: str = Field(..., min_length=8, max_length=500)
    bundle_id: Optional[str] = Field(default=WARROOM_BUNDLE_ID)
    dry_run: bool = False


@router.get("/public", response_model=PublicRecipeBundleListResponse)
async def list_public_recipe_bundle_catalog():
    """List official public recipe bundles available from Marketplace."""

    try:
        return PublicRecipeBundleListResponse(
            bundles=[PublicRecipeBundle(**bundle) for bundle in list_public_recipe_bundles()],
        )
    except RecipeBundleImportError as exc:
        logger.warning("Public recipe bundle catalog is unavailable: %s", exc)
        raise HTTPException(status_code=503, detail="Recipe bundle catalog unavailable") from exc


@router.post("/{bundle_id}/install", response_model=ImportWarroomBundleResponse)
async def install_public_recipe_bundle(
    bundle_id: str,
    request: InstallRecipeBundleRequest,
    current_user: dict = Depends(get_current_user),
):
    """Install an official public recipe bundle into the user's private Warroom folders."""

    if bundle_id != WARROOM_BUNDLE_ID:
        raise HTTPException(status_code=404, detail="Recipe bundle not found")
    if request.target != "private_warroom":
        raise HTTPException(status_code=400, detail="Unsupported recipe bundle install target")

    provider = get_data_provider()
    if provider is None or getattr(provider, "templates", None) is None:
        raise HTTPException(status_code=503, detail="Template provider unavailable")

    try:
        result = await WarroomRecipeBundleImporter(provider).import_bundle(
            user_id=_current_user_id(current_user),
            project_slug=request.project_slug,
            base_url=request.base_url,
            dry_run=request.dry_run,
        )
        return ImportWarroomBundleResponse(**result)
    except RecipeBundleImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Public recipe bundle install failed")
        raise HTTPException(status_code=500, detail="Recipe bundle install failed") from exc


@router.get("/import-warroom/pending", response_model=WarroomBundleInboxResponse)
async def list_pending_warroom_bundle_imports(
    current_user: dict = Depends(get_current_user),
):
    """List signed Warroom bundles pending approval from the local import inbox."""

    try:
        return WarroomBundleInboxResponse(**scan_warroom_bundle_inbox())
    except RecipeBundleImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import-warroom/scan", response_model=WarroomBundleInboxResponse)
async def scan_pending_warroom_bundle_imports(
    current_user: dict = Depends(get_current_user),
):
    """Rescan the local signed Warroom bundle import inbox."""

    try:
        return WarroomBundleInboxResponse(**scan_warroom_bundle_inbox())
    except RecipeBundleImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import-warroom/approve", response_model=ImportWarroomBundleResponse)
async def approve_warroom_recipe_bundle(
    request: ApproveWarroomBundleRequest,
    current_user: dict = Depends(get_current_user),
):
    """Approve a pending signed Warroom bundle and import it as private templates."""

    if request.bundle_id != WARROOM_BUNDLE_ID:
        raise HTTPException(status_code=400, detail="Unsupported recipe bundle")

    provider = get_data_provider()
    if provider is None or getattr(provider, "templates", None) is None:
        raise HTTPException(status_code=503, detail="Template provider unavailable")

    try:
        result = await WarroomRecipeBundleImporter(provider).import_bundle(
            user_id=_current_user_id(current_user),
            project_slug=request.project_slug,
            base_url=request.base_url,
            source_path=request.source_path,
            dry_run=request.dry_run,
        )
        return ImportWarroomBundleResponse(**result)
    except RecipeBundleImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Warroom recipe bundle approval failed")
        raise HTTPException(status_code=500, detail="Recipe bundle approval failed") from exc


@router.post("/import-warroom", response_model=ImportWarroomBundleResponse)
async def import_warroom_recipe_bundle(
    request: ImportWarroomBundleRequest,
    current_user: dict = Depends(get_current_user),
):
    """Import reusable Flyto2 Warroom MCP recipes into the user's folders."""

    if request.bundle_id != WARROOM_BUNDLE_ID:
        raise HTTPException(status_code=400, detail="Unsupported recipe bundle")

    provider = get_data_provider()
    if provider is None or getattr(provider, "templates", None) is None:
        raise HTTPException(status_code=503, detail="Template provider unavailable")

    try:
        result = await WarroomRecipeBundleImporter(provider).import_bundle(
            user_id=_current_user_id(current_user),
            project_slug=request.project_slug,
            base_url=request.base_url,
            source_path=request.source_path,
            dry_run=request.dry_run,
        )
        return ImportWarroomBundleResponse(**result)
    except RecipeBundleImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Warroom recipe bundle import failed")
        raise HTTPException(status_code=500, detail="Recipe bundle import failed") from exc
