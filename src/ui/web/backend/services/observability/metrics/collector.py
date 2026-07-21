"""
Metrics Collector

Single responsibility: Collect and store metrics in memory.
Thread-safe access with support for counters, gauges, and histograms.
"""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Metric type enumeration."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class MetricSample:
    """A single metric sample with timestamp."""

    value: float
    timestamp: str
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Metric:
    """Metric data model."""

    name: str
    type: MetricType
    help_text: str = ""
    labels: Dict[str, str] = field(default_factory=dict)
    samples: List[MetricSample] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type.value,
            "help": self.help_text,
            "labels": self.labels,
            "samples": [
                {
                    "value": s.value,
                    "timestamp": s.timestamp,
                    "labels": s.labels,
                }
                for s in self.samples
            ],
        }


class MetricsCollector:
    """
    Thread-safe in-memory metrics collector.

    Supports:
    - Counters: Monotonically increasing values
    - Gauges: Values that can go up or down
    - Histograms: Distribution of values with buckets
    """

    # Default histogram buckets (in seconds for duration metrics)
    DEFAULT_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

    def __init__(self, max_samples_per_metric: int = 1000):
        """
        Initialize collector.

        Args:
            max_samples_per_metric: Maximum samples to retain per metric
        """
        self._lock = threading.RLock()
        self._counters: Dict[str, Dict[str, float]] = {}
        self._gauges: Dict[str, Dict[str, float]] = {}
        self._histograms: Dict[str, Dict[str, List[float]]] = {}
        self._histogram_buckets: Dict[str, List[float]] = {}
        self._help_texts: Dict[str, str] = {}
        self._max_samples = max_samples_per_metric

    def _labels_key(self, labels: Dict[str, str]) -> str:
        """Generate a unique key from labels."""
        if not labels:
            return ""
        sorted_items = sorted(labels.items())
        return ",".join(f"{k}={v}" for k, v in sorted_items)

    def register_counter(self, name: str, help_text: str = "") -> None:
        """Register a new counter metric."""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = {}
                self._help_texts[name] = help_text

    def register_gauge(self, name: str, help_text: str = "") -> None:
        """Register a new gauge metric."""
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = {}
                self._help_texts[name] = help_text

    def register_histogram(
        self,
        name: str,
        help_text: str = "",
        buckets: Optional[List[float]] = None,
    ) -> None:
        """Register a new histogram metric."""
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = {}
                self._histogram_buckets[name] = buckets or self.DEFAULT_BUCKETS
                self._help_texts[name] = help_text

    def increment(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Increment a counter.

        Args:
            name: Metric name
            value: Value to add (must be positive)
            labels: Optional labels
        """
        if value < 0:
            logger.warning(f"Counter {name} cannot be decremented")
            return

        labels = labels or {}
        key = self._labels_key(labels)

        with self._lock:
            if name not in self._counters:
                self._counters[name] = {}

            if key not in self._counters[name]:
                self._counters[name][key] = 0.0

            self._counters[name][key] += value

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Set a gauge value.

        Args:
            name: Metric name
            value: Gauge value
            labels: Optional labels
        """
        labels = labels or {}
        key = self._labels_key(labels)

        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = {}

            self._gauges[name][key] = value

    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Observe a histogram value.

        Args:
            name: Metric name
            value: Observed value
            labels: Optional labels
        """
        labels = labels or {}
        key = self._labels_key(labels)

        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = {}
                self._histogram_buckets[name] = self.DEFAULT_BUCKETS

            if key not in self._histograms[name]:
                self._histograms[name][key] = []

            samples = self._histograms[name][key]
            samples.append(value)

            # Trim if exceeds max
            if len(samples) > self._max_samples:
                self._histograms[name][key] = samples[-self._max_samples :]

    def get_counter(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> float:
        """Get current counter value."""
        labels = labels or {}
        key = self._labels_key(labels)

        with self._lock:
            if name not in self._counters:
                return 0.0
            return self._counters[name].get(key, 0.0)

    def get_gauge(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> float:
        """Get current gauge value."""
        labels = labels or {}
        key = self._labels_key(labels)

        with self._lock:
            if name not in self._gauges:
                return 0.0
            return self._gauges[name].get(key, 0.0)

    def get_histogram_samples(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> List[float]:
        """Get histogram samples."""
        labels = labels or {}
        key = self._labels_key(labels)

        with self._lock:
            if name not in self._histograms:
                return []
            return list(self._histograms[name].get(key, []))

    def get_all_metrics(self) -> List[Metric]:
        """Get all metrics as Metric objects."""
        metrics = []
        now = datetime.now(timezone.utc).isoformat()

        with self._lock:
            # Counters
            for name, values in self._counters.items():
                for key, value in values.items():
                    labels = self._parse_labels_key(key)
                    metrics.append(
                        Metric(
                            name=name,
                            type=MetricType.COUNTER,
                            help_text=self._help_texts.get(name, ""),
                            labels=labels,
                            samples=[MetricSample(value=value, timestamp=now)],
                        )
                    )

            # Gauges
            for name, values in self._gauges.items():
                for key, value in values.items():
                    labels = self._parse_labels_key(key)
                    metrics.append(
                        Metric(
                            name=name,
                            type=MetricType.GAUGE,
                            help_text=self._help_texts.get(name, ""),
                            labels=labels,
                            samples=[MetricSample(value=value, timestamp=now)],
                        )
                    )

            # Histograms (aggregate into buckets)
            for name, values in self._histograms.items():
                buckets = self._histogram_buckets.get(name, self.DEFAULT_BUCKETS)
                for key, samples in values.items():
                    labels = self._parse_labels_key(key)
                    if samples:
                        # Create bucket counts
                        bucket_counts = self._compute_bucket_counts(samples, buckets)
                        metrics.append(
                            Metric(
                                name=name,
                                type=MetricType.HISTOGRAM,
                                help_text=self._help_texts.get(name, ""),
                                labels={**labels, "_buckets": str(bucket_counts)},
                                samples=[
                                    MetricSample(value=sum(samples), timestamp=now)
                                ],
                            )
                        )

        return metrics

    def _parse_labels_key(self, key: str) -> Dict[str, str]:
        """Parse labels key back to dict."""
        if not key:
            return {}
        labels = {}
        for item in key.split(","):
            if "=" in item:
                k, v = item.split("=", 1)
                labels[k] = v
        return labels

    def _compute_bucket_counts(
        self,
        samples: List[float],
        buckets: List[float],
    ) -> Dict[str, int]:
        """Compute histogram bucket counts."""
        counts = {str(b): 0 for b in buckets}
        counts["+Inf"] = len(samples)

        for sample in samples:
            for bucket in buckets:
                if sample <= bucket:
                    counts[str(bucket)] += 1

        return counts

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()

    def reset_metric(self, name: str) -> None:
        """Reset a specific metric."""
        with self._lock:
            self._counters.pop(name, None)
            self._gauges.pop(name, None)
            self._histograms.pop(name, None)


# Global collector instance
_collector: Optional[MetricsCollector] = None


def get_collector() -> MetricsCollector:
    """Get or create the global metrics collector."""
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector
