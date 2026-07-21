"""Cloud CE capability routes without hosted billing or trial dependencies."""

from typing import Optional

from fastapi import APIRouter, Depends

from capabilities import (
    UIConfig,
    auto_init_context,
    get_capability_context,
    get_page_visibility,
    has_capability_context,
    reset_capability_context,
)
from capabilities.editions import get_cloud_edition_contract
from gateway.auth import get_optional_user
from gateway.providers.base import UserInfo


router = APIRouter(tags=["capabilities"])


def _context():
    return get_capability_context() if has_capability_context() else auto_init_context()


def _response(ctx, user: Optional[UserInfo]) -> dict:
    enabled = ctx.get_enabled_features()
    capabilities = [feature.value for feature in enabled]
    edition = get_cloud_edition_contract(
        ctx,
        pages=get_page_visibility(ctx),
        capabilities=capabilities,
    )
    capabilities = edition["capabilities"]
    ui = UIConfig.from_context(ctx).to_dict()
    ui.update({
        "showBilling": False,
        "showSubscriptions": False,
        "canUpgrade": False,
        "upgradeUrl": None,
        "upgradeFeatures": [],
    })
    return {
        "deploymentMode": ctx.deploy_mode.value,
        "licenseType": ctx.license_type.value,
        "billingMode": "disabled",
        "isLicensed": True,
        "isPro": False,
        "isAdmin": bool(user and user.is_admin),
        "capabilities": capabilities,
        "features": {name: True for name in capabilities},
        "pages": edition["pages"],
        "ui": ui,
        "proFeatures": {},
        "editionContract": edition,
        "contractVersion": edition["contract_version"],
        "product": edition["product"],
        "edition": edition["edition"],
        "editionProfile": edition["profile"],
        "editionDeployment": edition["deployment"],
        "authMode": edition["auth_mode"],
        "licenseMode": edition["license_mode"],
        "bridgePolicy": edition["bridge_policy"],
    }


@router.get("/capabilities")
async def get_capabilities(user: Optional[UserInfo] = Depends(get_optional_user)):
    return _response(_context(), user)


@router.post("/capabilities/reload")
async def reload_capabilities(user: Optional[UserInfo] = Depends(get_optional_user)):
    reset_capability_context()
    return _response(auto_init_context(), user)
