"""
Device push notification service.

Provider-backed facade for device FCM token and push operations.
"""


async def register_fcm_token(user_id: str, token: str) -> None:
    """Store FCM token for push notifications."""
    await _device_provider().register_fcm_token(user_id, token)


async def notify_device_online(user_id: str, device_name: str) -> None:
    """Send a push notification when a desktop device comes online."""
    await _device_provider().notify_device_online(user_id, device_name)


async def notify_device_offline(user_id: str, device_name: str) -> None:
    """Send a push notification when a desktop device goes offline."""
    await _device_provider().notify_device_offline(user_id, device_name)


async def notify_job_complete(
    user_id: str,
    job_id: str,
    status: str,
    template_name: str,
) -> None:
    """Send a push notification when a job completes."""
    await _device_provider().notify_job_complete(
        user_id,
        job_id,
        status,
        template_name,
    )


async def notify_breakpoint_pending(
    user_id: str,
    breakpoint_id: str,
    execution_id: str,
    title: str,
    is_interact: bool = False,
) -> None:
    """Send a push notification when a breakpoint needs user action."""
    await _device_provider().notify_breakpoint_pending(
        user_id,
        breakpoint_id,
        execution_id,
        title,
        is_interact=is_interact,
    )


def _device_provider():
    from gateway.providers.hub import get_data_provider

    return get_data_provider().devices
