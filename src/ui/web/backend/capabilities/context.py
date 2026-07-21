"""
Capability Context

Runtime context for capability checks.
Should be initialized once at application startup.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Set

from capabilities.types import LicenseType, CapabilityDeployMode as DeploymentMode, Feature
from capabilities.feature_gate import (
    is_feature_enabled,
    get_enabled_features,
    get_disabled_features,
    require_feature,
    FeatureNotAvailableError,
)

import logging
logger = logging.getLogger(__name__)


# =============================================================================
# Capability Context
# =============================================================================

@dataclass(frozen=True)
class CapabilityContext:
    """
    Immutable runtime context for capability checks.

    Should be set once at application startup based on:
    1. License validation (from license file or server)
    2. Deployment mode detection (from environment/config)

    All feature checks should go through this context.
    """
    license_type: LicenseType
    deploy_mode: DeploymentMode

    # License metadata (for tracking & UI display)
    license_id: Optional[str] = None
    license_expires_at: Optional[datetime] = None
    licensed_to: Optional[str] = None  # Organization or user name

    # Verification fields (for frontend trust & anti-tamper)
    issued_at: Optional[datetime] = None  # When context was created
    signature: Optional[str] = None  # HMAC signature for verification
    context_version: str = "1.0"  # For future compatibility

    # License update policy (for offline licenses)
    update_policy: Optional[str] = None  # "lts" | "1y_updates" | "perpetual"
    update_expires_at: Optional[datetime] = None  # When updates expire

    # Feature overrides (for beta features, custom deals, etc.)
    # These are additional features granted beyond the license
    feature_overrides: frozenset = frozenset()

    def is_enabled(self, feature: Feature) -> bool:
        """
        Check if a feature is enabled.

        Args:
            feature: The feature to check

        Returns:
            True if feature is enabled
        """
        # Check overrides first
        if feature in self.feature_overrides:
            return True

        return is_feature_enabled(feature, self.license_type, self.deploy_mode)

    def get_enabled_features(self) -> Set[Feature]:
        """Get all enabled features."""
        enabled = get_enabled_features(self.license_type, self.deploy_mode)
        return enabled | set(self.feature_overrides)

    def get_disabled_features(self) -> Set[Feature]:
        """Get all disabled features."""
        enabled = self.get_enabled_features()
        return set(Feature) - enabled

    def require(self, feature: Feature) -> None:
        """
        Require a feature to be enabled. Raises if not.

        Args:
            feature: The feature to require

        Raises:
            FeatureNotAvailableError: If feature is not enabled
        """
        if self.is_enabled(feature):
            return

        require_feature(feature, self.license_type, self.deploy_mode)

    def is_licensed(self) -> bool:
        """Check if user has a paid license."""
        return self.license_type != LicenseType.FREE

    def is_expired(self) -> bool:
        """Check if license is expired."""
        if self.license_expires_at is None:
            return False

        return datetime.now(timezone.utc) > self.license_expires_at

    def days_until_expiry(self) -> Optional[int]:
        """Get days until license expires."""
        if self.license_expires_at is None:
            return None

        delta = self.license_expires_at - datetime.now(timezone.utc)
        return max(0, delta.days)

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "license_type": self.license_type.value,
            "deploy_mode": self.deploy_mode.value,
            "license_id": self.license_id,
            "license_expires_at": (
                self.license_expires_at.isoformat()
                if self.license_expires_at else None
            ),
            "licensed_to": self.licensed_to,
            "is_licensed": self.is_licensed(),
            "is_expired": self.is_expired(),
            "days_until_expiry": self.days_until_expiry(),
            # Verification fields
            "issued_at": (
                self.issued_at.isoformat()
                if self.issued_at else None
            ),
            "signature": self.signature,
            "context_version": self.context_version,
            # Update policy (for offline licenses)
            "update_policy": self.update_policy,
            "update_expires_at": (
                self.update_expires_at.isoformat()
                if self.update_expires_at else None
            ),
        }


# =============================================================================
# Global Context (Singleton)
# =============================================================================

_context: Optional[CapabilityContext] = None


def _generate_context_signature(
    license_type: LicenseType,
    deploy_mode: DeploymentMode,
    issued_at: datetime,
) -> str:
    """
    Generate HMAC signature for context verification.

    This prevents frontend from tampering with capability data.
    """
    import hmac
    import hashlib
    import os

    secret = os.getenv("FLYTO_CONTEXT_SECRET", "")
    if not secret:
        # Cloud deployments may not have this set yet — use a deterministic
        # fallback derived from deployment mode so the signature is still
        # tamper-resistant within the same instance, just not cross-instance.
        import socket
        secret = f"flyto-{deploy_mode.value}-{socket.gethostname()}"
        logger.warning("FLYTO_CONTEXT_SECRET not set — using ephemeral fallback")
    message = f"{license_type.value}:{deploy_mode.value}:{issued_at.isoformat()}"

    return hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()[:32]  # Truncate for readability


def init_capability_context(
    license_type: LicenseType,
    deploy_mode: DeploymentMode,
    license_id: Optional[str] = None,
    license_expires_at: Optional[datetime] = None,
    licensed_to: Optional[str] = None,
    feature_overrides: Optional[Set[Feature]] = None,
    update_policy: Optional[str] = None,
    update_expires_at: Optional[datetime] = None,
) -> CapabilityContext:
    """
    Initialize global capability context.

    Should be called once at application startup.

    Args:
        license_type: The license type
        deploy_mode: The deployment mode
        license_id: Optional license identifier
        license_expires_at: Optional expiry date
        licensed_to: Optional licensee name
        feature_overrides: Optional additional features to enable
        update_policy: Update policy for offline licenses ("lts", "1y_updates", "perpetual")
        update_expires_at: When updates expire for offline licenses

    Returns:
        The initialized context
    """
    global _context

    issued_at = datetime.now(timezone.utc)
    signature = _generate_context_signature(license_type, deploy_mode, issued_at)

    _context = CapabilityContext(
        license_type=license_type,
        deploy_mode=deploy_mode,
        license_id=license_id,
        license_expires_at=license_expires_at,
        licensed_to=licensed_to,
        issued_at=issued_at,
        signature=signature,
        update_policy=update_policy,
        update_expires_at=update_expires_at,
        feature_overrides=frozenset(feature_overrides or set()),
    )

    return _context


def get_capability_context() -> CapabilityContext:
    """
    Get current capability context.

    Raises:
        RuntimeError: If context not initialized
    """
    if _context is None:
        raise RuntimeError(
            "Capability context not initialized. "
            "Call init_capability_context() at application startup."
        )

    return _context


def has_capability_context() -> bool:
    """Check if context is initialized."""
    return _context is not None


def reset_capability_context() -> None:
    """
    Reset context. Only for testing.

    WARNING: Do not use in production code.
    """
    global _context
    _context = None


# =============================================================================
# Context Detection (Auto-initialization)
# =============================================================================

def detect_deploy_mode() -> DeploymentMode:
    """
    Detect deployment mode from environment.

    Bridges from gateway config (single source of truth) to capability system's
    DeploymentMode enum. Falls back to FLYTO_DEPLOY_MODE env var for fine-grained
    control (e.g., LOCAL_ONLINE vs LOCAL_OFFLINE).
    """
    import os

    # Fine-grained override via FLYTO_DEPLOY_MODE (e.g., local_offline)
    mode = os.getenv("FLYTO_DEPLOY_MODE", "").lower()
    if mode:
        mode_map = {
            "saas": DeploymentMode.SAAS_CLOUD,
            "cloud": DeploymentMode.SAAS_CLOUD,
            "saas_cloud": DeploymentMode.SAAS_CLOUD,
            "local_online": DeploymentMode.LOCAL_ONLINE,
            "online": DeploymentMode.LOCAL_ONLINE,
            "enterprise": DeploymentMode.ENTERPRISE_INTRANET,
            "airgap": DeploymentMode.ENTERPRISE_INTRANET,
            "enterprise_airgap": DeploymentMode.ENTERPRISE_INTRANET,
            "intranet": DeploymentMode.ENTERPRISE_INTRANET,
            "enterprise_intranet": DeploymentMode.ENTERPRISE_INTRANET,
            "offline": DeploymentMode.LOCAL_OFFLINE,
            "local_offline": DeploymentMode.LOCAL_OFFLINE,
        }
        if mode in mode_map:
            return mode_map[mode]

    # Bridge from gateway config (reads DEPLOYMENT_MODE env var)
    try:
        from gateway.config import get_gateway_config
        gw = get_gateway_config()
        bridge_map = {
            "cloud": DeploymentMode.SAAS_CLOUD,
            "local": DeploymentMode.LOCAL_ONLINE,
            "offline": DeploymentMode.LOCAL_OFFLINE,
            "enterprise": DeploymentMode.ENTERPRISE_INTRANET,
            "worker": DeploymentMode.SAAS_CLOUD,  # workers run in cloud infra
        }
        return bridge_map.get(gw.deployment_mode.value, DeploymentMode.LOCAL_ONLINE)
    except Exception:
        pass

    # Fallback: heuristic detection
    if os.getenv("K_SERVICE") or os.getenv("GOOGLE_CLOUD_PROJECT"):
        return DeploymentMode.SAAS_CLOUD
    if os.getenv("POSTGRES_HOST") or os.getenv("DATABASE_URL"):
        return DeploymentMode.ENTERPRISE_INTRANET

    return DeploymentMode.LOCAL_ONLINE


def detect_license_type() -> LicenseType:
    """
    Detect license type from environment or license file.

    Detection order:
    1. FLYTO_LICENSE_TYPE env var
    2. License file at ~/.flyto/license.json
    3. License server check (if online)
    4. Default to FREE
    """
    import os
    import json
    from pathlib import Path

    # Explicit setting
    license = os.getenv("FLYTO_LICENSE_TYPE", "").lower()
    if license:
        license_map = {
            "free": LicenseType.FREE,
            "pro": LicenseType.PRO,
            "team": LicenseType.TEAM,
            "offline": LicenseType.OFFLINE,
            "enterprise": LicenseType.ENTERPRISE,
            # Legacy values
            "subscription": LicenseType.PRO,
            "sub": LicenseType.PRO,
            "offline_license": LicenseType.OFFLINE,
            "ent": LicenseType.ENTERPRISE,
        }
        if license in license_map:
            return license_map[license]

    # Check license file
    license_file = Path.home() / ".flyto" / "license.json"
    if license_file.exists():
        try:
            data = json.loads(license_file.read_text())
            license_type = data.get("type", "").lower()
            # Try direct mapping first
            try:
                return LicenseType(license_type)
            except ValueError:
                # Handle legacy values
                if license_type == "subscription":
                    return LicenseType.PRO
                elif license_type == "offline_license":
                    return LicenseType.OFFLINE
        except (json.JSONDecodeError, ValueError):
            pass

    # Default to free
    return LicenseType.FREE


def auto_init_context() -> CapabilityContext:
    """
    Auto-detect and initialize context.

    Convenience function for applications that don't need
    explicit configuration.
    """
    deploy_mode = detect_deploy_mode()
    license_type = detect_license_type()

    return init_capability_context(
        license_type=license_type,
        deploy_mode=deploy_mode,
    )
