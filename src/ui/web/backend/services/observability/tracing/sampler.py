"""
Trace Sampler

Single responsibility: Decide which traces to record.
"""

import hashlib
import logging
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SamplingDecision(str, Enum):
    """Sampling decision result."""

    DROP = "drop"
    RECORD = "record"


@dataclass
class SamplerConfig:
    """Configuration for trace sampler."""

    # Default sampling rate (0.0 to 1.0)
    default_rate: float = 0.1  # 10% by default

    # Always sample on error
    always_sample_on_error: bool = True

    # Always sample slow operations
    always_sample_on_slow: bool = True
    slow_threshold_ms: int = 30000  # 30 seconds

    # Per-operation overrides (operation_name -> rate)
    operation_overrides: Dict[str, float] = field(default_factory=dict)

    # Per-trace-id overrides (for deterministic sampling)
    trace_id_overrides: Dict[str, SamplingDecision] = field(default_factory=dict)

    # Debug mode (sample everything)
    debug: bool = False


class TraceSampler:
    """
    Trace sampler for deciding which traces to record.

    Supports:
    - Probabilistic sampling with configurable rate
    - Always sample on error or slow operations
    - Per-operation rate overrides
    - Deterministic sampling based on trace ID
    """

    def __init__(self, config: Optional[SamplerConfig] = None):
        """
        Initialize sampler.

        Args:
            config: Sampler configuration
        """
        self.config = config or SamplerConfig()

    def should_sample(
        self,
        trace_id: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> SamplingDecision:
        """
        Decide whether to sample a trace.

        Args:
            trace_id: Trace ID
            attributes: Span attributes

        Returns:
            SamplingDecision.RECORD or SamplingDecision.DROP
        """
        attributes = attributes or {}

        # Debug mode: sample everything
        if self.config.debug:
            return SamplingDecision.RECORD

        # Check trace ID overrides
        if trace_id in self.config.trace_id_overrides:
            return self.config.trace_id_overrides[trace_id]

        # Check error condition
        if self.config.always_sample_on_error:
            if attributes.get("error") or attributes.get("exception"):
                return SamplingDecision.RECORD

        # Check slow operation
        if self.config.always_sample_on_slow:
            duration = attributes.get("duration_ms", 0)
            if duration > self.config.slow_threshold_ms:
                return SamplingDecision.RECORD

        # Check operation overrides
        operation = attributes.get("operation_name", "")
        if operation in self.config.operation_overrides:
            rate = self.config.operation_overrides[operation]
            if self._probabilistic_sample(trace_id, rate):
                return SamplingDecision.RECORD
            return SamplingDecision.DROP

        # Default probabilistic sampling
        if self._probabilistic_sample(trace_id, self.config.default_rate):
            return SamplingDecision.RECORD

        return SamplingDecision.DROP

    def _probabilistic_sample(self, trace_id: str, rate: float) -> bool:
        """
        Make probabilistic sampling decision.

        Uses trace ID hash for deterministic sampling (same trace ID
        always gets the same decision for a given rate).

        Args:
            trace_id: Trace ID
            rate: Sampling rate (0.0 to 1.0)

        Returns:
            True if should sample
        """
        if rate <= 0.0:
            return False
        if rate >= 1.0:
            return True

        # Use trace ID hash for determinism
        hash_value = int(hashlib.md5(trace_id.encode()).hexdigest()[:8], 16)
        threshold = int(rate * 0xFFFFFFFF)

        return hash_value < threshold

    def set_rate(self, rate: float) -> None:
        """
        Set the default sampling rate.

        Args:
            rate: Sampling rate (0.0 to 1.0)
        """
        self.config.default_rate = max(0.0, min(1.0, rate))

    def set_operation_rate(self, operation: str, rate: float) -> None:
        """
        Set sampling rate for a specific operation.

        Args:
            operation: Operation name
            rate: Sampling rate (0.0 to 1.0)
        """
        self.config.operation_overrides[operation] = max(0.0, min(1.0, rate))

    def force_sample(self, trace_id: str) -> None:
        """
        Force a trace ID to be sampled.

        Args:
            trace_id: Trace ID to force sample
        """
        self.config.trace_id_overrides[trace_id] = SamplingDecision.RECORD

    def force_drop(self, trace_id: str) -> None:
        """
        Force a trace ID to be dropped.

        Args:
            trace_id: Trace ID to force drop
        """
        self.config.trace_id_overrides[trace_id] = SamplingDecision.DROP


class AlwaysSampler(TraceSampler):
    """Sampler that always records."""

    def should_sample(
        self,
        trace_id: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> SamplingDecision:
        """Always return RECORD."""
        return SamplingDecision.RECORD


class NeverSampler(TraceSampler):
    """Sampler that never records."""

    def should_sample(
        self,
        trace_id: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> SamplingDecision:
        """Always return DROP."""
        return SamplingDecision.DROP


class RatioSampler(TraceSampler):
    """Simple ratio-based sampler."""

    def __init__(self, rate: float = 0.1):
        """
        Initialize with fixed rate.

        Args:
            rate: Sampling rate (0.0 to 1.0)
        """
        super().__init__(SamplerConfig(default_rate=rate))
