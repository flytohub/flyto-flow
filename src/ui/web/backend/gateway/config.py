"""
Gateway Configuration

Single source of truth for deployment mode.

All code MUST use get_gateway_config() instead of reading os.environ["DEPLOYMENT_MODE"].
The proxy adds X-Flyto2-Runner header so Cloud API knows request origin.

Four modes supported:
- cloud: Firebase + SaaS features
- local: Desktop app — cloud proxy auth, local execution
- offline: Fully self-contained — local JWT auth, SQLite data, no cloud dependency
- enterprise: PostgreSQL + LDAP/RBAC (connects to enterprise-backend on port 9191)
"""

import os
from typing import Optional
from dataclasses import dataclass
from functools import lru_cache

from gateway.capabilities.definitions import DeploymentMode


# Environment variable names
ENV_DEPLOYMENT_MODE = "DEPLOYMENT_MODE"
ENV_ENTERPRISE_BACKEND_URL = "ENTERPRISE_BACKEND_URL"

# Default values
DEFAULT_MODE = DeploymentMode.CLOUD
DEFAULT_ENTERPRISE_URL = "http://localhost:9191"

# ============================================================================
# Runner Header — identifies request origin when proxied to Cloud API
# ============================================================================
# Desktop proxy adds this header so Cloud API can distinguish:
#   - No header → direct call (SaaS frontend or external)
#   - "local"   → Desktop app proxied this request
#   - "enterprise" → Enterprise backend proxied this request
HEADER_RUNNER_MODE = "X-Flyto2-Runner"
LEGACY_HEADER_RUNNER_MODE = "X-" + "Flyto-" + "Runner"


@dataclass(frozen=True)
class GatewayConfig:
    """Immutable gateway configuration — single source of truth for deployment mode."""
    deployment_mode: DeploymentMode
    enterprise_backend_url: str = DEFAULT_ENTERPRISE_URL

    @property
    def is_cloud(self) -> bool:
        """Check if running in cloud deployment mode."""
        return self.deployment_mode == DeploymentMode.CLOUD

    @property
    def is_local(self) -> bool:
        """Check if running in local desktop deployment mode."""
        return self.deployment_mode == DeploymentMode.LOCAL

    @property
    def is_offline(self) -> bool:
        """Check if running in fully offline mode (no cloud dependency)."""
        return self.deployment_mode == DeploymentMode.OFFLINE

    @property
    def is_enterprise(self) -> bool:
        """Check if running in enterprise deployment mode."""
        return self.deployment_mode == DeploymentMode.ENTERPRISE

    @property
    def is_worker(self) -> bool:
        """Check if running as a cloud browser worker."""
        return self.deployment_mode == DeploymentMode.WORKER

    @property
    def runner_header_value(self) -> str:
        """Value to send as X-Flyto2-Runner header when proxying to Cloud API."""
        return self.deployment_mode.value

def _detect_deployment_mode() -> DeploymentMode:
    """
    Detect deployment mode from environment variable.

    Environment variable: DEPLOYMENT_MODE
    Valid values:
        - cloud, saas -> CLOUD mode (Firebase)
    - enterprise, selfhosted, self_hosted_online, airgap, enterprise_airgap -> ENTERPRISE mode
      (On-prem/private, connects to enterprise-backend)
    Default: cloud

    Supports backward compatibility with existing 'saas'/'selfhosted' values
    from settings.py.
    """
    mode_str = os.environ.get(ENV_DEPLOYMENT_MODE, "").lower().strip()

    # Map to LOCAL mode (desktop app)
    if mode_str == "local":
        return DeploymentMode.LOCAL

    # Map to OFFLINE mode (fully local, no cloud dependency)
    if mode_str == "offline":
        return DeploymentMode.OFFLINE

    # Map to WEB mode (lightweight frontend server + proxy)
    if mode_str == "web":
        return DeploymentMode.WEB

    # Map to WORKER mode (execution engine with Chrome)
    if mode_str == "worker":
        return DeploymentMode.WORKER

    # Map to ENTERPRISE mode
    if mode_str in ("enterprise", "selfhosted", "self_hosted", "self_hosted_online", "airgap", "enterprise_airgap"):
        return DeploymentMode.ENTERPRISE

    # Default to CLOUD
    return DeploymentMode.CLOUD


def _get_enterprise_backend_url() -> str:
    """Get enterprise backend URL from environment."""
    return os.environ.get(ENV_ENTERPRISE_BACKEND_URL, DEFAULT_ENTERPRISE_URL)


@lru_cache(maxsize=1)
def get_gateway_config() -> GatewayConfig:
    """
    Get gateway configuration (cached singleton).

    Returns:
        GatewayConfig with detected deployment mode
    """
    mode = _detect_deployment_mode()
    enterprise_url = _get_enterprise_backend_url()
    return GatewayConfig(
        deployment_mode=mode,
        enterprise_backend_url=enterprise_url,
    )


def reset_gateway_config() -> None:
    """Reset gateway config cache (for testing)."""
    get_gateway_config.cache_clear()


def get_runner_mode(request) -> Optional[str]:
    """
    Extract runner mode from request's X-Flyto2-Runner header.

    Returns:
        "local", "enterprise", "worker", or None (direct cloud/SaaS call)
    """
    return request.headers.get(HEADER_RUNNER_MODE) or request.headers.get(LEGACY_HEADER_RUNNER_MODE)


def is_proxied_from_desktop(request) -> bool:
    """Check if this request was proxied from a Desktop app."""
    return get_runner_mode(request) == DeploymentMode.LOCAL.value


def is_proxied_from_enterprise(request) -> bool:
    """Check if this request was proxied from an Enterprise backend."""
    return get_runner_mode(request) == DeploymentMode.ENTERPRISE.value


def validate_runner_header(request) -> Optional[str]:
    """
    Validate X-Flyto2-Runner header (defense-in-depth).

    Security model:
    - Authenticated endpoints: Bearer token proves identity; runner header is
      informational only (tells Cloud API the request origin).
    - Unauthenticated endpoints (webhook trigger): runner header is ignored;
      webhook HMAC is the sole auth mechanism.

    This function logs a warning if a runner header is present without a valid
    Authorization header, which may indicate header forgery. It never blocks
    requests — blocking is the job of auth middleware.

    Returns:
        The runner mode string if present, None otherwise.
    """
    import logging

    runner = get_runner_mode(request)
    if runner is None:
        return None

    auth_header = request.headers.get("authorization", "")
    if runner and not auth_header.startswith("Bearer "):
        _logger = logging.getLogger(__name__)
        _logger.warning(
            f"{HEADER_RUNNER_MODE}={runner!r} present without Bearer token — "
            f"header may be forged (client={getattr(request.client, 'host', 'unknown')})"
        )

    return runner
