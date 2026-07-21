"""
Telemetry Service Package

Re-exports TelemetryService and get_telemetry_service for backward compatibility.
"""
from typing import Optional

from .constants import COLLECTION_NAME, PRESENCE_COLLECTION, PRESENCE_TIMEOUT, SENSITIVE_FIELDS
from .core import TelemetryService

# Singleton instance
_service: Optional[TelemetryService] = None


def get_telemetry_service() -> TelemetryService:
    """Get singleton TelemetryService instance"""
    global _service
    if _service is None:
        _service = TelemetryService()
    return _service
