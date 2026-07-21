"""
Prometheus Exporter

Single responsibility: Export metrics in Prometheus text format.
"""

import logging
from typing import Dict, List, Optional

from services.observability.metrics.collector import Metric, MetricType, MetricsCollector

logger = logging.getLogger(__name__)


class PrometheusExporter:
    """
    Export metrics in Prometheus text format.

    Format specification: https://prometheus.io/docs/instrumenting/exposition_formats/
    """

    def __init__(self, collector: Optional[MetricsCollector] = None):
        """
        Initialize exporter.

        Args:
            collector: MetricsCollector instance (uses global if not provided)
        """
        self._collector = collector

    @property
    def collector(self) -> MetricsCollector:
        """Get collector instance."""
        if self._collector is None:
            from services.observability.metrics.collector import get_collector

            self._collector = get_collector()
        return self._collector

    def export(self) -> str:
        """
        Export all metrics in Prometheus text format.

        Returns:
            Prometheus-formatted metrics string
        """
        metrics = self.collector.get_all_metrics()
        return self._format_metrics(metrics)

    def _format_metrics(self, metrics: List[Metric]) -> str:
        """Format metrics list to Prometheus text format."""
        lines = []
        seen_help = set()

        for metric in metrics:
            # Add HELP and TYPE lines (once per metric name)
            if metric.name not in seen_help:
                if metric.help_text:
                    lines.append(f"# HELP {metric.name} {self._escape_help(metric.help_text)}")
                lines.append(f"# TYPE {metric.name} {self._prometheus_type(metric.type)}")
                seen_help.add(metric.name)

            # Format based on type
            if metric.type == MetricType.HISTOGRAM:
                lines.extend(self._format_histogram(metric))
            else:
                lines.extend(self._format_simple(metric))

        return "\n".join(lines) + "\n"

    def _format_simple(self, metric: Metric) -> List[str]:
        """Format counter or gauge metric."""
        lines = []
        for sample in metric.samples:
            # Merge metric labels with sample labels
            all_labels = {**metric.labels, **sample.labels}
            # Remove internal labels
            all_labels = {k: v for k, v in all_labels.items() if not k.startswith("_")}

            label_str = self._format_labels(all_labels)
            lines.append(f"{metric.name}{label_str} {self._format_value(sample.value)}")

        return lines

    def _format_histogram(self, metric: Metric) -> List[str]:
        """Format histogram metric with buckets."""
        lines = []

        # Parse bucket counts from labels
        buckets_str = metric.labels.get("_buckets", "{}")
        try:
            import json
            buckets = json.loads(buckets_str.replace("'", '"'))
        except Exception:
            buckets = {}

        # Get base labels (without internal ones)
        base_labels = {k: v for k, v in metric.labels.items() if not k.startswith("_")}

        # Output bucket counts
        for bucket, count in sorted(buckets.items(), key=lambda x: (x[0] == "+Inf", float(x[0]) if x[0] != "+Inf" else float("inf"))):
            labels = {**base_labels, "le": bucket}
            label_str = self._format_labels(labels)
            lines.append(f"{metric.name}_bucket{label_str} {count}")

        # Output sum and count
        if metric.samples:
            total = metric.samples[0].value
            count = buckets.get("+Inf", 0)

            label_str = self._format_labels(base_labels)
            lines.append(f"{metric.name}_sum{label_str} {self._format_value(total)}")
            lines.append(f"{metric.name}_count{label_str} {count}")

        return lines

    def _format_labels(self, labels: Dict[str, str]) -> str:
        """Format labels as Prometheus label string."""
        if not labels:
            return ""

        parts = []
        for key, value in sorted(labels.items()):
            escaped_value = self._escape_label_value(str(value))
            parts.append(f'{key}="{escaped_value}"')

        return "{" + ",".join(parts) + "}"

    def _format_value(self, value: float) -> str:
        """Format numeric value."""
        if value == float("inf"):
            return "+Inf"
        if value == float("-inf"):
            return "-Inf"
        if value != value:  # NaN check
            return "NaN"

        # Use scientific notation for very large/small values
        if abs(value) >= 1e15 or (abs(value) < 1e-6 and value != 0):
            return f"{value:.6e}"

        # Otherwise use fixed notation
        if value == int(value):
            return str(int(value))
        return f"{value:.6f}".rstrip("0").rstrip(".")

    def _prometheus_type(self, metric_type: MetricType) -> str:
        """Convert MetricType to Prometheus type string."""
        return metric_type.value

    def _escape_help(self, text: str) -> str:
        """Escape help text for Prometheus format."""
        return text.replace("\\", "\\\\").replace("\n", "\\n")

    def _escape_label_value(self, value: str) -> str:
        """Escape label value for Prometheus format."""
        return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def export_prometheus(collector: Optional[MetricsCollector] = None) -> str:
    """
    Convenience function to export metrics in Prometheus format.

    Args:
        collector: Optional collector instance

    Returns:
        Prometheus-formatted metrics string
    """
    exporter = PrometheusExporter(collector)
    return exporter.export()
