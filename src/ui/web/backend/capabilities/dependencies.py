"""
FastAPI Dependencies

FastAPI dependency functions for feature gating.

NOTE: For SaaS Cloud mode, the license type is determined per-user based on
their subscription_plan, not from a global config. This allows different users
to have different feature access based on their subscription.
"""

import logging
import os
from typing import Callable, List, Optional

from fastapi import Depends, HTTPException, Header, Request

from capabilities.types import Feature, LicenseType, CapabilityDeployMode as DeploymentMode
from capabilities.context import get_capability_context, CapabilityContext
from capabilities.feature_gate import get_denial_reason, DenialReason, is_feature_enabled

logger = logging.getLogger(__name__)


def _billing_mode() -> str:
    # Billing preview is a deliberate, explicit demo mode.  Treat an unset
    # value as live so a fresh self-hosted or enterprise install never grants
    # paid capabilities because of a missing environment variable.
    return "preview" if os.getenv("FLYTO_BILLING_MODE", "").strip().lower() == "preview" else "live"


def _is_billing_preview() -> bool:
    return _billing_mode() == "preview"


# =============================================================================
# User License Detection
# =============================================================================

def _map_subscription_to_license(subscription_plan: Optional[str]) -> LicenseType:
    """
    Map user's subscription_plan to LicenseType.

    Now that LicenseType values match SUBSCRIPTION_PLANS, this is a direct mapping:
    - free -> LicenseType.FREE
    - pro -> LicenseType.PRO
    - team -> LicenseType.TEAM
    - offline -> LicenseType.OFFLINE
    - enterprise -> LicenseType.ENTERPRISE

    NOTE: Values match frontend constants/subscription.js SUBSCRIPTION_PLANS
    """
    if not subscription_plan:
        return LicenseType.FREE

    plan = subscription_plan.lower()

    # Direct mapping - plan names now match LicenseType values
    try:
        return LicenseType(plan)
    except ValueError:
        # Handle legacy values
        if plan == "subscription":
            return LicenseType.PRO
        elif plan == "offline_license":
            return LicenseType.OFFLINE
        else:
            logger.warning(f"[FeatureGate] Unknown subscription_plan: {plan}, defaulting to FREE")
            return LicenseType.FREE


async def _get_user_from_token(authorization: Optional[str]) -> Optional[dict]:
    """Get user from authorization token without raising exceptions."""
    if not authorization or not authorization.startswith("Bearer "):
        return None

    try:
        from gateway.providers.hub import get_auth_provider
        token = authorization.split("Bearer ")[1]
        auth_provider = get_auth_provider()
        result = await auth_provider.verify_token(token)

        if result.ok and result.user:
            return result.user.model_dump()
    except Exception:
        pass

    return None


def _get_effective_license(user: Optional[dict], ctx: CapabilityContext) -> LicenseType:
    """
    Get effective license type considering user's subscription.

    Priority:
    1. If user has a subscription, use that
    2. If global context has a non-FREE license (env var or license file), use that
    3. Fall back to FREE
    """
    # Check user's subscription first
    if user:
        subscription_plan = user.get("subscription_plan")
        subscription_status = user.get("subscription_status")
        user_id = user.get("uid") or user.get("id") or "unknown"

        logger.debug(
            f"[FeatureGate] user={user_id}, plan={subscription_plan}, "
            f"status={subscription_status}, is_admin={user.get('is_admin')}"
        )

        # Only use subscription if status is valid
        # NOTE: We accept None status for backwards compatibility with users
        # created before subscription_status was added. New users should always
        # have an explicit status ("active", "trialing", "cancelled", "expired").
        valid_statuses = (None, "active", "trialing")
        if subscription_plan and subscription_status in valid_statuses:
            user_license = _map_subscription_to_license(subscription_plan)
            if user_license != LicenseType.FREE:
                logger.debug(f"[FeatureGate] -> effective_license={user_license.value} (from subscription)")
                return user_license
            else:
                logger.debug(f"[FeatureGate] plan '{subscription_plan}' mapped to FREE, checking other sources")
        elif subscription_plan:
            logger.warning(
                f"[FeatureGate] user={user_id} has plan={subscription_plan} but "
                f"status={subscription_status} is not valid (expected: {valid_statuses})"
            )

        # Admin users get pro-level access
        if user.get("is_admin"):
            logger.debug("[FeatureGate] -> effective_license=pro (admin override)")
            return LicenseType.PRO
    else:
        logger.debug("[FeatureGate] No user found, using global context")

    # Fall back to global context (from env var or license file)
    if _is_billing_preview() and ctx.license_type == LicenseType.FREE:
        logger.debug("[FeatureGate] -> effective_license=pro (billing preview)")
        return LicenseType.PRO

    logger.debug(f"[FeatureGate] -> effective_license={ctx.license_type.value} (from global context)")
    return ctx.license_type


# =============================================================================
# Dependency Functions
# =============================================================================

def get_context() -> CapabilityContext:
    """
    Get the current capability context.

    Use as a FastAPI dependency:

        @router.get("/endpoint")
        async def endpoint(ctx: CapabilityContext = Depends(get_context)):
            if ctx.is_enabled(Feature.SOME_FEATURE):
                ...
    """
    return get_capability_context()


async def _check_feature_quota(feature: Feature, user: Optional[dict], effective_license: LicenseType) -> Optional[bool]:
    """Check admin-configured feature quota for FREE users.

    Returns:
        True if quota allows access, None if no quota configured or not applicable.
    Raises:
        HTTPException(429) if quota is exceeded.
    """
    if effective_license != LicenseType.FREE:
        return None

    user_id = (user.get("uid") or user.get("id")) if user else None
    if not user_id:
        return None

    from services.plan_config import get_feature_quota
    quota = await get_feature_quota(feature.value)
    if not quota:
        return None

    from services.feature_usage import check_and_increment
    result = await check_and_increment(
        user_id=user_id,
        feature_id=feature.value,
        limit=quota.get("limit", 0),
        unit=quota.get("unit", "count_per_month"),
    )
    if result["allowed"]:
        return True

    raise HTTPException(
        status_code=429,
        detail={
            "error": "quota_exceeded",
            "feature": feature.value,
            "current": result["current"],
            "limit": result["limit"],
            "unit": quota.get("unit", "count_per_month"),
            "message": f"Free quota exceeded for {feature.value}. "
                       f"Used {result['current']}/{result['limit']}. "
                       f"Upgrade for unlimited access.",
        },
    )


def _build_denial_response(feature: Feature, effective_license: LicenseType, ctx: CapabilityContext):
    """Build and raise the appropriate HTTPException for a denied feature."""
    reason_code, message = get_denial_reason(
        feature, effective_license, ctx.deploy_mode
    )

    status_code = 402 if reason_code == DenialReason.LICENSE_REQUIRED else 403

    raise HTTPException(
        status_code=status_code,
        detail={
            "error": "feature_not_available",
            "feature": feature.value,
            "reason_code": reason_code,
            "message": message,
            "license_type": effective_license.value,
            "deploy_mode": ctx.deploy_mode.value,
        }
    )


def require_feature(*features: Feature) -> Callable:
    """
    FastAPI dependency that requires specific features.

    NOTE: This now checks the user's subscription_plan to determine license type,
    not just the global context. Admin users automatically get subscription-level access.

    Use as a router dependency:

        @router.get(
            "/metrics",
            dependencies=[Depends(require_feature(Feature.LOCAL_METRICS))]
        )
        async def get_metrics():
            ...

    Or on a router:

        router = APIRouter(
            prefix="/metrics",
            dependencies=[Depends(require_feature(Feature.LOCAL_METRICS))],
        )

    Args:
        *features: Features to require (all must be enabled)

    Returns:
        Dependency function
    """
    async def check(authorization: Optional[str] = Header(None)):
        ctx = get_capability_context()

        user = await _get_user_from_token(authorization)
        effective_license = _get_effective_license(user, ctx)

        for feature in features:
            if is_feature_enabled(feature, effective_license, ctx.deploy_mode):
                continue

            reason_code, _ = get_denial_reason(feature, effective_license, ctx.deploy_mode)

            # FREE users with LICENSE_REQUIRED: check quota before denying
            if effective_license == LicenseType.FREE and reason_code == DenialReason.LICENSE_REQUIRED:
                try:
                    quota_allowed = await _check_feature_quota(feature, user, effective_license)
                    if quota_allowed:
                        continue
                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Feature quota check failed for {feature.value}: {e}")

            _build_denial_response(feature, effective_license, ctx)

        return True

    return check


def require_any_feature(*features: Feature) -> Callable:
    """
    FastAPI dependency that requires at least one of the features.

    NOTE: This now checks the user's subscription_plan to determine license type,
    not just the global context. Admin users automatically get subscription-level access.

    Use when multiple features can satisfy a requirement:

        @router.get(
            "/observability",
            dependencies=[Depends(require_any_feature(
                Feature.LOCAL_METRICS,
                Feature.HOSTED_OBSERVABILITY,
            ))]
        )
        async def get_observability():
            ...

    Args:
        *features: Features to check (at least one must be enabled)

    Returns:
        Dependency function
    """
    async def check(authorization: Optional[str] = Header(None)):
        ctx = get_capability_context()

        # Get user's subscription-based license
        user = await _get_user_from_token(authorization)
        effective_license = _get_effective_license(user, ctx)

        for feature in features:
            if is_feature_enabled(feature, effective_license, ctx.deploy_mode):
                return feature  # Return the first enabled feature

        # FREE users: check admin-configured feature quotas before denying
        if effective_license == LicenseType.FREE:
            try:
                from services.plan_config import get_feature_quota
                user_id = (user.get("uid") or user.get("id")) if user else None
                for feature in features:
                    quota = await get_feature_quota(feature.value)
                    if quota and user_id:
                        from services.feature_usage import check_and_increment
                        result = await check_and_increment(
                            user_id=user_id,
                            feature_id=feature.value,
                            limit=quota.get("limit", 0),
                            unit=quota.get("unit", "count_per_month"),
                        )
                        if result["allowed"]:
                            return feature
            except Exception:
                pass

        # None enabled, raise for the first one
        first_feature = features[0]
        reason_code, message = get_denial_reason(
            first_feature, effective_license, ctx.deploy_mode
        )

        status_code = 402 if reason_code == DenialReason.LICENSE_REQUIRED else 403

        raise HTTPException(
            status_code=status_code,
            detail={
                "error": "feature_not_available",
                "features": [f.value for f in features],
                "reason_code": reason_code,
                "message": f"At least one of these features is required: {[f.value for f in features]}",
                "license_type": effective_license.value,
                "deploy_mode": ctx.deploy_mode.value,
            }
        )

    return check


def require_license(*license_types: LicenseType) -> Callable:
    """
    FastAPI dependency that requires specific license types.

    NOTE: This now checks the user's subscription_plan to determine license type,
    not just the global context. Admin users automatically get subscription-level access.

    Use when you want to gate by license directly:

        @router.get(
            "/enterprise-only",
            dependencies=[Depends(require_license(LicenseType.ENTERPRISE))]
        )
        async def enterprise_endpoint():
            ...

    Args:
        *license_types: Allowed license types

    Returns:
        Dependency function
    """
    async def check(authorization: Optional[str] = Header(None)):
        ctx = get_capability_context()

        # Get user's subscription-based license
        user = await _get_user_from_token(authorization)
        effective_license = _get_effective_license(user, ctx)

        if effective_license not in license_types:
            allowed = [lt.value for lt in license_types]
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "license_required",
                    "current_license": effective_license.value,
                    "required_licenses": allowed,
                    "message": f"This endpoint requires one of: {allowed}",
                }
            )

        return True

    return check


def require_paid() -> Callable:
    """
    FastAPI dependency that requires any paid license.

    NOTE: This now checks the user's subscription_plan to determine license type.
    Admin users automatically get pro-level access.

    Shorthand for:
        require_license(
            LicenseType.PRO,
            LicenseType.TEAM,
            LicenseType.OFFLINE,
            LicenseType.ENTERPRISE,
        )
    """
    return require_license(
        LicenseType.PRO,
        LicenseType.TEAM,
        LicenseType.OFFLINE,
        LicenseType.ENTERPRISE,
    )


# =============================================================================
# Feature Check Helpers (for use in route handlers)
# =============================================================================

def can_use(feature: Feature) -> bool:
    """
    Check if a feature is available.

    Use in route handlers for conditional logic:

        @router.get("/data")
        async def get_data():
            if can_use(Feature.LOCAL_METRICS):
                return get_with_metrics()
            else:
                return get_basic()
    """
    ctx = get_capability_context()
    return ctx.is_enabled(feature)


def get_available_features() -> List[str]:
    """
    Get list of available feature IDs.

    Useful for returning to frontend.
    """
    ctx = get_capability_context()
    return [f.value for f in ctx.get_enabled_features()]


# =============================================================================
# Middleware
# =============================================================================

class CapabilityMiddleware:
    """
    Middleware that adds capability context to request state.

    Usage:
        app.add_middleware(CapabilityMiddleware)

    Then in routes:
        @router.get("/endpoint")
        async def endpoint(request: Request):
            ctx = request.state.capability_context
            if ctx.is_enabled(Feature.SOME_FEATURE):
                ...
    """

    def __init__(self, app):
        """Initialize middleware with the ASGI application."""
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Attach context to request state
            # This happens in the ASGI lifecycle
            pass

        await self.app(scope, receive, send)


def get_context_from_request(request: Request) -> CapabilityContext:
    """
    Get context from request state.

    Alternative to global context when using middleware.
    """
    if hasattr(request.state, "capability_context"):
        return request.state.capability_context

    return get_capability_context()
