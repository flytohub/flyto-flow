"""
License Grants

Defines what features each license type grants the RIGHT to use.
This is the business/commercial axis of the dual-axis model.

Note: Having the right doesn't mean you can use it!
The feature must also be technically possible in your deployment mode.
"""

from typing import Dict, Set

from capabilities.types import LicenseType, Feature


# =============================================================================
# License Grants
# =============================================================================

# Core features available to everyone (including free)
_CORE_FEATURES: Set[Feature] = {
    Feature.CORE_WORKFLOW_RUN,
    Feature.CORE_TEMPLATE_BUILDER,
    Feature.CORE_EXECUTION_HISTORY,
    Feature.CORE_BASIC_LOGGING,
    Feature.WORKFLOW_RECORDING,
}

# Free quota features: intentionally EMPTY in license grants.
#
# Quota-limited features (execution.debug, local.metrics, etc.) are NOT added to
# LICENSE_GRANTS[FREE]. Instead, they are gated through the quota system in
# require_feature() — when is_feature_enabled() returns False for a FREE user,
# the quota check runs and allows the action if under the configured limit.
#
# Adding them to LICENSE_GRANTS would bypass quota enforcement entirely because
# is_feature_enabled() would return True before the quota check ever fires.
_FREE_QUOTA_FEATURES: Set[Feature] = set()

# All local paid features (Pro/Offline/Enterprise get the full set, unlimited)
_PAID_LOCAL_FEATURES: Set[Feature] = {
    Feature.EXECUTION_RECORD_FULL,
    Feature.EXECUTION_REPLAY,
    Feature.EXECUTION_RERUN,
    Feature.EXECUTION_DEBUG,
    Feature.EVIDENCE_VIEW,
    Feature.LINEAGE_VIEW,
    Feature.LOCAL_METRICS,
    Feature.LOCAL_TRACING,
    Feature.LOCAL_ALERTS,
    Feature.EXPORT_PROMETHEUS,
    Feature.LOCAL_VERSIONING,
    Feature.LOCAL_VERSION_ROLLBACK,
    Feature.LOCAL_AUDIT,
    Feature.LOCAL_AUDIT_CHAIN,
    Feature.LOCAL_AUDIT_VERIFY,
}

# Basic orchestration (subscription/offline_license - not enterprise exclusive)
_BASIC_ORCH_FEATURES: Set[Feature] = {
    Feature.ORCH_BASIC_SCHEDULER,
    Feature.ORCH_BASIC_QUEUE,
}

# Cloud features (subscription only)
_CLOUD_FEATURES: Set[Feature] = {
    Feature.MARKETPLACE_BROWSE,
    Feature.MARKETPLACE_PURCHASE,
    Feature.MARKETPLACE_PUBLISH,
    Feature.CLOUD_SYNC,
    Feature.HOSTED_OBSERVABILITY,
    Feature.BILLING_STRIPE,
}

# Enterprise governance features (enterprise only - on top of basic orch)
_ENTERPRISE_GOVERNANCE_FEATURES: Set[Feature] = {
    # Enterprise Orchestration
    Feature.ORCHESTRATOR,
    Feature.MULTI_RUNNER,
    Feature.RUNNER_ISOLATION,
    Feature.RUNNER_QUOTAS,
    Feature.CENTRAL_LOGGING,
    Feature.CENTRAL_METRICS,

    # Organization & Access
    Feature.ORG_STRUCTURE,
    Feature.ORG_DEPARTMENTS,
    Feature.ORG_TEAMS,
    Feature.RBAC_FULL,

    # SSO
    Feature.SSO_LDAP,
    Feature.SSO_SAML,
    Feature.SSO_OIDC,

    # Workflow Governance
    Feature.APPROVAL_WORKFLOW,
    Feature.SECRETS_VAULT,
}

# Pro Modules (paid add-on modules from flyto-modules-pro)
_PRO_MODULES_FEATURES: Set[Feature] = {
    Feature.PRO_MODULES_STEALTH,
    Feature.PRO_MODULES_CAPTCHA,
    Feature.PRO_MODULES_ENTERPRISE,
    Feature.PRO_MODULES_PARALLEL,
    Feature.PRO_MODULES_CHECKPOINT,
    Feature.PRO_MODULES_DOCUMENT,
    Feature.PRO_MODULES_VISION,
    Feature.PRO_MODULES_ALL,
}


# =============================================================================
# License Grants Mapping
# =============================================================================

# Pro/Team features (subscription-based)
_PRO_FEATURES: Set[Feature] = (
    _CORE_FEATURES |
    _PAID_LOCAL_FEATURES |  # Superset of _FREE_QUOTA_FEATURES
    _BASIC_ORCH_FEATURES |  # Basic scheduling/queue
    _CLOUD_FEATURES |
    _PRO_MODULES_FEATURES  # All Pro automation modules
)

LICENSE_GRANTS: Dict[LicenseType, Set[Feature]] = {

    # -------------------------------------------------------------------------
    # FREE: Core features only (quota features gated via require_feature)
    # -------------------------------------------------------------------------
    LicenseType.FREE: _CORE_FEATURES | _FREE_QUOTA_FEATURES,

    # -------------------------------------------------------------------------
    # PRO: All local features + basic orch + cloud services
    # -------------------------------------------------------------------------
    LicenseType.PRO: _PRO_FEATURES,

    # -------------------------------------------------------------------------
    # TEAM: Same as Pro (for now, may add team-specific features later)
    # -------------------------------------------------------------------------
    LicenseType.TEAM: _PRO_FEATURES,

    # -------------------------------------------------------------------------
    # OFFLINE: All local features + basic orch + Pro modules, NO cloud
    # -------------------------------------------------------------------------
    LicenseType.OFFLINE: (
        _CORE_FEATURES |
        _PAID_LOCAL_FEATURES |
        _BASIC_ORCH_FEATURES |  # Basic scheduling/queue
        _PRO_MODULES_FEATURES  # All Pro automation modules
        # Note: No cloud features - that's the trade-off for one-time purchase
    ),

    # -------------------------------------------------------------------------
    # ENTERPRISE: Everything + full governance + Pro modules (but typically no cloud)
    # -------------------------------------------------------------------------
    LicenseType.ENTERPRISE: (
        _CORE_FEATURES |
        _PAID_LOCAL_FEATURES |
        _BASIC_ORCH_FEATURES |  # Includes basic
        _ENTERPRISE_GOVERNANCE_FEATURES |  # Plus full enterprise orch
        _PRO_MODULES_FEATURES  # All Pro automation modules
        # Note: No cloud features by default - enterprise self-hosts
        # But they CAN have cloud if they want (hybrid deployment)
    ),
}


# =============================================================================
# Helper Functions
# =============================================================================

def get_license_grants(license_type: LicenseType) -> Set[Feature]:
    """Get features granted by a license type."""
    return LICENSE_GRANTS.get(license_type, set())


def license_grants_feature(license_type: LicenseType, feature: Feature) -> bool:
    """Check if a license grants a specific feature."""
    return feature in LICENSE_GRANTS.get(license_type, set())


def get_upgrade_features(
    current: LicenseType,
    target: LicenseType,
) -> Set[Feature]:
    """
    Get features you would gain by upgrading.

    Useful for "upgrade to unlock" prompts.
    """
    current_features = LICENSE_GRANTS.get(current, set())
    target_features = LICENSE_GRANTS.get(target, set())
    return target_features - current_features


def get_license_comparison() -> Dict[str, Dict[str, bool]]:
    """
    Generate a comparison table for documentation/UI.

    Returns:
        {
            "feature_id": {
                "free": True/False,
                "subscription": True/False,
                ...
            }
        }
    """
    comparison = {}
    all_features = set()

    for features in LICENSE_GRANTS.values():
        all_features |= features

    for feature in sorted(all_features, key=lambda f: f.value):
        comparison[feature.value] = {
            license_type.value: feature in LICENSE_GRANTS.get(license_type, set())
            for license_type in LicenseType
        }

    return comparison
