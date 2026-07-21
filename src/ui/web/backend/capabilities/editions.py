"""
Edition contract helpers for Flyto2 Cloud.

flyto.editions.v1 is the shared delivery contract used by UI, API, MCP, and
Cloud/Warroom bridge checks. It is additive to the existing capability enum so
older clients can continue reading deploymentMode/licenseType/capabilities.
"""

import os
from copy import deepcopy
from typing import Dict, Iterable, Mapping, Optional

from capabilities.context import CapabilityContext
from capabilities.types import CapabilityDeployMode as DeploymentMode
from capabilities.types import LicenseType


CONTRACT_VERSION = "flyto.editions.v1"
PRODUCT = "cloud"

CORE_PAGES = {
    "/": True,
    "/login": True,
    "/dashboard": True,
    "/my-templates": True,
    "/templates": True,
    "/templates/*": True,
    "/templates/builder": True,
    "/templates/builder/*": True,
    "/workflows": True,
    "/workflows/*": True,
    "/recipe-bundles": True,
    "/recipe-bundles/*": True,
    "/mcp": True,
    "/mcp/*": True,
    "/tools": True,
    "/variables": True,
    "/settings": True,
}

COMMERCIAL_PAGES = {
    "/marketplace": False,
    "/marketplace/*": False,
    "/billing": False,
    "/payment": False,
    "/payment/*": False,
    "/purchases": False,
    "/wallet": False,
    "/subscription": False,
    "/creator": False,
    "/settings/payout": False,
    "/messages": False,
}

ENTERPRISE_PAGES = {
    "/settings/organization": False,
    "/settings/projects": False,
    "/settings/roles": False,
    "/admin": False,
    "/admin/*": False,
    "/admin/org": False,
    "/admin/rbac": False,
    "/admin/sso": False,
}

COMMON_CAPABILITIES = [
    "workflow.builder",
    "workflow.local_execution",
    "template.import",
    "mcp.server",
    "mcp.workflow_tools",
    "warroom.bundle_inbox",
]

PROFILE_CONTRACTS = {
    "cloud_saas": {
        "edition": "saas",
        "deployment": "hosted",
        "auth_mode": "flyto_account_oidc",
        "license_mode": "subscription",
        "capabilities": COMMON_CAPABILITIES + [
            "marketplace.hosted",
            "billing.stripe",
            "runner.managed",
            "cloud.bridge",
        ],
        "pages": {
            **CORE_PAGES,
            **{key: True for key in COMMERCIAL_PAGES},
            **ENTERPRISE_PAGES,
        },
        "bridge_policy": {
            "warroom_import": "signed_bundle_required",
            "cloud_bridge": "managed",
            "allow_unsigned_bundles": False,
            "network_required": True,
        },
    },
    "cloud_ce": {
        "edition": "ce",
        "deployment": "local_offline",
        "auth_mode": "local_jwt",
        "license_mode": "open_source_ce",
        "capabilities": COMMON_CAPABILITIES + [
            "storage.sqlite",
            "auth.local_setup",
        ],
        "pages": {
            **CORE_PAGES,
            **COMMERCIAL_PAGES,
            **ENTERPRISE_PAGES,
        },
        "bridge_policy": {
            "warroom_import": "signed_bundle_required",
            "cloud_bridge": "disabled",
            "allow_unsigned_bundles": False,
            "network_required": False,
        },
    },
    "cloud_enterprise_selfhost": {
        "edition": "enterprise",
        "deployment": "self_host",
        "auth_mode": "enterprise_idp_or_local_jwt",
        "license_mode": "commercial_enterprise",
        "capabilities": COMMON_CAPABILITIES + [
            "registry.private_mcp",
            "auth.sso",
            "rbac.team",
            "cloud.bridge.optional",
        ],
        "pages": {
            **CORE_PAGES,
            **COMMERCIAL_PAGES,
            **{key: True for key in ENTERPRISE_PAGES},
        },
        "bridge_policy": {
            "warroom_import": "signed_bundle_required",
            "cloud_bridge": "optional_signed_short_lived_token",
            "allow_unsigned_bundles": False,
            "network_required": False,
        },
    },
    "cloud_enterprise_airgap": {
        "edition": "airgap",
        "deployment": "airgap",
        "auth_mode": "enterprise_idp_or_local_jwt",
        "license_mode": "signed_offline_license",
        "capabilities": COMMON_CAPABILITIES + [
            "registry.private_mcp",
            "auth.sso_optional",
            "rbac.team",
            "updates.offline_bundle",
        ],
        "pages": {
            **CORE_PAGES,
            **COMMERCIAL_PAGES,
            **{key: True for key in ENTERPRISE_PAGES},
        },
        "bridge_policy": {
            "warroom_import": "signed_bundle_required",
            "cloud_bridge": "disabled",
            "allow_unsigned_bundles": False,
            "network_required": False,
        },
    },
}


def resolve_cloud_profile(ctx: CapabilityContext) -> str:
    """Resolve Cloud edition profile from explicit override or context."""
    override = os.getenv("FLYTO_EDITION_PROFILE", "").strip().lower()
    if override in PROFILE_CONTRACTS:
        return override

    if ctx.deploy_mode == DeploymentMode.SAAS_CLOUD:
        return "cloud_saas"
    if ctx.deploy_mode == DeploymentMode.ENTERPRISE_INTRANET:
        if os.getenv("FLYTO_AIRGAP", "").strip().lower() in {"1", "true", "yes", "on"}:
            return "cloud_enterprise_airgap"
        if ctx.license_type in {LicenseType.ENTERPRISE, LicenseType.OFFLINE}:
            return "cloud_enterprise_selfhost"

    return "cloud_ce"


def _merge_pages(base_pages: Mapping[str, bool], edition_pages: Mapping[str, bool]) -> Dict[str, bool]:
    merged = dict(base_pages)
    merged.update(edition_pages)
    return merged


def get_cloud_edition_contract(
    ctx: CapabilityContext,
    *,
    pages: Optional[Mapping[str, bool]] = None,
    capabilities: Optional[Iterable[str]] = None,
) -> Dict[str, object]:
    """Build the flyto.editions.v1 contract for Cloud."""
    profile = resolve_cloud_profile(ctx)
    profile_contract = deepcopy(PROFILE_CONTRACTS[profile])
    contract_pages = _merge_pages(pages or {}, profile_contract["pages"])
    contract_capabilities = list(dict.fromkeys([
        *(capabilities or []),
        *profile_contract["capabilities"],
    ]))

    return {
        "contract_version": CONTRACT_VERSION,
        "profile": profile,
        "product": PRODUCT,
        "edition": profile_contract["edition"],
        "deployment": profile_contract["deployment"],
        "auth_mode": profile_contract["auth_mode"],
        "license_mode": profile_contract["license_mode"],
        "capabilities": contract_capabilities,
        "pages": contract_pages,
        "bridge_policy": profile_contract["bridge_policy"],
    }
