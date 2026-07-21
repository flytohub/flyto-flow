"""
Feature Gate

The core dual-axis feature gate logic.

Feature Enabled = License Gate ∩ Deployment Gate

A feature is only enabled if:
1. License grants the right to use it (paid for it)
2. Deployment mode technically allows it (can work here)

Both conditions must be true.
"""

from typing import Dict, Optional, Set, Tuple

from capabilities.types import LicenseType, CapabilityDeployMode as DeploymentMode, Feature
from capabilities.license_grants import LICENSE_GRANTS, license_grants_feature
from capabilities.deploy_constraints import DEPLOY_ALLOWS, deploy_allows_feature


# =============================================================================
# Core Feature Gate Functions
# =============================================================================

def is_feature_enabled(
    feature: Feature,
    license_type: LicenseType,
    deploy_mode: DeploymentMode,
) -> bool:
    """
    Dual-axis feature gate.

    Feature is enabled only if:
    1. License grants the right to use it (paid for it)
    2. Deployment mode technically allows it (can work here)

    Args:
        feature: The feature to check
        license_type: User's license type
        deploy_mode: Current deployment mode

    Returns:
        True if feature is enabled, False otherwise
    """
    license_allows = license_grants_feature(license_type, feature)
    deploy_allows = deploy_allows_feature(deploy_mode, feature)

    return license_allows and deploy_allows


def get_enabled_features(
    license_type: LicenseType,
    deploy_mode: DeploymentMode,
) -> Set[Feature]:
    """
    Get all enabled features for given license and deployment.

    This is the intersection of license grants and deployment allows.

    Args:
        license_type: User's license type
        deploy_mode: Current deployment mode

    Returns:
        Set of enabled features
    """
    license_features = LICENSE_GRANTS.get(license_type, set())
    deploy_features = DEPLOY_ALLOWS.get(deploy_mode, set())

    return license_features & deploy_features  # Intersection


def get_disabled_features(
    license_type: LicenseType,
    deploy_mode: DeploymentMode,
) -> Set[Feature]:
    """
    Get all features that are NOT enabled.

    Useful for "upgrade to unlock" prompts.

    Args:
        license_type: User's license type
        deploy_mode: Current deployment mode

    Returns:
        Set of disabled features
    """
    enabled = get_enabled_features(license_type, deploy_mode)
    all_features = set(Feature)

    return all_features - enabled


# =============================================================================
# Denial Reason Functions
# =============================================================================

class DenialReason:
    """Reasons why a feature is not available."""
    LICENSE_REQUIRED = "license_required"
    DEPLOY_CONSTRAINT = "deploy_constraint"
    BOTH = "both"
    NONE = "none"  # Feature is available


def get_denial_reason(
    feature: Feature,
    license_type: LicenseType,
    deploy_mode: DeploymentMode,
) -> Tuple[str, Optional[str]]:
    """
    Get the reason why a feature is not available.

    Args:
        feature: The feature to check
        license_type: User's license type
        deploy_mode: Current deployment mode

    Returns:
        Tuple of (reason_code, human_readable_message)
        If feature is available, returns (DenialReason.NONE, None)
    """
    license_allows = license_grants_feature(license_type, feature)
    deploy_allows = deploy_allows_feature(deploy_mode, feature)

    if license_allows and deploy_allows:
        return DenialReason.NONE, None

    if not license_allows and not deploy_allows:
        return (
            DenialReason.BOTH,
            f"Feature '{feature.value}' requires a higher license tier "
            f"and is not available in {deploy_mode.value} deployment."
        )

    if not license_allows:
        # Suggest upgrade
        upgrade_to = _suggest_license_upgrade(license_type, feature)
        return (
            DenialReason.LICENSE_REQUIRED,
            f"Feature '{feature.value}' requires {upgrade_to.value} license. "
            f"Current license: {license_type.value}"
        )

    if not deploy_allows:
        from capabilities.deploy_constraints import explain_constraint
        explanation = explain_constraint(deploy_mode, feature)
        return DenialReason.DEPLOY_CONSTRAINT, explanation

    return DenialReason.NONE, None


def _suggest_license_upgrade(
    current: LicenseType,
    feature: Feature,
) -> LicenseType:
    """
    Suggest which license to upgrade to for a feature.
    """
    # Check in order of "cheapest" to "most expensive"
    upgrade_order = [
        LicenseType.FREE,
        LicenseType.OFFLINE,
        LicenseType.PRO,
        LicenseType.TEAM,
        LicenseType.ENTERPRISE,
    ]

    for license_type in upgrade_order:
        if license_grants_feature(license_type, feature):
            if license_type != current:
                return license_type

    return LicenseType.ENTERPRISE  # Default fallback


# =============================================================================
# Validation Functions
# =============================================================================

class FeatureNotAvailableError(Exception):
    """Raised when a feature is not available."""

    def __init__(
        self,
        feature: Feature,
        reason_code: str,
        message: str,
        license_type: LicenseType,
        deploy_mode: DeploymentMode,
    ):
        """Initialize with feature, denial reason, and context."""
        self.feature = feature
        self.reason_code = reason_code
        self.license_type = license_type
        self.deploy_mode = deploy_mode
        super().__init__(message)


def require_feature(
    feature: Feature,
    license_type: LicenseType,
    deploy_mode: DeploymentMode,
) -> None:
    """
    Require a feature to be enabled. Raises if not.

    Args:
        feature: The feature to require
        license_type: User's license type
        deploy_mode: Current deployment mode

    Raises:
        FeatureNotAvailableError: If feature is not enabled
    """
    if is_feature_enabled(feature, license_type, deploy_mode):
        return

    reason_code, message = get_denial_reason(feature, license_type, deploy_mode)

    raise FeatureNotAvailableError(
        feature=feature,
        reason_code=reason_code,
        message=message or f"Feature {feature.value} is not available",
        license_type=license_type,
        deploy_mode=deploy_mode,
    )


def require_any_feature(
    features: Set[Feature],
    license_type: LicenseType,
    deploy_mode: DeploymentMode,
) -> Feature:
    """
    Require at least one of the features to be enabled.

    Args:
        features: Set of features (any one must be enabled)
        license_type: User's license type
        deploy_mode: Current deployment mode

    Returns:
        The first enabled feature

    Raises:
        FeatureNotAvailableError: If none of the features are enabled
    """
    for feature in features:
        if is_feature_enabled(feature, license_type, deploy_mode):
            return feature

    # None enabled, raise for the first one
    first_feature = next(iter(features))
    require_feature(first_feature, license_type, deploy_mode)

    # Should never reach here
    return first_feature


def require_all_features(
    features: Set[Feature],
    license_type: LicenseType,
    deploy_mode: DeploymentMode,
) -> None:
    """
    Require all features to be enabled.

    Args:
        features: Set of features (all must be enabled)
        license_type: User's license type
        deploy_mode: Current deployment mode

    Raises:
        FeatureNotAvailableError: If any feature is not enabled
    """
    for feature in features:
        require_feature(feature, license_type, deploy_mode)


# =============================================================================
# Comparison & Documentation Functions
# =============================================================================

def generate_feature_matrix() -> Dict[str, Dict[str, Dict[str, bool]]]:
    """
    Generate a complete feature availability matrix.

    Returns:
        {
            feature_id: {
                license_type: {
                    deploy_mode: True/False
                }
            }
        }

    Useful for generating documentation or admin dashboards.
    """
    matrix = {}

    for feature in Feature:
        matrix[feature.value] = {}

        for license_type in LicenseType:
            matrix[feature.value][license_type.value] = {}

            for deploy_mode in DeploymentMode:
                enabled = is_feature_enabled(feature, license_type, deploy_mode)
                matrix[feature.value][license_type.value][deploy_mode.value] = enabled

    return matrix


def generate_simple_matrix() -> Dict[str, Dict[str, bool]]:
    """
    Generate a simplified feature matrix (most common scenarios).

    Returns:
        {
            feature_id: {
                "free_offline": True/False,
                "pro_online": True/False,
                "offline": True/False,
                "enterprise": True/False,
            }
        }
    """
    scenarios = [
        ("free_offline", LicenseType.FREE, DeploymentMode.LOCAL_OFFLINE),
        ("pro_online", LicenseType.PRO, DeploymentMode.LOCAL_ONLINE),
        ("offline", LicenseType.OFFLINE, DeploymentMode.LOCAL_OFFLINE),
        ("enterprise", LicenseType.ENTERPRISE, DeploymentMode.ENTERPRISE_INTRANET),
    ]

    matrix = {}

    for feature in Feature:
        matrix[feature.value] = {}

        for scenario_name, license_type, deploy_mode in scenarios:
            enabled = is_feature_enabled(feature, license_type, deploy_mode)
            matrix[feature.value][scenario_name] = enabled

    return matrix
