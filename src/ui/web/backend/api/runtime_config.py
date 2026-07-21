"""
Runtime configuration for frontend deployments.

This endpoint is intentionally safe for unauthenticated bootstrap: it exposes
deployment shape and UI wiring, not secrets.
"""

import os
from fastapi import APIRouter

from gateway.config import get_gateway_config
from gateway.capabilities.definitions import DeploymentMode

router = APIRouter()


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _auth_mode(mode: DeploymentMode) -> str:
    if mode == DeploymentMode.ENTERPRISE:
        return "enterprise_jwt"
    if mode == DeploymentMode.OFFLINE:
        return "local_jwt"
    return "firebase"


def _raw_deployment_mode() -> str:
    return _env("DEPLOYMENT_MODE").lower().replace("-", "_")


def _deployment_label() -> str:
    raw = _raw_deployment_mode()
    if raw in {"airgap", "enterprise_airgap"}:
        return "enterprise_airgap"
    if raw in {"selfhosted", "self_hosted", "self_hosted_online"}:
        return "self_hosted_online"
    if raw in {"community", "oss", "open_source"}:
        return "community"
    cfg = get_gateway_config()
    if cfg.deployment_mode == DeploymentMode.ENTERPRISE:
        return "self_hosted_online"
    return cfg.deployment_mode.value


def _edition(label: str, mode: DeploymentMode) -> str:
    if label in {"community", "saas", "self_hosted_online", "enterprise_airgap"}:
        return label
    if mode == DeploymentMode.OFFLINE:
        return "community"
    return "saas"


def _license_class(edition: str) -> str:
    if edition == "community":
        return "apache_2"
    return "commercial"


def _providers(edition: str) -> dict[str, str]:
    if edition == "enterprise_airgap":
        return {
            "auth": "enterprise_jwt",
            "billing": "offline_license",
            "storage": "s3_compatible",
            "ai": "local_openai_compatible",
            "threatIntel": "offline_bundle",
        }
    if edition == "self_hosted_online":
        return {
            "auth": "enterprise_jwt",
            "billing": "offline_license",
            "storage": "s3_compatible",
            "ai": "openai",
            "threatIntel": "online_feed",
        }
    if edition == "community":
        return {
            "auth": "local_jwt",
            "billing": "none",
            "storage": "local_fs",
            "ai": "rules_only",
            "threatIntel": "offline_bundle",
        }
    return {
        "auth": "firebase",
        "billing": "stripe",
        "storage": "gcs",
        "ai": "openai",
        "threatIntel": "online_feed",
    }


def _hidden_surfaces(edition: str) -> list[str]:
    if edition == "community":
        return sorted({
            "billing",
            "payments",
            "marketplace",
            "creator_earnings",
            "social",
            "audit",
            "rbac",
            "sso",
            "redteam",
            "darkweb",
            "ai_governance",
        })
    if edition == "enterprise_airgap":
        return sorted({
            "billing",
            "payments",
            "marketplace",
            "creator_earnings",
            "social",
        })
    if edition == "self_hosted_online":
        return sorted({
            "billing",
            "payments",
            "creator_earnings",
            "social",
        })
    return []


def _unsupported_actions(edition: str) -> list[str]:
    if edition == "community":
        return sorted({
            "billing.checkout",
            "payment.manage",
            "marketplace.open",
            "audit.export",
            "redteam.run",
            "darkweb.monitor",
            "ai.workflow_mcp.call",
            "ai.agent_tool.call",
        })
    if edition == "enterprise_airgap":
        return sorted({
            "billing.checkout",
            "payment.manage",
            "marketplace.open",
        })
    if edition == "self_hosted_online":
        return sorted({
            "billing.checkout",
            "payment.manage",
        })
    return []


@router.get("/runtime-config")
async def runtime_config():
    cfg = get_gateway_config()
    deployment_label = _deployment_label()
    edition = _edition(deployment_label, cfg.deployment_mode)
    airgap = deployment_label == "enterprise_airgap"
    local_offline = cfg.deployment_mode == DeploymentMode.OFFLINE
    enterprise_backend_enabled = cfg.deployment_mode == DeploymentMode.ENTERPRISE

    return {
        "deploymentMode": deployment_label,
        "edition": edition,
        "licenseClass": _license_class(edition),
        "providers": _providers(edition),
        "authMode": _auth_mode(cfg.deployment_mode),
        "engineUrl": _env("FLYTO_ENGINE_URL", _env("VITE_ENGINE_URL", "")),
        "automationUrl": _env("FLYTO_AUTOMATION_URL", ""),
        "enterpriseBackendUrl": cfg.enterprise_backend_url if enterprise_backend_enabled else "",
        "deploymentId": _env("FLYTO_DEPLOYMENT_ID", "local"),
        "network": {
            "internetAllowed": not (airgap or local_offline),
            "airgap": airgap,
        },
        "unsupportedActions": _unsupported_actions(edition),
        "visibility": {
            "hiddenSurfaces": _hidden_surfaces(edition),
        },
    }
