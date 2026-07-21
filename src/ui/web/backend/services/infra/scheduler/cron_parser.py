"""
Cron Parser

Simple cron expression parser for schedule timing.
"""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class CronValidationResult:
    """Result of cron expression validation."""
    valid: bool
    error: Optional[str] = None
    next_run: Optional[datetime] = None


class CronParser:
    """
    Simple cron expression parser.

    Format: minute hour day_of_month month day_of_week
    Examples:
        "0 9 * * *"     - Every day at 9:00 AM
        "*/15 * * * *"  - Every 15 minutes
        "0 0 1 * *"     - First day of every month at midnight
    """

    @classmethod
    def get_next_run(
        cls,
        expression: str,
        from_time: Optional[datetime] = None,
        timezone_str: str = "UTC",
    ) -> datetime:
        """
        Calculate next run time from cron expression.

        Args:
            expression: Cron expression (5 fields)
            from_time: Base time (defaults to now UTC)
            timezone_str: IANA timezone for cron matching (e.g. "Asia/Taipei")

        Returns:
            Next scheduled run time (UTC)
        """
        if from_time is None:
            from_time = datetime.now(timezone.utc)

        parts = expression.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {expression}")

        minute, hour, day, month, dow = parts

        # Resolve target timezone for cron matching
        try:
            tz = ZoneInfo(timezone_str)
        except (KeyError, Exception):
            tz = timezone.utc

        # Convert to target timezone so cron fields match local time
        local_time = from_time.astimezone(tz)

        # Start from next minute in local time
        candidate = local_time.replace(second=0, microsecond=0) + timedelta(minutes=1)

        # Search for matching time (max 1 year)
        max_iterations = 525600  # minutes in a year
        for _ in range(max_iterations):
            if cls._matches(candidate, minute, hour, day, month, dow):
                # Return as UTC for consistent storage
                return candidate.astimezone(timezone.utc)
            candidate += timedelta(minutes=1)

        # Fallback: return from_time + 1 day
        return from_time + timedelta(days=1)

    @classmethod
    def _matches(
        cls,
        dt: datetime,
        minute: str,
        hour: str,
        day: str,
        month: str,
        dow: str,
    ) -> bool:
        """Check if datetime matches cron fields."""
        return (
            cls._field_matches(dt.minute, minute, 0, 59)
            and cls._field_matches(dt.hour, hour, 0, 23)
            and cls._field_matches(dt.day, day, 1, 31)
            and cls._field_matches(dt.month, month, 1, 12)
            and cls._field_matches(dt.weekday(), dow, 0, 6)  # Monday=0
        )

    @classmethod
    def _field_matches(cls, value: int, field: str, min_val: int, max_val: int) -> bool:
        """Check if value matches cron field."""
        if field == "*":
            return True

        # Handle step values: */5
        if field.startswith("*/"):
            step = int(field[2:])
            return value % step == 0

        # Handle ranges: 1-5
        if "-" in field:
            start, end = field.split("-")
            return int(start) <= value <= int(end)

        # Handle lists: 1,3,5
        if "," in field:
            values = [int(v) for v in field.split(",")]
            return value in values

        # Single value
        return value == int(field)

    @classmethod
    def validate(cls, expression: str) -> CronValidationResult:
        """
        Validate a cron expression.

        Args:
            expression: Cron expression to validate

        Returns:
            CronValidationResult with valid flag, error message, and next run time

        Example:
            >>> result = CronParser.validate("0 9 * * *")
            >>> if not result.valid:
            ...     raise ValueError(result.error)
        """
        if not expression or not expression.strip():
            return CronValidationResult(
                valid=False,
                error="Cron expression cannot be empty",
            )

        try:
            next_run = cls.get_next_run(expression)
            return CronValidationResult(
                valid=True,
                next_run=next_run,
            )
        except ValueError as e:
            return CronValidationResult(
                valid=False,
                error=str(e),
            )
        except Exception as e:
            return CronValidationResult(
                valid=False,
                error=f"Invalid cron expression: {e}",
            )
