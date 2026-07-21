"""
Metrics Aggregator

Single responsibility: Aggregate metrics over time windows.
Computes percentiles, averages, and other statistical measures.
"""

import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.observability.metrics.collector import MetricsCollector, MetricType

logger = logging.getLogger(__name__)


@dataclass
class AggregatedMetric:
    """Aggregated metric with statistical measures."""

    name: str
    type: MetricType
    labels: Dict[str, str]
    window_seconds: int
    timestamp: str

    # Statistical measures
    count: int = 0
    sum: float = 0.0
    min: float = 0.0
    max: float = 0.0
    avg: float = 0.0

    # Percentiles (for histograms)
    p50: Optional[float] = None
    p75: Optional[float] = None
    p90: Optional[float] = None
    p95: Optional[float] = None
    p99: Optional[float] = None

    # Rate (for counters)
    rate_per_second: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "name": self.name,
            "type": self.type.value,
            "labels": self.labels,
            "window_seconds": self.window_seconds,
            "timestamp": self.timestamp,
            "count": self.count,
            "sum": self.sum,
            "min": self.min,
            "max": self.max,
            "avg": self.avg,
        }

        if self.p50 is not None:
            result["percentiles"] = {
                "p50": self.p50,
                "p75": self.p75,
                "p90": self.p90,
                "p95": self.p95,
                "p99": self.p99,
            }

        if self.rate_per_second is not None:
            result["rate_per_second"] = self.rate_per_second

        return result


class MetricsAggregator:
    """
    Aggregate metrics over configurable time windows.

    Provides statistical analysis of metric data including:
    - Count, sum, min, max, average
    - Percentiles (p50, p75, p90, p95, p99)
    - Rate calculations for counters
    """

    def __init__(self, collector: Optional[MetricsCollector] = None):
        """
        Initialize aggregator.

        Args:
            collector: MetricsCollector instance (uses global if not provided)
        """
        self._collector = collector
        self._previous_counters: Dict[str, float] = {}
        self._previous_timestamp: Optional[datetime] = None

    @property
    def collector(self) -> MetricsCollector:
        """Get collector instance."""
        if self._collector is None:
            from services.observability.metrics.collector import get_collector

            self._collector = get_collector()
        return self._collector

    def aggregate(
        self,
        window_seconds: int = 60,
    ) -> Dict[str, AggregatedMetric]:
        """
        Aggregate all metrics.

        Args:
            window_seconds: Time window for rate calculations

        Returns:
            Dictionary of metric name to aggregated metric
        """
        result = {}
        now = datetime.now(timezone.utc)
        timestamp = now.isoformat()

        # Process each metric type
        result.update(self._aggregate_counters(window_seconds, timestamp, now))
        result.update(self._aggregate_gauges(window_seconds, timestamp))
        result.update(self._aggregate_histograms(window_seconds, timestamp))

        self._previous_timestamp = now
        return result

    def _aggregate_counters(
        self,
        window_seconds: int,
        timestamp: str,
        now: datetime,
    ) -> Dict[str, AggregatedMetric]:
        """Aggregate counter metrics with rate calculation."""
        result = {}

        for name, values in self.collector._counters.items():
            for key, value in values.items():
                labels = self.collector._parse_labels_key(key)
                metric_key = f"{name}:{key}"

                # Calculate rate
                rate = None
                if self._previous_timestamp is not None:
                    elapsed = (now - self._previous_timestamp).total_seconds()
                    if elapsed > 0 and metric_key in self._previous_counters:
                        delta = value - self._previous_counters[metric_key]
                        rate = delta / elapsed

                self._previous_counters[metric_key] = value

                result[metric_key] = AggregatedMetric(
                    name=name,
                    type=MetricType.COUNTER,
                    labels=labels,
                    window_seconds=window_seconds,
                    timestamp=timestamp,
                    count=1,
                    sum=value,
                    min=value,
                    max=value,
                    avg=value,
                    rate_per_second=rate,
                )

        return result

    def _aggregate_gauges(
        self,
        window_seconds: int,
        timestamp: str,
    ) -> Dict[str, AggregatedMetric]:
        """Aggregate gauge metrics."""
        result = {}

        for name, values in self.collector._gauges.items():
            for key, value in values.items():
                labels = self.collector._parse_labels_key(key)
                metric_key = f"{name}:{key}"

                result[metric_key] = AggregatedMetric(
                    name=name,
                    type=MetricType.GAUGE,
                    labels=labels,
                    window_seconds=window_seconds,
                    timestamp=timestamp,
                    count=1,
                    sum=value,
                    min=value,
                    max=value,
                    avg=value,
                )

        return result

    def _aggregate_histograms(
        self,
        window_seconds: int,
        timestamp: str,
    ) -> Dict[str, AggregatedMetric]:
        """Aggregate histogram metrics with percentiles."""
        result = {}

        for name, values in self.collector._histograms.items():
            for key, samples in values.items():
                if not samples:
                    continue

                labels = self.collector._parse_labels_key(key)
                metric_key = f"{name}:{key}"

                # Calculate statistics
                count = len(samples)
                total = sum(samples)
                minimum = min(samples)
                maximum = max(samples)
                avg = total / count if count > 0 else 0

                # Calculate percentiles
                sorted_samples = sorted(samples)
                p50 = self._percentile(sorted_samples, 50)
                p75 = self._percentile(sorted_samples, 75)
                p90 = self._percentile(sorted_samples, 90)
                p95 = self._percentile(sorted_samples, 95)
                p99 = self._percentile(sorted_samples, 99)

                result[metric_key] = AggregatedMetric(
                    name=name,
                    type=MetricType.HISTOGRAM,
                    labels=labels,
                    window_seconds=window_seconds,
                    timestamp=timestamp,
                    count=count,
                    sum=total,
                    min=minimum,
                    max=maximum,
                    avg=avg,
                    p50=p50,
                    p75=p75,
                    p90=p90,
                    p95=p95,
                    p99=p99,
                )

        return result

    def _percentile(self, sorted_data: List[float], percentile: float) -> float:
        """
        Calculate percentile of sorted data.

        Args:
            sorted_data: Sorted list of values
            percentile: Percentile to calculate (0-100)

        Returns:
            Percentile value
        """
        if not sorted_data:
            return 0.0

        n = len(sorted_data)
        if n == 1:
            return sorted_data[0]

        # Calculate index
        k = (percentile / 100) * (n - 1)
        f = int(k)
        c = f + 1 if f + 1 < n else f

        # Linear interpolation
        if f == c:
            return sorted_data[f]

        return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all metrics.

        Returns:
            Summary dictionary with counts by type
        """
        aggregated = self.aggregate()

        counters = [m for m in aggregated.values() if m.type == MetricType.COUNTER]
        gauges = [m for m in aggregated.values() if m.type == MetricType.GAUGE]
        histograms = [m for m in aggregated.values() if m.type == MetricType.HISTOGRAM]

        return {
            "total_metrics": len(aggregated),
            "counters": len(counters),
            "gauges": len(gauges),
            "histograms": len(histograms),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_dashboard_data(self, window_seconds: int = 60) -> Dict[str, Any]:
        """
        Get pre-aggregated data for dashboard display.

        Args:
            window_seconds: Time window for calculations

        Returns:
            Dashboard-ready data structure
        """
        aggregated = self.aggregate(window_seconds)

        # Group by category
        workflows = {}
        nodes = {}
        queue = {}
        workers = {}
        api = {}
        errors = {}

        for key, metric in aggregated.items():
            data = metric.to_dict()

            if metric.name.startswith("workflow_"):
                workflows[metric.name] = data
            elif metric.name.startswith("node_"):
                nodes[metric.name] = data
            elif metric.name.startswith("queue_"):
                queue[metric.name] = data
            elif metric.name.startswith("worker_"):
                workers[metric.name] = data
            elif metric.name.startswith("http_"):
                api[metric.name] = data
            elif metric.name.startswith("error"):
                errors[metric.name] = data

        return {
            "workflow": workflows,
            "node": nodes,
            "queue": queue,
            "worker": workers,
            "api": api,
            "errors": errors,
            "summary": self.get_summary(),
        }
