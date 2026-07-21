"""
Device Service

Manages registered runner devices for the A+B pattern.
"""

from .models import Device, DeviceStatus
from .repository import DeviceRepository
from .service import DeviceService

__all__ = [
    "Device",
    "DeviceStatus",
    "DeviceRepository",
    "DeviceService",
]

# Sub-modules available via: from services.device import notification, wake
# - notification: FCM push notification service
# - wake: remote wake command service
# - job_repository: execution job persistence
