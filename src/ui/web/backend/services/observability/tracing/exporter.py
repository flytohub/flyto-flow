"""
Trace Exporter

Single responsibility: Export traces to backend storage.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from services.observability.tracing.span import Span

logger = logging.getLogger(__name__)


class TraceExporter(ABC):
    """
    Abstract base class for trace exporters.

    Exporters are responsible for sending completed spans to
    a trace collection backend.
    """

    @abstractmethod
    def export(self, spans: List[Span]) -> bool:
        """
        Export a batch of spans.

        Args:
            spans: List of spans to export

        Returns:
            True if export successful
        """
        pass

    def shutdown(self) -> None:
        """Shutdown the exporter (cleanup resources)."""
        pass


class ConsoleTraceExporter(TraceExporter):
    """
    Export traces to console/stdout.

    Useful for development and debugging.
    """

    def __init__(self, pretty: bool = True):
        """
        Initialize console exporter.

        Args:
            pretty: Pretty-print JSON output
        """
        self.pretty = pretty

    def export(self, spans: List[Span]) -> bool:
        """Export spans to console."""
        for span in spans:
            data = span.to_dict()
            if self.pretty:
                output = json.dumps(data, indent=2)
            else:
                output = json.dumps(data)
            print(f"[TRACE] {output}")
        return True


class JsonFileTraceExporter(TraceExporter):
    """
    Export traces to JSON files.

    One file per trace, stored in a directory structure.
    """

    def __init__(
        self,
        output_dir: str = "traces",
        max_files: int = 1000,
    ):
        """
        Initialize file exporter.

        Args:
            output_dir: Directory to store trace files
            max_files: Maximum files to keep (oldest deleted)
        """
        self.output_dir = Path(output_dir)
        self.max_files = max_files
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(self, spans: List[Span]) -> bool:
        """Export spans to JSON files."""
        try:
            for span in spans:
                self._write_span(span)
            self._cleanup_old_files()
            return True
        except Exception as e:
            logger.error(f"Failed to export traces: {e}")
            return False

    def _write_span(self, span: Span) -> None:
        """Write a single span to file."""
        # Create directory for trace
        trace_dir = self.output_dir / span.trace_id[:8]
        trace_dir.mkdir(exist_ok=True)

        # Write span file
        filename = f"{span.span_id}.json"
        filepath = trace_dir / filename

        with open(filepath, "w") as f:
            json.dump(span.to_dict(), f, indent=2)

    def _cleanup_old_files(self) -> None:
        """Remove old trace files if over limit."""
        try:
            # Get all trace directories
            trace_dirs = list(self.output_dir.iterdir())
            if len(trace_dirs) <= self.max_files:
                return

            # Sort by modification time
            trace_dirs.sort(key=lambda p: p.stat().st_mtime)

            # Remove oldest
            to_remove = len(trace_dirs) - self.max_files
            for trace_dir in trace_dirs[:to_remove]:
                for f in trace_dir.iterdir():
                    f.unlink()
                trace_dir.rmdir()

        except Exception as e:
            logger.warning(f"Failed to cleanup old traces: {e}")


class InMemoryTraceExporter(TraceExporter):
    """
    Export traces to in-memory storage.

    Useful for testing and short-term storage.
    """

    def __init__(self, max_spans: int = 10000):
        """
        Initialize in-memory exporter.

        Args:
            max_spans: Maximum spans to keep
        """
        self.max_spans = max_spans
        self._spans: List[Span] = []

    def export(self, spans: List[Span]) -> bool:
        """Export spans to memory."""
        self._spans.extend(spans)

        # Trim if over limit
        if len(self._spans) > self.max_spans:
            self._spans = self._spans[-self.max_spans:]

        return True

    def get_spans(self) -> List[Span]:
        """Get all stored spans."""
        return list(self._spans)

    def get_trace(self, trace_id: str) -> List[Span]:
        """Get all spans for a trace."""
        return [s for s in self._spans if s.trace_id == trace_id]

    def clear(self) -> None:
        """Clear all stored spans."""
        self._spans.clear()


class MultiTraceExporter(TraceExporter):
    """
    Export traces to multiple backends.

    Combines multiple exporters, exporting to all of them.
    """

    def __init__(self, exporters: List[TraceExporter]):
        """
        Initialize multi-exporter.

        Args:
            exporters: List of exporters to use
        """
        self.exporters = exporters

    def export(self, spans: List[Span]) -> bool:
        """Export to all exporters."""
        success = True
        for exporter in self.exporters:
            try:
                if not exporter.export(spans):
                    success = False
            except Exception as e:
                logger.error(f"Exporter {type(exporter).__name__} failed: {e}")
                success = False
        return success

    def shutdown(self) -> None:
        """Shutdown all exporters."""
        for exporter in self.exporters:
            try:
                exporter.shutdown()
            except Exception as e:
                logger.error(f"Failed to shutdown {type(exporter).__name__}: {e}")


class SqliteTraceExporter(TraceExporter):
    """
    Export traces to SQLite database via TraceRepository.

    Persists spans for query via the traces API.
    """

    def export(self, spans: List[Span]) -> bool:
        """Export spans to SQLite."""
        try:
            from gateway.storage.trace_repo import TraceRepository

            span_dicts = [span.to_dict() for span in spans]
            TraceRepository.save_spans(span_dicts)

            return True
        except Exception as e:
            logger.error(f"Failed to export traces to SQLite: {e}")
            return False


class BatchTraceExporter(TraceExporter):
    """
    Batch spans before exporting.

    Collects spans and exports them in batches for efficiency.
    """

    def __init__(
        self,
        delegate: TraceExporter,
        batch_size: int = 100,
        max_wait_seconds: float = 5.0,
    ):
        """
        Initialize batch exporter.

        Args:
            delegate: Underlying exporter to use
            batch_size: Number of spans to collect before export
            max_wait_seconds: Maximum time to wait before flush
        """
        self.delegate = delegate
        self.batch_size = batch_size
        self.max_wait_seconds = max_wait_seconds
        self._buffer: List[Span] = []
        self._last_flush = datetime.now(timezone.utc)

    def export(self, spans: List[Span]) -> bool:
        """Add spans to buffer, export if batch full."""
        self._buffer.extend(spans)

        if len(self._buffer) >= self.batch_size:
            return self.flush()

        # Check time since last flush
        now = datetime.now(timezone.utc)
        elapsed = (now - self._last_flush).total_seconds()
        if elapsed >= self.max_wait_seconds and self._buffer:
            return self.flush()

        return True

    def flush(self) -> bool:
        """Flush buffer to delegate exporter."""
        if not self._buffer:
            return True

        spans = self._buffer
        self._buffer = []
        self._last_flush = datetime.now(timezone.utc)

        return self.delegate.export(spans)

    def shutdown(self) -> None:
        """Flush remaining and shutdown."""
        self.flush()
        self.delegate.shutdown()
