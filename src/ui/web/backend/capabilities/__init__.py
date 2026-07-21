"""
Capability System

Dual-Axis Feature Gate:
    Feature Enabled = License Gate ∩ Deployment Gate

- Axis A: LicenseType (Business Rights) - What you paid for
- Axis B: DeploymentMode (Technical Constraints) - What's technically possible

Usage:

    # At application startup
    from capabilities import init_capability_context, LicenseType, DeploymentMode

    init_capability_context(
        license_type=LicenseType.PRO,
        deploy_mode=DeploymentMode.LOCAL_ONLINE,
    )

    # In FastAPI routes
    from capabilities import require_feature, Feature

    @router.get(
        "/metrics",
        dependencies=[Depends(require_feature(Feature.LOCAL_METRICS))]
    )
    async def get_metrics():
        ...

    # In code
    from capabilities import get_capability_context, Feature

    ctx = get_capability_context()
    if ctx.is_enabled(Feature.LOCAL_METRICS):
        ...
"""

# Types
from capabilities.types import (
    LicenseType,
    CapabilityDeployMode,
    Feature,
    FeatureCategory,
    FEATURE_METADATA,
)
# Backward-compatible alias — internal modules use CapabilityDeployMode;
# external consumers (mounts.py, tests) can still import DeploymentMode.
DeploymentMode = CapabilityDeployMode

# License Grants
from capabilities.license_grants import (
    LICENSE_GRANTS,
    get_license_grants,
    license_grants_feature,
    get_upgrade_features,
    get_license_comparison,
)

# Deployment Constraints
from capabilities.deploy_constraints import (
    DEPLOY_ALLOWS,
    get_deploy_allows,
    deploy_allows_feature,
    get_deploy_constraints,
    explain_constraint,
)

# Feature Gate
from capabilities.feature_gate import (
    is_feature_enabled,
    get_enabled_features,
    get_disabled_features,
    get_denial_reason,
    require_feature as require_feature_check,
    require_any_feature as require_any_feature_check,
    require_all_features,
    generate_feature_matrix,
    generate_simple_matrix,
    DenialReason,
    FeatureNotAvailableError,
)

# Context
from capabilities.context import (
    CapabilityContext,
    init_capability_context,
    get_capability_context,
    has_capability_context,
    reset_capability_context,
    detect_deploy_mode,
    detect_license_type,
    auto_init_context,
)

# FastAPI Dependencies
from capabilities.dependencies import (
    get_context,
    require_feature,
    require_any_feature,
    require_license,
    require_paid,
    can_use,
    get_available_features,
    get_context_from_request,
)

# UI Config
from capabilities.ui_config import (
    UIConfig,
    get_page_visibility,
    get_feature_lock_info,
)

__all__ = [
    # Types
    "LicenseType",
    "DeploymentMode",
    "Feature",
    "FeatureCategory",
    "FEATURE_METADATA",

    # License Grants
    "LICENSE_GRANTS",
    "get_license_grants",
    "license_grants_feature",
    "get_upgrade_features",
    "get_license_comparison",

    # Deployment Constraints
    "DEPLOY_ALLOWS",
    "get_deploy_allows",
    "deploy_allows_feature",
    "get_deploy_constraints",
    "explain_constraint",

    # Feature Gate
    "is_feature_enabled",
    "get_enabled_features",
    "get_disabled_features",
    "get_denial_reason",
    "require_feature_check",
    "require_any_feature_check",
    "require_all_features",
    "generate_feature_matrix",
    "generate_simple_matrix",
    "DenialReason",
    "FeatureNotAvailableError",

    # Context
    "CapabilityContext",
    "init_capability_context",
    "get_capability_context",
    "has_capability_context",
    "reset_capability_context",
    "detect_deploy_mode",
    "detect_license_type",
    "auto_init_context",

    # FastAPI Dependencies
    "get_context",
    "require_feature",
    "require_any_feature",
    "require_license",
    "require_paid",
    "can_use",
    "get_available_features",
    "get_context_from_request",

    # UI Config
    "UIConfig",
    "get_page_visibility",
    "get_feature_lock_info",
]
