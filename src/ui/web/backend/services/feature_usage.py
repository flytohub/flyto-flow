"""No-op hosted feature metering compatibility for Cloud CE."""


async def get_feature_usage(user_id: str, feature_id: str, unit: str = "count_per_month") -> int:
    del user_id, feature_id, unit
    return 0


async def increment_feature_usage(
    user_id: str,
    feature_id: str,
    amount: int = 1,
    unit: str = "count_per_month",
) -> int:
    del user_id, feature_id, amount, unit
    return 0


async def check_and_increment(
    user_id: str,
    feature_id: str,
    limit: int,
    unit: str = "count_per_month",
    amount: int = 1,
) -> dict:
    del user_id, feature_id, unit, amount
    return {"allowed": True, "current": 0, "limit": limit}
