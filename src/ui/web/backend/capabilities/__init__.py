"""Static local capabilities for the CE appliance."""

from dataclasses import dataclass
from enum import Enum


class Feature(str, Enum):
    EXECUTION_DEBUG = "execution.debug"
    EVIDENCE_VIEW = "evidence.view"
    LOCAL_METRICS = "local.metrics"
    LOCAL_TRACING = "local.tracing"
    LOCAL_ALERTS = "local.alerts"


@dataclass(frozen=True)
class CapabilityContext:
    def is_enabled(self, _feature: Feature) -> bool:
        return True


_context = CapabilityContext()


def auto_init_context() -> CapabilityContext:
    return _context


def has_capability_context() -> bool:
    return True


def get_capability_context() -> CapabilityContext:
    return _context


def require_feature(feature: Feature):
    async def dependency():
        return feature

    return dependency


def require_any_feature(*features: Feature):
    async def dependency():
        return features[0] if features else None

    return dependency
