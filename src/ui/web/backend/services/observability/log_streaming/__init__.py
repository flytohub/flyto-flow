"""
Log Streaming Module

Real-time log streaming to external SIEM systems.
Supports multiple backends: Webhook, Elasticsearch, Syslog, File.
"""

from services.observability.log_streaming.interface import (
    LogStreamInterface,
    LogEvent,
    LogLevel,
    LogCategory,
    StreamConfig,
)
from services.observability.log_streaming.manager import (
    LogStreamManager,
    ManagerConfig,
    StreamStatus,
    get_log_stream_manager,
    reset_log_stream_manager,
    configure_streams_from_env,
)
from services.observability.log_streaming.webhook_stream import WebhookStream, WebhookConfig
from services.observability.log_streaming.elasticsearch_stream import ElasticsearchStream, ElasticsearchConfig
from services.observability.log_streaming.syslog_stream import SyslogStream, SyslogConfig
from services.observability.log_streaming.file_stream import FileStream, FileConfig

__all__ = [
    # Interface
    "LogStreamInterface",
    "LogEvent",
    "LogLevel",
    "LogCategory",
    "StreamConfig",
    # Manager
    "LogStreamManager",
    "ManagerConfig",
    "StreamStatus",
    "get_log_stream_manager",
    "reset_log_stream_manager",
    "configure_streams_from_env",
    # Webhook
    "WebhookStream",
    "WebhookConfig",
    # Elasticsearch
    "ElasticsearchStream",
    "ElasticsearchConfig",
    # Syslog
    "SyslogStream",
    "SyslogConfig",
    # File
    "FileStream",
    "FileConfig",
]
