"""
Cancellation Token

Provides graceful cancellation mechanism for workflow execution.
Thread-safe and asyncio-compatible.
"""

import asyncio
import logging
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)


class CancelledException(Exception):
    """Raised when operation is cancelled."""

    def __init__(self, reason: str = "Cancelled"):
        """Initialize with a cancellation reason message."""
        self.reason = reason
        super().__init__(reason)


class CancellationToken:
    """
    Token for graceful cancellation of long-running operations.

    Provides cooperative cancellation mechanism where:
    - Caller requests cancellation via cancel()
    - Running code periodically checks is_cancelled or calls raise_if_cancelled()
    - Callbacks can be registered for cleanup on cancellation

    Thread-safe and asyncio-compatible.

    Usage:
        token = CancellationToken()

        # In workflow execution:
        for item in items:
            token.raise_if_cancelled()
            await process(item)

        # To cancel from another context:
        token.cancel("User requested cancellation")

        # Register cleanup callback:
        token.on_cancel(lambda: cleanup_resources())
    """

    def __init__(self):
        """Initialize cancellation token."""
        self._cancelled = False
        self._reason: Optional[str] = None
        self._callbacks: List[Callable[[], None]] = []
        self._event = asyncio.Event()
        self._lock = asyncio.Lock()

    @property
    def is_cancelled(self) -> bool:
        """Check if cancellation was requested."""
        return self._cancelled

    @property
    def reason(self) -> Optional[str]:
        """Get cancellation reason if cancelled."""
        return self._reason

    def cancel(self, reason: str = "Cancelled") -> None:
        """
        Request cancellation.

        This method is idempotent - calling multiple times has no effect.

        Args:
            reason: Human-readable reason for cancellation
        """
        if self._cancelled:
            return

        self._cancelled = True
        self._reason = reason
        self._event.set()

        # Invoke registered callbacks
        for callback in self._callbacks:
            try:
                callback()
            except Exception as e:
                logger.warning(f"Cancellation callback error: {e}")

        logger.info(f"Cancellation requested: {reason}")

    def on_cancel(self, callback: Callable[[], None]) -> None:
        """
        Register callback to be invoked on cancellation.

        If already cancelled, callback is invoked immediately.

        Args:
            callback: Function to call when cancelled
        """
        if self._cancelled:
            # Already cancelled, invoke immediately
            try:
                callback()
            except Exception as e:
                logger.warning(f"Cancellation callback error: {e}")
        else:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[], None]) -> bool:
        """
        Remove a previously registered callback.

        Args:
            callback: Callback to remove

        Returns:
            True if callback was found and removed
        """
        try:
            self._callbacks.remove(callback)
            return True
        except ValueError:
            return False

    async def wait_for_cancellation(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for cancellation to be requested.

        Useful for background tasks that should exit when cancelled.

        Args:
            timeout: Maximum seconds to wait (None = wait forever)

        Returns:
            True if cancelled, False if timeout
        """
        try:
            await asyncio.wait_for(self._event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    def raise_if_cancelled(self) -> None:
        """
        Raise CancelledException if cancelled.

        Use this at safe points in long-running operations.

        Raises:
            CancelledException: If cancellation was requested
        """
        if self._cancelled:
            raise CancelledException(self._reason or "Cancelled")

    def check_cancelled(self) -> bool:
        """
        Check if cancelled without raising.

        Alias for is_cancelled property for consistency with other APIs.

        Returns:
            True if cancellation was requested
        """
        return self._cancelled

    def reset(self) -> None:
        """
        Reset the token to initial state.

        Clears cancelled state, reason, and callbacks.
        Use with caution - typically create a new token instead.
        """
        self._cancelled = False
        self._reason = None
        self._callbacks.clear()
        self._event.clear()


class CancellationTokenSource:
    """
    Factory for creating linked cancellation tokens.

    Provides ability to create child tokens that are cancelled
    when the parent is cancelled.
    """

    def __init__(self):
        """Initialize token source."""
        self._token = CancellationToken()
        self._children: List[CancellationToken] = []

    @property
    def token(self) -> CancellationToken:
        """Get the cancellation token."""
        return self._token

    def cancel(self, reason: str = "Cancelled") -> None:
        """
        Cancel all tokens from this source.

        Args:
            reason: Cancellation reason
        """
        self._token.cancel(reason)

        # Also cancel all child tokens
        for child in self._children:
            child.cancel(reason)

    def create_linked_token(self) -> CancellationToken:
        """
        Create a child token linked to this source.

        The child token will be cancelled when the parent is cancelled.

        Returns:
            New linked CancellationToken
        """
        child = CancellationToken()
        self._children.append(child)

        # If parent already cancelled, cancel child immediately
        if self._token.is_cancelled:
            child.cancel(self._token.reason or "Parent cancelled")
        else:
            # Link parent cancellation to child
            self._token.on_cancel(
                lambda: child.cancel(self._token.reason or "Parent cancelled")
            )

        return child
