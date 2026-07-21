"""
Log Stream Interface

Abstract interface for log streaming implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class LogLevel(Enum):
    """Log severity levels (RFC 5424)."""
    EMERGENCY = 0
    ALERT = 1
    CRITICAL = 2
    ERROR = 3
    WARNING = 4
    NOTICE = 5
    INFO = 6
    DEBUG = 7


class LogCategory(Enum):
    """Log event categories."""
    AUDIT = "audit"
    SECURITY = "security"
    EXECUTION = "execution"
    SYSTEM = "system"
    ACCESS = "access"


@dataclass
class LogEvent:
    """
    Standard log event format for streaming.

    Compatible with:
    - Splunk Common Information Model (CIM)
    - Elastic Common Schema (ECS)
    - OCSF (Open Cybersecurity Schema Framework)
    """
    # Required fields
    timestamp: str
    level: LogLevel
    category: LogCategory
    message: str

    # Event identification
    event_id: Optional[str] = None
    event_type: Optional[str] = None
    event_action: Optional[str] = None

    # Source identification
    source_system: str = "flyto"
    source_component: Optional[str] = None
    source_version: Optional[str] = None

    # Actor information
    actor_id: Optional[str] = None
    actor_type: Optional[str] = None
    actor_ip: Optional[str] = None
    actor_user_agent: Optional[str] = None

    # Resource information
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None

    # Organization context
    org_id: Optional[str] = None
    org_name: Optional[str] = None

    # Execution context
    execution_id: Optional[str] = None
    workflow_id: Optional[str] = None
    trace_id: Optional[str] = None

    # Outcome
    outcome: Optional[str] = None  # success, failure, unknown
    outcome_reason: Optional[str] = None

    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.event_id:
            import uuid
            self.event_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp,
            "level": self.level.name.lower(),
            "level_code": self.level.value,
            "category": self.category.value,
            "message": self.message,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "event_action": self.event_action,
            "source": {
                "system": self.source_system,
                "component": self.source_component,
                "version": self.source_version,
            },
            "actor": {
                "id": self.actor_id,
                "type": self.actor_type,
                "ip": self.actor_ip,
                "user_agent": self.actor_user_agent,
            } if self.actor_id else None,
            "resource": {
                "type": self.resource_type,
                "id": self.resource_id,
                "name": self.resource_name,
            } if self.resource_type else None,
            "organization": {
                "id": self.org_id,
                "name": self.org_name,
            } if self.org_id else None,
            "execution": {
                "id": self.execution_id,
                "workflow_id": self.workflow_id,
                "trace_id": self.trace_id,
            } if self.execution_id else None,
            "outcome": self.outcome,
            "outcome_reason": self.outcome_reason,
            "metadata": self.metadata,
            "tags": self.tags,
        }

    def to_ecs(self) -> Dict[str, Any]:
        """Convert to Elastic Common Schema format."""
        return {
            "@timestamp": self.timestamp,
            "log": {
                "level": self.level.name.lower(),
            },
            "event": {
                "id": self.event_id,
                "type": self.event_type,
                "action": self.event_action,
                "category": self.category.value,
                "outcome": self.outcome,
            },
            "message": self.message,
            "source": {
                "address": self.actor_ip,
            },
            "user": {
                "id": self.actor_id,
            } if self.actor_id else None,
            "user_agent": {
                "original": self.actor_user_agent,
            } if self.actor_user_agent else None,
            "organization": {
                "id": self.org_id,
            } if self.org_id else None,
            "labels": self.metadata,
            "tags": self.tags,
        }

    def to_syslog(self) -> str:
        """Convert to syslog format (RFC 5424)."""
        # Format: <priority>version timestamp hostname app-name procid msgid structured-data msg
        priority = self.level.value + 8  # Facility 1 (user-level)
        hostname = "-"
        app_name = self.source_system
        procid = self.execution_id or "-"
        msgid = self.event_type or "-"

        structured_data = ""
        if self.actor_id or self.org_id:
            sd_parts = []
            if self.actor_id:
                sd_parts.append(f'actor="{self.actor_id}"')
            if self.org_id:
                sd_parts.append(f'org="{self.org_id}"')
            structured_data = f'[flyto {" ".join(sd_parts)}]'
        else:
            structured_data = "-"

        return f"<{priority}>1 {self.timestamp} {hostname} {app_name} {procid} {msgid} {structured_data} {self.message}"


@dataclass
class StreamConfig:
    """Configuration for a log stream."""
    enabled: bool = True
    min_level: LogLevel = LogLevel.INFO
    categories: Optional[List[LogCategory]] = None  # None = all
    batch_size: int = 100
    flush_interval_seconds: float = 5.0
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class LogStreamInterface(ABC):
    """
    Abstract interface for log streaming backends.

    Implementations must be async-safe and handle their own buffering.
    """

    def __init__(self, config: Optional[StreamConfig] = None):
        """
        Initialize stream.

        Args:
            config: Stream configuration
        """
        self.config = config or StreamConfig()

    @abstractmethod
    async def push(self, event: LogEvent) -> bool:
        """
        Push a single log event.

        Args:
            event: Log event to push

        Returns:
            True if successfully pushed
        """
        pass

    @abstractmethod
    async def push_batch(self, events: List[LogEvent]) -> int:
        """
        Push a batch of log events.

        Args:
            events: List of log events

        Returns:
            Number of successfully pushed events
        """
        pass

    @abstractmethod
    async def flush(self) -> int:
        """
        Flush any buffered events.

        Returns:
            Number of flushed events
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check stream health.

        Returns:
            Health status dict
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the stream and cleanup resources."""
        pass

    def should_stream(self, event: LogEvent) -> bool:
        """
        Check if event should be streamed based on config.

        Args:
            event: Event to check

        Returns:
            True if event should be streamed
        """
        if not self.config.enabled:
            return False

        if event.level.value > self.config.min_level.value:
            return False

        if self.config.categories and event.category not in self.config.categories:
            return False

        return True
