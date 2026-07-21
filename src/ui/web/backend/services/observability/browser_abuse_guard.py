"""
Browser Abuse Guard — Real-time detection and throttling of browser automation abuse.

Tracks per-user browser navigation frequency and blocks users who exceed
thresholds. Designed for cloud worker mode where users run browser workflows.

Detection signals:
- High-frequency navigations (> N goto calls per window)
- Rapid session creation
- SSRF/egress guard violations (blocked requests)

Actions:
- Rate-limit: Delay subsequent browser operations
- Suspend: Block browser access and notify admin
"""

import logging
import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class UserBrowserStats:
    """Per-user browser activity counters (sliding window)."""
    navigation_timestamps: list = field(default_factory=list)
    blocked_request_timestamps: list = field(default_factory=list)
    suspended_until: float = 0.0
    suspend_reason: str = ""


class BrowserAbuseGuard:
    """
    In-process browser abuse detector.

    Thresholds (per user, configurable):
    - max_navigations_per_window: Max browser.goto calls within the window
    - max_blocked_requests_per_window: Max egress guard blocks before suspend
    - window_seconds: Sliding window size
    - suspend_duration_seconds: How long to suspend abusive users
    """

    def __init__(
        self,
        max_navigations_per_window: int = 100,
        max_blocked_requests_per_window: int = 10,
        window_seconds: int = 600,  # 10 minutes
        suspend_duration_seconds: int = 3600,  # 1 hour
    ):
        self._max_nav = max_navigations_per_window
        self._max_blocked = max_blocked_requests_per_window
        self._window = window_seconds
        self._suspend_duration = suspend_duration_seconds
        self._users: Dict[str, UserBrowserStats] = defaultdict(UserBrowserStats)
        self._lock = threading.Lock()
        self._on_suspend_callback = None

    def set_suspend_callback(self, callback):
        """Set callback(user_id, reason) called when a user is suspended."""
        self._on_suspend_callback = callback

    def check_navigation(self, user_id: str, url: str) -> Optional[str]:
        """
        Record a browser navigation and check for abuse.

        Args:
            user_id: Authenticated user ID
            url: Target URL

        Returns:
            None if allowed, or an error message if blocked/suspended
        """
        with self._lock:
            stats = self._users[user_id]
            now = time.time()

            # Check if currently suspended
            if stats.suspended_until > now:
                remaining = int(stats.suspended_until - now)
                return (
                    f"Browser access suspended for {remaining}s. "
                    f"Reason: {stats.suspend_reason}"
                )

            # Prune old entries
            cutoff = now - self._window
            stats.navigation_timestamps = [
                t for t in stats.navigation_timestamps if t > cutoff
            ]

            # Record this navigation
            stats.navigation_timestamps.append(now)

            # Check threshold
            count = len(stats.navigation_timestamps)
            if count > self._max_nav:
                reason = (
                    f"Excessive browser navigations: {count} in "
                    f"{self._window}s (limit: {self._max_nav})"
                )
                self._suspend_user(user_id, stats, reason)
                return reason

        return None

    def record_blocked_request(self, user_id: str, url: str):
        """
        Record an egress guard block (SSRF attempt etc.).

        Multiple blocked requests are a strong abuse signal.
        """
        with self._lock:
            stats = self._users[user_id]
            now = time.time()

            cutoff = now - self._window
            stats.blocked_request_timestamps = [
                t for t in stats.blocked_request_timestamps if t > cutoff
            ]
            stats.blocked_request_timestamps.append(now)

            count = len(stats.blocked_request_timestamps)
            if count >= self._max_blocked:
                reason = (
                    f"Repeated blocked requests: {count} SSRF/egress violations "
                    f"in {self._window}s (limit: {self._max_blocked})"
                )
                self._suspend_user(user_id, stats, reason)

    def is_suspended(self, user_id: str) -> bool:
        """Check if a user is currently suspended from browser access."""
        with self._lock:
            stats = self._users.get(user_id)
            if not stats:
                return False
            return stats.suspended_until > time.time()

    def _suspend_user(self, user_id: str, stats: UserBrowserStats, reason: str):
        """Suspend a user and fire callback."""
        stats.suspended_until = time.time() + self._suspend_duration
        stats.suspend_reason = reason
        logger.warning(
            "BROWSER ABUSE: user %s suspended for %ds — %s",
            user_id, self._suspend_duration, reason,
        )
        if self._on_suspend_callback:
            try:
                self._on_suspend_callback(user_id, reason)
            except Exception as e:
                logger.error("Suspend callback failed: %s", e)

    def get_stats(self, user_id: str) -> dict:
        """Get current stats for a user (admin use)."""
        with self._lock:
            stats = self._users.get(user_id)
            if not stats:
                return {"navigations": 0, "blocked": 0, "suspended": False}
            now = time.time()
            cutoff = now - self._window
            return {
                "navigations": len([
                    t for t in stats.navigation_timestamps if t > cutoff
                ]),
                "blocked": len([
                    t for t in stats.blocked_request_timestamps if t > cutoff
                ]),
                "suspended": stats.suspended_until > now,
                "suspended_until": stats.suspended_until if stats.suspended_until > now else None,
                "suspend_reason": stats.suspend_reason if stats.suspended_until > now else None,
            }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_guard: Optional[BrowserAbuseGuard] = None


def get_browser_abuse_guard() -> BrowserAbuseGuard:
    """Get or create the singleton BrowserAbuseGuard."""
    global _guard
    if _guard is None:
        _guard = BrowserAbuseGuard()
    return _guard
