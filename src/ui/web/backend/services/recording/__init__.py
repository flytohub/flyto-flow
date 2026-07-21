"""
Recording Service Package

Browser recording functionality using Playwright.
"""

from services.recording.models import (
    ActionType,
    RecordedAction,
    RecordingSession,
    SelectorStrategy,
)
from services.recording.hooks import RECORDING_SCRIPT
from services.recording.service import RecordingService


__all__ = [
    # Models
    "ActionType",
    "RecordedAction",
    "RecordingSession",
    "SelectorStrategy",
    # Hooks
    "RECORDING_SCRIPT",
    # Service
    "RecordingService",
]
