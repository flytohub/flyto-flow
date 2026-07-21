"""Unlimited local quota policy for Cloud CE.

The private source implementation reads hosted plan configuration. CE has no
subscription plans, so all local resources are unmetered.
"""


async def get_feature_quota(feature_id: str):
    del feature_id
    return None


async def get_all_feature_quotas() -> dict:
    return {}


async def get_monthly_points_limit(plan: str):
    del plan
    return None


async def get_max_workflows(plan: str):
    del plan
    return None


async def get_collaboration_hours(plan: str):
    del plan
    return None


async def get_plan_config() -> dict:
    return {"plans": {}, "feature_quotas": {}}


def invalidate_cache() -> None:
    return None
