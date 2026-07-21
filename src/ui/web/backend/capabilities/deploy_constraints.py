"""
Deployment Constraints

Defines what features are TECHNICALLY POSSIBLE in each deployment mode.
This is the technical axis of the dual-axis model.

Note: Being technically possible doesn't mean you can use it!
You must also have the license rights.
"""

from typing import Dict, Set

from capabilities.types import CapabilityDeployMode as DeploymentMode, Feature


# =============================================================================
# Feature Sets by Technical Requirement
# =============================================================================

# Features that work purely locally (no network needed)
_LOCAL_FEATURES: Set[Feature] = {
    # Core
    Feature.CORE_WORKFLOW_RUN,
    Feature.CORE_TEMPLATE_BUILDER,
    Feature.CORE_EXECUTION_HISTORY,
    Feature.CORE_BASIC_LOGGING,

    # Full execution record (prerequisite for advanced execution features)
    Feature.EXECUTION_RECORD_FULL,

    # Local Observability
    Feature.LOCAL_METRICS,
    Feature.LOCAL_TRACING,
    Feature.LOCAL_ALERTS,
    Feature.EXPORT_PROMETHEUS,

    # Local Versioning
    Feature.LOCAL_VERSIONING,
    Feature.LOCAL_VERSION_ROLLBACK,

    # Local Audit
    Feature.LOCAL_AUDIT,
    Feature.LOCAL_AUDIT_CHAIN,
    Feature.LOCAL_AUDIT_VERIFY,

    # Execution (require EXECUTION_RECORD_FULL as prerequisite)
    Feature.EXECUTION_REPLAY,
    Feature.EXECUTION_RERUN,
    Feature.EXECUTION_DEBUG,
    Feature.EVIDENCE_VIEW,
    Feature.LINEAGE_VIEW,

    # Desktop-only
    Feature.WORKFLOW_RECORDING,
}

# Features that need network but can be self-hosted
_SELF_HOST_FEATURES: Set[Feature] = {
    Feature.ORCHESTRATOR,
    Feature.MULTI_RUNNER,
    Feature.CENTRAL_LOGGING,
    Feature.CENTRAL_METRICS,
    Feature.ORG_STRUCTURE,
    Feature.ORG_DEPARTMENTS,
    Feature.ORG_TEAMS,
    Feature.RBAC_FULL,
    Feature.SSO_LDAP,
    Feature.SSO_SAML,
    Feature.SSO_OIDC,
    Feature.APPROVAL_WORKFLOW,
    Feature.SECRETS_VAULT,
}

# Features that require cloud infrastructure
_CLOUD_FEATURES: Set[Feature] = {
    Feature.MARKETPLACE_BROWSE,
    Feature.MARKETPLACE_PURCHASE,
    Feature.MARKETPLACE_PUBLISH,
    Feature.CLOUD_SYNC,
    Feature.HOSTED_OBSERVABILITY,
    Feature.BILLING_STRIPE,
}


# =============================================================================
# Deployment Allows Mapping
# =============================================================================

DEPLOY_ALLOWS: Dict[DeploymentMode, Set[Feature]] = {

    # -------------------------------------------------------------------------
    # SAAS_CLOUD: Cloud SaaS (has internet, no local storage persistence)
    # -------------------------------------------------------------------------
    DeploymentMode.SAAS_CLOUD: (
        # Core features work
        {
            Feature.CORE_WORKFLOW_RUN,
            Feature.CORE_TEMPLATE_BUILDER,
            Feature.CORE_EXECUTION_HISTORY,
            Feature.CORE_BASIC_LOGGING,
        } |
        # Cloud features work (we're in the cloud!)
        _CLOUD_FEATURES |
        # Hosted observability instead of local
        {Feature.HOSTED_OBSERVABILITY} |
        # Execution features for Pro users (stored in cloud database)
        {
            Feature.EXECUTION_RECORD_FULL,
            Feature.EXECUTION_REPLAY,
            Feature.EXECUTION_RERUN,
            Feature.EXECUTION_DEBUG,
            Feature.EVIDENCE_VIEW,
            Feature.LINEAGE_VIEW,
        } |
        # Versioning for Pro users (stored in cloud database)
        {
            Feature.LOCAL_VERSIONING,
            Feature.LOCAL_VERSION_ROLLBACK,
        }
        # Note: No self-host features (we host, not customer)
        # Note: LOCAL_AUDIT not included — Cloud audit provider is Noop,
        # need real storage backend before enabling
    ),

    # -------------------------------------------------------------------------
    # LOCAL_ONLINE: Local install with internet
    # -------------------------------------------------------------------------
    DeploymentMode.LOCAL_ONLINE: (
        # All local features work
        _LOCAL_FEATURES |
        # All cloud features work (has internet)
        _CLOUD_FEATURES
        # Note: No self-host features (single machine)
    ),

    # -------------------------------------------------------------------------
    # ENTERPRISE_INTRANET: On-premise, intranet only
    # -------------------------------------------------------------------------
    DeploymentMode.ENTERPRISE_INTRANET: (
        # All local features work
        _LOCAL_FEATURES |
        # All self-host features work (has intranet infrastructure)
        _SELF_HOST_FEATURES
        # Note: No cloud features (no internet)
    ),

    # -------------------------------------------------------------------------
    # LOCAL_OFFLINE: Local install, no network
    # -------------------------------------------------------------------------
    DeploymentMode.LOCAL_OFFLINE: (
        # Only local features work
        _LOCAL_FEATURES
        # Note: No cloud features (no network)
        # Note: No self-host features (no network)
    ),
}


# =============================================================================
# Helper Functions
# =============================================================================

def get_deploy_allows(deploy_mode: DeploymentMode) -> Set[Feature]:
    """Get features allowed by a deployment mode."""
    return DEPLOY_ALLOWS.get(deploy_mode, set())


def deploy_allows_feature(deploy_mode: DeploymentMode, feature: Feature) -> bool:
    """Check if a deployment mode allows a specific feature."""
    return feature in DEPLOY_ALLOWS.get(deploy_mode, set())


def get_deploy_constraints(deploy_mode: DeploymentMode) -> Dict[str, bool]:
    """
    Get technical constraints for a deployment mode.

    Returns a dict describing what's technically possible.
    """
    mode = deploy_mode

    return {
        "has_internet": mode in {
            DeploymentMode.SAAS_CLOUD,
            DeploymentMode.LOCAL_ONLINE,
        },
        "has_local_storage": mode in {
            DeploymentMode.LOCAL_ONLINE,
            DeploymentMode.ENTERPRISE_INTRANET,
            DeploymentMode.LOCAL_OFFLINE,
        },
        "has_intranet": mode in {
            DeploymentMode.ENTERPRISE_INTRANET,
        },
        "can_self_host": mode in {
            DeploymentMode.ENTERPRISE_INTRANET,
        },
        "can_use_cloud": mode in {
            DeploymentMode.SAAS_CLOUD,
            DeploymentMode.LOCAL_ONLINE,
        },
    }


def explain_constraint(deploy_mode: DeploymentMode, feature: Feature) -> str:
    """
    Explain why a feature is not available in a deployment mode.

    Useful for error messages and UI feedback.
    """
    from capabilities.types import FEATURE_METADATA, FeatureCategory

    if deploy_allows_feature(deploy_mode, feature):
        return ""  # No constraint, feature is available

    metadata = FEATURE_METADATA.get(feature, {})
    category = metadata.get("category")

    if category == FeatureCategory.CLOUD_ONLY:
        if deploy_mode == DeploymentMode.LOCAL_OFFLINE:
            return "This feature requires internet connection. You are running in offline mode."
        elif deploy_mode == DeploymentMode.ENTERPRISE_INTRANET:
            return "This feature requires internet connection. Enterprise intranet deployment does not have internet access."

    if category == FeatureCategory.SELF_HOSTABLE:
        if deploy_mode in {DeploymentMode.LOCAL_OFFLINE, DeploymentMode.LOCAL_ONLINE}:
            return "This feature requires enterprise infrastructure. Consider upgrading to Enterprise deployment."

    if category == FeatureCategory.LOCAL_ONLY:
        if deploy_mode == DeploymentMode.SAAS_CLOUD:
            return "This feature requires local storage. SaaS deployment runs in cloud without persistent local storage."

    return f"Feature '{feature.value}' is not available in {deploy_mode.value} deployment mode."
