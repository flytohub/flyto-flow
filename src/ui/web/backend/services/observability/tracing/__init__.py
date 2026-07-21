"""
Distributed Tracing Services.

This module provides:
- Span: Trace span data model
- Tracer: Span creation and management
- TraceContext: Context propagation
- TraceSampler: Sampling decisions
- TraceExporter: Export to backends
"""

from services.observability.tracing.span import Span, SpanStatus, SpanEvent
from services.observability.tracing.tracer import Tracer, get_tracer
from services.observability.tracing.context import (
    get_current_span,
    set_current_span,
    get_trace_context,
    TraceContext,
)
from services.observability.tracing.sampler import TraceSampler, SamplingDecision, SamplerConfig
from services.observability.tracing.exporter import (
    TraceExporter,
    ConsoleTraceExporter,
    JsonFileTraceExporter,
    SqliteTraceExporter,
)

__all__ = [
    "Span",
    "SpanStatus",
    "SpanEvent",
    "Tracer",
    "get_tracer",
    "get_current_span",
    "set_current_span",
    "get_trace_context",
    "TraceContext",
    "TraceSampler",
    "SamplingDecision",
    "SamplerConfig",
    "TraceExporter",
    "ConsoleTraceExporter",
    "JsonFileTraceExporter",
    "SqliteTraceExporter",
]
