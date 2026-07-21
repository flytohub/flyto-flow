"""Telemetry provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Sequence

TelemetryFilter = tuple[str, str, Any]
TelemetryOrder = tuple[str, Any]


@dataclass
class TelemetryRecord:
    """Provider-neutral telemetry record."""

    id: str
    data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return a copy of the record payload."""
        return dict(self.data)


class TelemetryProvider(ABC):
    """Provider interface for telemetry event and presence persistence."""

    @property
    @abstractmethod
    def server_timestamp(self) -> Any:
        """Return the provider-specific server timestamp sentinel."""
        pass

    @property
    @abstractmethod
    def descending_order(self) -> Any:
        """Return the provider-specific descending order value."""
        pass

    @abstractmethod
    def save_event(self, event: dict[str, Any]) -> str:
        """Persist a telemetry event and return its record ID."""
        pass

    @abstractmethod
    def has_event_with_dedupe_key(self, dedupe_key: str) -> bool:
        """Return whether a telemetry event already exists for the dedupe key."""
        pass

    @abstractmethod
    def query_events(
        self,
        filters: Sequence[TelemetryFilter] = (),
        limit: int | None = None,
        order_by: TelemetryOrder | None = None,
    ) -> list[TelemetryRecord]:
        """Query telemetry events."""
        pass

    @abstractmethod
    def save_presence(
        self,
        user_id: str,
        data: dict[str, Any],
        merge: bool = True,
    ) -> None:
        """Persist a user presence record."""
        pass

    @abstractmethod
    def list_presence(self) -> list[TelemetryRecord]:
        """List user presence records."""
        pass
