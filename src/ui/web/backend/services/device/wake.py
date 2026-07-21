"""
Remote wake command service.

Provider-backed facade for remote wake commands.
"""

from typing import Optional, Tuple


def create_wake_command(device_id: str, user_id: str) -> None:
    """Store a wake command for the daemon to pick up."""
    _device_provider().create_wake_command(device_id, user_id)


def poll_wake_commands(device_id: str) -> Tuple[bool, Optional[str]]:
    """
    Poll for pending wake commands.

    Returns (wake: bool, command_id: str | None).
    """
    return _device_provider().poll_wake_commands(device_id)


def _device_provider():
    from gateway.providers.hub import get_data_provider

    return get_data_provider().devices
