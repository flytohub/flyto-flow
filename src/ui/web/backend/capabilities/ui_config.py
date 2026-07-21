"""
UI Configuration

Configuration for frontend UI visibility based on capabilities.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from capabilities.types import Feature, LicenseType, CapabilityDeployMode as DeploymentMode
from capabilities.context import CapabilityContext


@dataclass
class UIConfig:
    """
    Configuration for frontend UI visibility.

    Frontend should call /api/ui-config on startup and use this to:
    - Show/hide navigation items
    - Enable/disable feature buttons
    - Display license information
    - Show upgrade prompts
    """

    # -------------------------------------------------------------------------
    # Navigation Visibility
    # -------------------------------------------------------------------------
    show_marketplace: bool = False
    show_billing: bool = False
    show_observability: bool = False
    show_versioning: bool = False
    show_audit: bool = False
    show_org_settings: bool = False
    show_rbac_settings: bool = False
    show_sso_settings: bool = False
    show_subscriptions: bool = False

    # -------------------------------------------------------------------------
    # Feature Availability
    # -------------------------------------------------------------------------
    can_sync_cloud: bool = False
    can_export_prometheus: bool = False
    can_use_sso: bool = False
    can_replay_execution: bool = False
    can_rerun_execution: bool = False
    can_debug_execution: bool = False

    # -------------------------------------------------------------------------
    # License Information
    # -------------------------------------------------------------------------
    license_type: str = "free"
    deploy_mode: str = "local_offline"
    is_licensed: bool = False
    is_expired: bool = False
    days_until_expiry: Optional[int] = None
    licensed_to: Optional[str] = None

    # -------------------------------------------------------------------------
    # Enabled Features List (for dynamic UI)
    # -------------------------------------------------------------------------
    enabled_features: List[str] = None

    # -------------------------------------------------------------------------
    # Upgrade Information
    # -------------------------------------------------------------------------
    can_upgrade: bool = True
    upgrade_url: Optional[str] = None
    upgrade_features: List[str] = None  # Features unlocked by upgrading

    @classmethod
    def from_context(cls, ctx: CapabilityContext) -> "UIConfig":
        """
        Create UI config from capability context.

        Args:
            ctx: The capability context

        Returns:
            UIConfig instance
        """
        from capabilities.feature_gate import get_disabled_features
        from capabilities.license_grants import get_upgrade_features

        # Get enabled features
        enabled = ctx.get_enabled_features()
        enabled_ids = [f.value for f in enabled]

        # Calculate upgrade features (what you'd get with pro)
        upgrade_target = (
            LicenseType.PRO
            if ctx.license_type == LicenseType.FREE
            else LicenseType.ENTERPRISE
        )
        upgrade_features = get_upgrade_features(ctx.license_type, upgrade_target)
        upgrade_feature_ids = [f.value for f in upgrade_features]

        return cls(
            # Navigation
            show_marketplace=ctx.is_enabled(Feature.MARKETPLACE_BROWSE),
            show_billing=ctx.is_enabled(Feature.BILLING_STRIPE),
            show_observability=(
                ctx.is_enabled(Feature.LOCAL_METRICS) or
                ctx.is_enabled(Feature.HOSTED_OBSERVABILITY)
            ),
            show_versioning=ctx.is_enabled(Feature.LOCAL_VERSIONING),
            show_audit=ctx.is_enabled(Feature.LOCAL_AUDIT),
            show_org_settings=ctx.is_enabled(Feature.ORG_STRUCTURE),
            show_rbac_settings=ctx.is_enabled(Feature.RBAC_FULL),
            show_sso_settings=any([
                ctx.is_enabled(Feature.SSO_LDAP),
                ctx.is_enabled(Feature.SSO_SAML),
                ctx.is_enabled(Feature.SSO_OIDC),
            ]),
            show_subscriptions=ctx.is_enabled(Feature.BILLING_STRIPE),

            # Features
            can_sync_cloud=ctx.is_enabled(Feature.CLOUD_SYNC),
            can_export_prometheus=ctx.is_enabled(Feature.EXPORT_PROMETHEUS),
            can_use_sso=any([
                ctx.is_enabled(Feature.SSO_LDAP),
                ctx.is_enabled(Feature.SSO_SAML),
                ctx.is_enabled(Feature.SSO_OIDC),
            ]),
            can_replay_execution=ctx.is_enabled(Feature.EXECUTION_REPLAY),
            can_rerun_execution=ctx.is_enabled(Feature.EXECUTION_RERUN),
            can_debug_execution=ctx.is_enabled(Feature.EXECUTION_DEBUG),

            # License
            license_type=ctx.license_type.value,
            deploy_mode=ctx.deploy_mode.value,
            is_licensed=ctx.is_licensed(),
            is_expired=ctx.is_expired(),
            days_until_expiry=ctx.days_until_expiry(),
            licensed_to=ctx.licensed_to,

            # Features list
            enabled_features=enabled_ids,

            # Upgrade
            can_upgrade=ctx.license_type == LicenseType.FREE,
            upgrade_url="/pricing" if ctx.license_type == LicenseType.FREE else None,
            upgrade_features=upgrade_feature_ids,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            # Navigation
            "showMarketplace": self.show_marketplace,
            "showBilling": self.show_billing,
            "showObservability": self.show_observability,
            "showVersioning": self.show_versioning,
            "showAudit": self.show_audit,
            "showOrgSettings": self.show_org_settings,
            "showRbacSettings": self.show_rbac_settings,
            "showSsoSettings": self.show_sso_settings,
            "showSubscriptions": self.show_subscriptions,

            # Features
            "canSyncCloud": self.can_sync_cloud,
            "canExportPrometheus": self.can_export_prometheus,
            "canUseSso": self.can_use_sso,
            "canReplayExecution": self.can_replay_execution,
            "canRerunExecution": self.can_rerun_execution,
            "canDebugExecution": self.can_debug_execution,

            # License
            "licenseType": self.license_type,
            "deployMode": self.deploy_mode,
            "isLicensed": self.is_licensed,
            "isExpired": self.is_expired,
            "daysUntilExpiry": self.days_until_expiry,
            "licensedTo": self.licensed_to,

            # Features list
            "enabledFeatures": self.enabled_features or [],

            # Upgrade
            "canUpgrade": self.can_upgrade,
            "upgradeUrl": self.upgrade_url,
            "upgradeFeatures": self.upgrade_features or [],
        }


# =============================================================================
# Page Visibility Configuration
# =============================================================================

def get_page_visibility(ctx: CapabilityContext) -> Dict[str, bool]:
    """
    Get page visibility configuration.

    Returns a dict of page paths to visibility.
    """
    return {
        # Always visible
        "/": True,
        "/login": True,
        "/dashboard": True,
        "/my-templates": True,
        "/templates/builder": True,
        "/templates/builder/*": True,
        "/settings": True,

        # Cloud features
        "/marketplace": ctx.is_enabled(Feature.MARKETPLACE_BROWSE),
        "/marketplace/*": ctx.is_enabled(Feature.MARKETPLACE_BROWSE),
        "/billing": ctx.is_enabled(Feature.BILLING_STRIPE),

        # Observability (LOCAL_* for self-hosted, HOSTED_OBSERVABILITY for cloud)
        "/observability": (
            ctx.is_enabled(Feature.LOCAL_METRICS) or
            ctx.is_enabled(Feature.HOSTED_OBSERVABILITY)
        ),
        "/observability/metrics": (
            ctx.is_enabled(Feature.LOCAL_METRICS) or
            ctx.is_enabled(Feature.HOSTED_OBSERVABILITY)
        ),
        "/observability/traces": (
            ctx.is_enabled(Feature.LOCAL_TRACING) or
            ctx.is_enabled(Feature.HOSTED_OBSERVABILITY)
        ),
        "/observability/alerts": (
            ctx.is_enabled(Feature.LOCAL_ALERTS) or
            ctx.is_enabled(Feature.HOSTED_OBSERVABILITY)
        ),

        # Versioning
        "/versions": ctx.is_enabled(Feature.LOCAL_VERSIONING),

        # Audit
        "/audit": ctx.is_enabled(Feature.LOCAL_AUDIT),

        # Phase 7: Multi-tenancy Settings
        "/settings/organization": ctx.is_enabled(Feature.ORG_STRUCTURE),
        "/settings/projects": ctx.is_enabled(Feature.ORG_STRUCTURE),
        "/settings/roles": ctx.is_enabled(Feature.RBAC_FULL),

        # Admin
        "/admin/org": ctx.is_enabled(Feature.ORG_STRUCTURE),
        "/admin/rbac": ctx.is_enabled(Feature.RBAC_FULL),
        "/admin/sso": any([
            ctx.is_enabled(Feature.SSO_LDAP),
            ctx.is_enabled(Feature.SSO_SAML),
            ctx.is_enabled(Feature.SSO_OIDC),
        ]),
    }


# =============================================================================
# Feature Lock Information (for upgrade prompts)
# =============================================================================

def get_feature_lock_info(
    feature: Feature,
    ctx: CapabilityContext,
) -> Optional[Dict[str, Any]]:
    """
    Get lock information for a feature.

    Returns None if feature is available.
    Returns lock info dict if feature is locked.
    """
    if ctx.is_enabled(feature):
        return None

    from capabilities.feature_gate import get_denial_reason, DenialReason

    reason_code, message = get_denial_reason(
        feature, ctx.license_type, ctx.deploy_mode
    )

    return {
        "feature": feature.value,
        "locked": True,
        "reason_code": reason_code,
        "message": message,
        "can_unlock": reason_code == DenialReason.LICENSE_REQUIRED,
        "unlock_action": (
            "upgrade" if reason_code == DenialReason.LICENSE_REQUIRED
            else "change_deployment"
        ),
    }
