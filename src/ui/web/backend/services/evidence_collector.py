"""
Evidence Collector Service

Collects execution evidence for debugging features:
- Screenshots and DOM snapshots for browser modules
- Context before/after each step
- Step timing and status

Writes to ./evidence/{execution_id}/ directory in the format expected by:
- Evidence API (/api/evidence/)
- Lineage API (/api/lineage/)
- Replay API (/api/replay/)

Screenshot Modes:
- off: No screenshots (default for production)
- on_error: Only capture screenshots when a step fails
- all: Capture screenshots after every browser step
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from local.storage_paths import evidence_path

logger = logging.getLogger(__name__)


class ScreenshotMode(str, Enum):
    """Screenshot capture mode for browser modules."""
    OFF = "off"           # No screenshots
    ON_ERROR = "on_error" # Only on failure (recommended default)
    ALL = "all"           # Every browser step


def get_evidence_base_path() -> Path:
    """Get base path for evidence storage."""
    path = evidence_path()
    logger.info("[EvidenceCollector] Using local evidence path: %s", path)
    return path


class EvidenceCollector:
    """
    Collects and stores execution evidence for debugging.

    Stores evidence in JSONL format at:
        evidence/{execution_id}/evidence.jsonl

    Each line contains:
    {
        "step_id": "...",
        "step_index": 0,
        "module_id": "browser.click",
        "timestamp": "2024-01-01T00:00:00Z",
        "duration_ms": 100,
        "status": "success" | "error",
        "context_before": {...},
        "context_after": {...},
        "error_message": null | "...",
        "params": {...},
        "result": {...}
    }

    Also stores:
        evidence/{execution_id}/{step_id}.png - Screenshots
        evidence/{execution_id}/{step_id}.html - DOM snapshots
    """

    def __init__(
        self,
        execution_id: str,
        base_path: Optional[Path] = None,
        screenshot_mode: ScreenshotMode = ScreenshotMode.ON_ERROR,
    ):
        """
        Initialize evidence collector.

        Args:
            execution_id: Unique execution identifier
            base_path: Base path for evidence storage
            screenshot_mode: When to capture screenshots (off, on_error, all)
        """
        self._execution_id = execution_id
        self._base_path = base_path or get_evidence_base_path()
        self._evidence_dir = self._base_path / execution_id
        self._step_contexts: Dict[str, Dict[str, Any]] = {}
        self._step_start_times: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        self._initialized = False
        self._screenshot_mode = screenshot_mode
        self._browser_context: Optional[Any] = None  # Browser page for screenshots

    @property
    def execution_id(self) -> str:
        """Get execution ID."""
        return self._execution_id

    @property
    def evidence_dir(self) -> Path:
        """Get evidence directory path."""
        return self._evidence_dir

    @property
    def screenshot_mode(self) -> ScreenshotMode:
        """Get screenshot mode."""
        return self._screenshot_mode

    def set_browser_context(self, browser_context: Any) -> None:
        """
        Set browser context for screenshot capture.

        Args:
            browser_context: Browser page or driver object with screenshot capability
        """
        self._browser_context = browser_context
        logger.debug(f"Browser context set for {self._execution_id}")

    def clear_browser_context(self) -> None:
        """Clear browser context (call when browser closes)."""
        self._browser_context = None

    async def initialize(self) -> None:
        """Initialize evidence directory."""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            # Create evidence directory
            self._evidence_dir.mkdir(parents=True, exist_ok=True)

            # Create empty evidence.jsonl
            evidence_file = self._evidence_dir / "evidence.jsonl"
            if not evidence_file.exists():
                evidence_file.touch()

            self._initialized = True
            logger.info(f"[EvidenceCollector] Initialized: {self._evidence_dir} (exists={self._evidence_dir.exists()})")

    async def on_step_start(
        self,
        step_id: str,
        step_index: int,
        module_id: str,
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> None:
        """
        Record step start.

        Args:
            step_id: Step identifier
            step_index: Step index in workflow
            module_id: Module being executed
            params: Step parameters
            context: Execution context before step
        """
        await self.initialize()

        self._step_start_times[step_id] = time.time()
        self._step_contexts[step_id] = {
            "step_id": step_id,
            "step_index": step_index,
            "module_id": module_id,
            "params": self._redact_sensitive(params),
            "context_before": self._redact_sensitive(dict(context)),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def on_step_complete(
        self,
        step_id: str,
        context: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Record step completion.

        Args:
            step_id: Step identifier
            context: Execution context after step
            result: Step result (if successful)
            error: Error message (if failed)
        """
        if step_id not in self._step_contexts:
            logger.warning(f"Step {step_id} not found in context tracking")
            return

        # Calculate duration
        start_time = self._step_start_times.get(step_id)
        duration_ms = int((time.time() - start_time) * 1000) if start_time else 0

        # Build evidence record
        record = self._step_contexts[step_id]
        record["context_after"] = self._redact_sensitive(dict(context))
        record["duration_ms"] = duration_ms
        record["status"] = "error" if error else "success"
        record["error_message"] = error
        record["result"] = self._redact_sensitive(result) if result else None

        # Auto-capture screenshot for browser modules based on mode
        module_id = record.get("module_id", "")
        has_screenshot = False
        if module_id.startswith("browser.") and module_id != "browser.close":
            has_screenshot = await self._auto_capture_screenshot(step_id, error is not None)
        record["has_screenshot"] = has_screenshot

        # Write to JSONL
        await self._append_evidence(record)
        logger.info(f"[EvidenceCollector] Recorded step {step_id} (status={record['status']})")

        # Cleanup
        del self._step_contexts[step_id]
        if step_id in self._step_start_times:
            del self._step_start_times[step_id]

    async def _auto_capture_screenshot(self, step_id: str, is_error: bool) -> bool:
        """
        Auto-capture screenshot based on screenshot_mode.

        Args:
            step_id: Step identifier
            is_error: Whether the step failed

        Returns:
            True if screenshot was captured, False otherwise
        """
        # Check if we should capture
        if self._screenshot_mode == ScreenshotMode.OFF:
            return False
        if self._screenshot_mode == ScreenshotMode.ON_ERROR and not is_error:
            return False

        # Need browser context to capture
        if not self._browser_context:
            logger.debug(f"No browser context for screenshot: {step_id}")
            return False

        try:
            # Try to get screenshot from browser context
            screenshot_data = await self._get_screenshot_from_browser()
            if screenshot_data:
                await self.save_screenshot(step_id, screenshot_data)
                logger.info(f"Auto-captured screenshot for {step_id}")
                return True
        except Exception as e:
            logger.warning(f"Failed to auto-capture screenshot for {step_id}: {e}")

        return False

    async def _get_screenshot_from_browser(self) -> Optional[bytes]:
        """
        Get screenshot from browser context.

        Supports multiple browser driver types.

        Returns:
            Screenshot PNG data or None
        """
        if not self._browser_context:
            return None

        try:
            # Try Playwright-style page.screenshot() with timeout to avoid hangs
            if hasattr(self._browser_context, 'screenshot'):
                return await asyncio.wait_for(
                    self._browser_context.screenshot(type='png'), timeout=5
                )

            # Try getting page from BrowserDriver
            if hasattr(self._browser_context, 'page') and self._browser_context.page:
                page = self._browser_context.page
                if hasattr(page, 'screenshot'):
                    return await page.screenshot(type='png')

            # Try getting page from _page attribute
            if hasattr(self._browser_context, '_page') and self._browser_context._page:
                page = self._browser_context._page
                if hasattr(page, 'screenshot'):
                    return await page.screenshot(type='png')

            logger.debug("Browser context doesn't support screenshot")
            return None

        except Exception as e:
            logger.warning(f"Error getting screenshot from browser: {e}")
            return None

    async def save_screenshot(
        self,
        step_id: str,
        screenshot_data: bytes,
    ) -> Path:
        """
        Save screenshot for a step.

        Args:
            step_id: Step identifier
            screenshot_data: PNG image data

        Returns:
            Path to saved screenshot
        """
        await self.initialize()

        screenshot_path = self._evidence_dir / f"{step_id}.png"

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: screenshot_path.write_bytes(screenshot_data)
        )

        logger.debug(f"Saved screenshot: {screenshot_path}")
        return screenshot_path

    async def save_dom_snapshot(
        self,
        step_id: str,
        dom_html: str,
    ) -> Path:
        """
        Save DOM snapshot for a step.

        Args:
            step_id: Step identifier
            dom_html: HTML content

        Returns:
            Path to saved DOM snapshot
        """
        await self.initialize()

        dom_path = self._evidence_dir / f"{step_id}.html"

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: dom_path.write_text(dom_html, encoding="utf-8")
        )

        logger.debug(f"Saved DOM snapshot: {dom_path}")
        return dom_path

    async def _append_evidence(self, record: Dict[str, Any]) -> None:
        """Append evidence record to JSONL file."""
        evidence_file = self._evidence_dir / "evidence.jsonl"
        line = json.dumps(record, default=str) + "\n"

        def _write():
            with open(evidence_file, "a", encoding="utf-8") as f:
                f.write(line)

        async with self._lock:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _write)

    def _redact_sensitive(self, data: Any) -> Any:
        """Redact sensitive values from data."""
        if data is None:
            return None

        sensitive_keys = {
            "password", "passwd", "pwd", "token", "access_token",
            "refresh_token", "secret", "api_key", "apikey", "auth",
            "authorization", "credential", "credentials", "private_key",
            "private", "access_key", "secret_key", "session", "cookie",
            "jwt", "bearer",
        }

        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                key_lower = key.lower()
                if any(s in key_lower for s in sensitive_keys):
                    result[key] = "[REDACTED]"
                else:
                    result[key] = self._redact_sensitive(value)
            return result

        if isinstance(data, list):
            return [self._redact_sensitive(item) for item in data]

        if isinstance(data, str) and len(data) > 20:
            # Check for token patterns
            secret_patterns = ["eyJ", "sk-", "pk_", "ghp_", "gho_", "Bearer "]
            for pattern in secret_patterns:
                if pattern in data:
                    return "[REDACTED]"

        return data


# Global collector registry
_collectors: Dict[str, EvidenceCollector] = {}
_default_screenshot_mode: ScreenshotMode = ScreenshotMode.ON_ERROR


def set_default_screenshot_mode(mode: ScreenshotMode) -> None:
    """Set default screenshot mode for new collectors."""
    global _default_screenshot_mode
    _default_screenshot_mode = mode
    logger.info(f"Default screenshot mode set to: {mode.value}")


def get_evidence_collector(
    execution_id: str,
    screenshot_mode: Optional[ScreenshotMode] = None,
) -> EvidenceCollector:
    """
    Get or create evidence collector for execution.

    Args:
        execution_id: Execution identifier
        screenshot_mode: Screenshot mode (uses default if not specified)

    Returns:
        EvidenceCollector instance
    """
    if execution_id not in _collectors:
        mode = screenshot_mode or _default_screenshot_mode
        _collectors[execution_id] = EvidenceCollector(
            execution_id,
            screenshot_mode=mode,
        )
        logger.debug(f"Created evidence collector for {execution_id} with mode: {mode.value}")
    return _collectors[execution_id]


def remove_evidence_collector(execution_id: str) -> None:
    """Remove evidence collector from registry."""
    if execution_id in _collectors:
        del _collectors[execution_id]
