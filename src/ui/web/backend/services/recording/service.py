"""
Recording Service

Browser recording service using Playwright.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from services.recording.models import ActionType, RecordedAction, RecordingSession
from services.recording.hooks import RECORDING_SCRIPT

logger = logging.getLogger(__name__)


class RecordingService:
    """
    Service for recording browser interactions.

    Usage:
        service = RecordingService()

        # Start recording
        session = await service.start_recording(
            url="https://example.com",
            options={"capture_screenshots": True}
        )

        # Actions are recorded automatically via Playwright hooks

        # Stop and get results
        workflow = await service.stop_recording(session.session_id)
    """

    def __init__(self):
        """Initialize recording service."""
        self._sessions: Dict[str, RecordingSession] = {}
        self._browsers: Dict[str, Any] = {}
        self._pages: Dict[str, Any] = {}
        self._action_callbacks: Dict[str, Callable] = {}
        self._playwright = None

    async def _ensure_playwright(self):
        """Ensure Playwright is initialized."""
        if self._playwright is None:
            try:
                from playwright.async_api import async_playwright
                self._playwright = await async_playwright().start()
            except ImportError:
                raise ImportError(
                    "Playwright not installed. Run: pip install playwright && playwright install"
                )

    async def start_recording(
        self,
        url: str,
        session_id: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        on_action: Optional[Callable[[RecordedAction], None]] = None,
    ) -> RecordingSession:
        """
        Start a new recording session.

        Args:
            url: Target URL to record
            session_id: Custom session ID
            options: Recording options
            on_action: Callback for each recorded action

        Returns:
            RecordingSession instance
        """
        await self._ensure_playwright()

        session_id = session_id or f"rec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        options = options or {}

        # Create session
        session = RecordingSession(
            session_id=session_id,
            url=url,
            options=options,
        )
        self._sessions[session_id] = session

        # Store callback
        if on_action:
            self._action_callbacks[session_id] = on_action

        # Launch browser
        browser = await self._playwright.chromium.launch(
            headless=False,
            args=["--start-maximized"],
        )
        self._browsers[session_id] = browser

        # Create context with recording
        context = await browser.new_context(
            viewport=None,
            record_video_dir=None,
        )

        # Create page
        page = await context.new_page()
        self._pages[session_id] = page

        # Set up event listeners
        await self._setup_recording_hooks(session_id, page, options)

        # Navigate to URL
        await page.goto(url)

        # Record initial navigation
        self._record_action(session_id, RecordedAction(
            type=ActionType.NAVIGATE,
            value=url,
        ))

        logger.info(f"Started recording session {session_id} for {url}")
        return session

    async def _setup_recording_hooks(
        self,
        session_id: str,
        page: Any,
        options: Dict[str, Any],
    ) -> None:
        """Set up Playwright hooks for recording."""
        capture_screenshots = options.get("capture_screenshots", False)

        # Inject recording script
        await page.add_init_script(RECORDING_SCRIPT)

        # Set up page event handlers
        page.on("framenavigated", lambda frame: self._on_navigation(session_id, frame))

        # Poll for actions
        async def poll_actions():
            while session_id in self._sessions and self._sessions[session_id].status == "active":
                try:
                    action_data = await page.evaluate(
                        "() => { const a = window.__flytoLastAction; window.__flytoLastAction = null; return a; }"
                    )
                    if action_data:
                        action = RecordedAction(
                            type=ActionType(action_data["type"]),
                            selector=action_data.get("selector"),
                            value=action_data.get("value"),
                            alternatives=action_data.get("alternatives", []),
                        )

                        # Capture screenshot if enabled
                        if capture_screenshots:
                            try:
                                screenshot = await page.screenshot(type="png")
                                import base64
                                action.screenshot = base64.b64encode(screenshot).decode()
                            except Exception:
                                pass

                        self._record_action(session_id, action)
                except Exception as e:
                    if "Target closed" in str(e):
                        break
                    logger.debug(f"Poll error: {e}")

                await asyncio.sleep(0.1)

        asyncio.create_task(poll_actions())

    def _on_navigation(self, session_id: str, frame: Any) -> None:
        """Handle navigation events."""
        if frame.parent_frame is None:
            url = frame.url
            if url and not url.startswith("about:"):
                self._record_action(session_id, RecordedAction(
                    type=ActionType.NAVIGATE,
                    value=url,
                ))

    def _record_action(self, session_id: str, action: RecordedAction) -> None:
        """Record an action to the session."""
        session = self._sessions.get(session_id)
        if not session or session.status != "active":
            return

        # Deduplicate consecutive fill actions
        if (action.type == ActionType.FILL and
            session.actions and
            session.actions[-1].type == ActionType.FILL and
            session.actions[-1].selector == action.selector):
            session.actions[-1].value = action.value
            return

        session.actions.append(action)

        # Notify callback
        callback = self._action_callbacks.get(session_id)
        if callback:
            try:
                callback(action)
            except Exception as e:
                logger.error(f"Action callback error: {e}")

        logger.debug(f"Recorded action: {action.type.value} on {action.selector}")

    async def stop_recording(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Stop recording and return workflow."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        session.status = "completed"
        session.ended_at = datetime.now(timezone.utc).isoformat()

        # Close browser
        browser = self._browsers.pop(session_id, None)
        if browser:
            await browser.close()

        self._pages.pop(session_id, None)
        self._action_callbacks.pop(session_id, None)

        logger.info(f"Stopped recording session {session_id}: {len(session.actions)} actions")

        return session.to_workflow()

    async def pause_recording(self, session_id: str) -> bool:
        """Pause recording."""
        session = self._sessions.get(session_id)
        if session and session.status == "active":
            session.status = "paused"
            return True
        return False

    async def resume_recording(self, session_id: str) -> bool:
        """Resume recording."""
        session = self._sessions.get(session_id)
        if session and session.status == "paused":
            session.status = "active"
            return True
        return False

    def get_session(self, session_id: str) -> Optional[RecordingSession]:
        """Get session by ID."""
        return self._sessions.get(session_id)

    def get_actions(self, session_id: str) -> List[RecordedAction]:
        """Get recorded actions for a session."""
        session = self._sessions.get(session_id)
        return session.actions if session else []

    async def test_selector(
        self,
        session_id: str,
        selector: str,
    ) -> Dict[str, Any]:
        """Test if a selector finds elements."""
        page = self._pages.get(session_id)
        if not page:
            return {"success": False, "error": "No active page"}

        try:
            elements = await page.query_selector_all(selector)
            return {
                "success": True,
                "count": len(elements),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def cleanup(self) -> None:
        """Clean up all resources."""
        for session_id in list(self._sessions.keys()):
            await self.stop_recording(session_id)

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
