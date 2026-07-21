"""
Time Range Utilities

Atomic utilities for time range calculations.
Single responsibility: parse time range strings to datetime objects.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal, Tuple

# Type alias for supported time ranges
TimeRangeStr = Literal["24h", "7d", "30d", "90d"]

# Mapping from time range string to days
TIME_RANGE_DAYS = {
    "24h": 1,
    "7d": 7,
    "30d": 30,
    "90d": 90,
}


@dataclass(frozen=True)
class TimeRange:
    """Immutable time range with start and end datetimes."""

    start: datetime
    end: datetime
    days: int

    @property
    def previous_start(self) -> datetime:
        """Get start of previous period (for comparison)."""
        return self.start - timedelta(days=self.days)


def parse_time_range(
    range_str: TimeRangeStr,
    end_time: datetime = None,
) -> TimeRange:
    """
    Parse time range string to TimeRange object.

    Args:
        range_str: Time range string (24h, 7d, 30d, 90d)
        end_time: End time (defaults to now)

    Returns:
        TimeRange object with start, end, and days

    Example:
        >>> tr = parse_time_range("7d")
        >>> tr.days
        7
    """
    if end_time is None:
        end_time = datetime.now(timezone.utc)

    days = TIME_RANGE_DAYS.get(range_str, 7)
    start_time = end_time - timedelta(days=days)

    return TimeRange(start=start_time, end=end_time, days=days)


def get_comparison_ranges(
    range_str: TimeRangeStr,
    end_time: datetime = None,
) -> Tuple[TimeRange, TimeRange]:
    """
    Get current and previous time ranges for comparison.

    Args:
        range_str: Time range string (24h, 7d, 30d, 90d)
        end_time: End time (defaults to now)

    Returns:
        Tuple of (current_range, previous_range)

    Example:
        >>> current, previous = get_comparison_ranges("7d")
        >>> # current: last 7 days
        >>> # previous: 7 days before that
    """
    current = parse_time_range(range_str, end_time)
    previous = TimeRange(
        start=current.previous_start,
        end=current.start,
        days=current.days,
    )
    return current, previous
