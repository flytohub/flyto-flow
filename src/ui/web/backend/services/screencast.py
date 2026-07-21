"""
Browser Screencast Service

CDP-based screencast for real-time browser viewing and collaborative control.
Uses Page.startScreencast/stopScreencast for JPEG frame streaming.
"""

import asyncio
import base64
import logging
import time
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple

from fastapi import WebSocket

logger = logging.getLogger(__name__)

# Frame rate limit (server-side, on top of CDP everyNthFrame)
_FRAME_INTERVAL_MS = 40  # ~25 fps cap — balanced for local + remote


class ScreencastSession:
    """
    Manages a CDP screencast session for a single Playwright page.

    Streams JPEG frames via Page.startScreencast and dispatches
    user input events (mouse, keyboard, scroll) via CDP Input domain.
    """

    def __init__(self, page: Any, execution_id: str):
        """Initialize screencast session for a Playwright page."""
        self._page = page
        self._execution_id = execution_id
        self._cdp_session: Optional[Any] = None
        self._active = False
        self._latest_metadata: Optional[Dict] = None
        self._last_frame_time: float = 0  # server-side frame rate limit
        self._cached_frame: Optional[bytes] = None  # latest frame for instant viewer bootstrap
        self.on_frame_callback: Optional[Callable[[bytes, Dict], Coroutine]] = None

    @property
    def active(self) -> bool:
        """Whether the screencast is currently streaming."""
        return self._active

    @property
    def viewport(self) -> Dict[str, int]:
        """Return current viewport dimensions from metadata or page."""
        if self._latest_metadata:
            return {
                "width": self._latest_metadata.get("deviceWidth", 1280),
                "height": self._latest_metadata.get("deviceHeight", 720),
            }
        vp = self._page.viewport_size
        if vp:
            return {"width": vp["width"], "height": vp["height"]}
        return {"width": 1280, "height": 720}

    async def start(self, quality: int = 40, max_width: int = 1280, max_height: int = 720):
        """Start CDP screencast."""
        if self._active:
            return

        try:
            self._cdp_session = await self._page.context.new_cdp_session(self._page)
            self._cdp_session.on("Page.screencastFrame", self._on_frame)

            await self._cdp_session.send("Page.startScreencast", {
                "format": "jpeg",
                "quality": quality,
                "maxWidth": max_width,
                "maxHeight": max_height,
                "everyNthFrame": 1,
            })
            self._active = True
            logger.info(f"Screencast started for execution {self._execution_id}")
        except Exception as e:
            logger.error(f"Failed to start screencast for {self._execution_id}: {e}")
            await self._cleanup()
            raise

    def _on_frame(self, event: Dict):
        """Handle incoming screencast frame from CDP.

        NOTE: Must be synchronous — Playwright CDPSession.on() does not
        await async handlers.  Async work is scheduled via ensure_future.
        """
        try:
            session_id = event.get("sessionId", 0)
            # Ack immediately to keep frames flowing
            if self._cdp_session:
                asyncio.ensure_future(
                    self._cdp_session.send("Page.screencastFrameAck", {
                        "sessionId": session_id,
                    })
                )

            self._latest_metadata = event.get("metadata", {})

            # Server-side frame rate cap
            now = time.monotonic() * 1000
            if now - self._last_frame_time < _FRAME_INTERVAL_MS:
                return
            self._last_frame_time = now

            data_b64 = event.get("data", "")
            if data_b64:
                frame_bytes = base64.b64decode(data_b64)
                self._cached_frame = frame_bytes  # cache for instant viewer bootstrap
                if self.on_frame_callback:
                    asyncio.ensure_future(
                        self.on_frame_callback(frame_bytes, self._latest_metadata)
                    )
        except Exception as e:
            logger.debug(f"Frame handling error: {e}")

    async def dispatch_mouse(self, event_type: str, x: float, y: float, button: str = "left", click_count: int = 1):
        """Dispatch mouse event via CDP Input domain."""
        if not self._cdp_session or not self._active:
            return

        try:
            params: Dict[str, Any] = {
                "type": event_type,
                "x": x,
                "y": y,
                "button": button,
            }
            if event_type == "mousePressed" or event_type == "mouseReleased":
                params["clickCount"] = click_count
            await self._cdp_session.send("Input.dispatchMouseEvent", params)
        except Exception as e:
            logger.debug(f"Mouse dispatch error: {e}")

    async def dispatch_scroll(self, x: float, y: float, delta_x: float, delta_y: float):
        """Dispatch mouse wheel event via CDP."""
        if not self._cdp_session or not self._active:
            return

        try:
            await self._cdp_session.send("Input.dispatchMouseEvent", {
                "type": "mouseWheel",
                "x": x,
                "y": y,
                "deltaX": delta_x,
                "deltaY": delta_y,
            })
        except Exception as e:
            logger.debug(f"Scroll dispatch error: {e}")

    async def dispatch_key(self, event_type: str, key: str = "", code: str = "", modifiers: int = 0, text: str = ""):
        """Dispatch keyboard event via CDP Input domain."""
        if not self._cdp_session or not self._active:
            return

        try:
            params: Dict[str, Any] = {
                "type": event_type,
                "modifiers": modifiers,
            }
            if key:
                params["key"] = key
            if code:
                params["code"] = code
            if text and event_type == "keyDown":
                params["text"] = text
            await self._cdp_session.send("Input.dispatchKeyEvent", params)
        except Exception as e:
            logger.debug(f"Key dispatch error: {e}")

    async def dispatch_type(self, text: str):
        """Insert text directly (efficient for typing, avoids per-character key events)."""
        if not self._cdp_session or not self._active:
            return

        try:
            await self._cdp_session.send("Input.insertText", {"text": text})
        except Exception as e:
            logger.debug(f"InsertText error: {e}")

    async def stop(self):
        """Stop screencast and clean up CDP session."""
        if not self._active:
            return
        self._active = False
        await self._cleanup()
        logger.info(f"Screencast stopped for execution {self._execution_id}")

    async def _cleanup(self):
        if self._cdp_session:
            try:
                await self._cdp_session.send("Page.stopScreencast")
            except Exception:
                pass
            try:
                await self._cdp_session.detach()
            except Exception:
                pass
            self._cdp_session = None


class ScreencastManager:
    """
    Manages all active screencast sessions, viewers, and driver seat control.

    - One ScreencastSession per execution_id
    - Multiple viewers (WebSocket connections) per execution_id
    - Driver seat: only one user can send input at a time
    """

    def __init__(self):
        """Initialize the screencast manager with empty session/viewer maps."""
        self._sessions: Dict[str, ScreencastSession] = {}
        self._viewers: Dict[str, List[Tuple[WebSocket, str]]] = {}  # (ws, user_id)
        self._driver_seat: Dict[str, Optional[str]] = {}
        self._lock = asyncio.Lock()  # protects _viewers and _driver_seat mutations

    def get_session(self, execution_id: str) -> Optional[ScreencastSession]:
        """Get the screencast session for an execution, if any."""
        return self._sessions.get(execution_id)

    async def start_screencast(self, execution_id: str, page: Any) -> ScreencastSession:
        """Start a screencast session for an execution."""
        # Stop existing session if any
        if execution_id in self._sessions:
            await self.stop_screencast(execution_id)

        session = ScreencastSession(page, execution_id)
        session.on_frame_callback = lambda data, meta: self._broadcast_frame(execution_id, data, meta)
        self._sessions[execution_id] = session
        self._viewers.setdefault(execution_id, [])
        self._driver_seat.setdefault(execution_id, None)

        await session.start()

        # Notify existing viewers that screencast started
        await self._broadcast_json(execution_id, {
            "type": "screencast.started",
            "viewport": session.viewport,
        })

        return session

    async def stop_screencast(self, execution_id: str):
        """Stop screencast and notify all viewers."""
        session = self._sessions.pop(execution_id, None)
        if session:
            await session.stop()

        # Notify viewers
        await self._broadcast_json(execution_id, {"type": "screencast.stopped"})

        # Clean up
        self._driver_seat.pop(execution_id, None)

    async def close_browser(self, execution_id: str):
        """Close the actual browser (stop screencast + close Playwright page).

        Called when a user clicks the "close browser" button in the UI.
        """
        session = self._sessions.get(execution_id)
        page = session._page if session else None

        # Stop screencast first
        await self.stop_screencast(execution_id)

        # Close the Playwright page
        if page:
            try:
                await page.close()
                logger.info(f"Browser page closed for execution {execution_id}")
            except Exception as e:
                logger.debug(f"Error closing browser page: {e}")

        # Update execution metadata
        try:
            from services.runtime.execution import get_execution_manager
            manager = get_execution_manager()
            info = manager.get_info(execution_id)
            if info:
                info.metadata["has_browser"] = False
        except Exception as e:
            logger.debug(f"Error updating execution metadata: {e}")

    async def add_viewer(self, execution_id: str, ws: WebSocket, user_id: str):
        """Add a viewer WebSocket connection."""
        async with self._lock:
            viewers = self._viewers.setdefault(execution_id, [])
            viewers.append((ws, user_id))

            # First viewer gets driver seat if none assigned
            if self._driver_seat.get(execution_id) is None:
                self._driver_seat[execution_id] = user_id

        # Send current state to new viewer (outside lock — no mutation)
        session = self._sessions.get(execution_id)
        if session and session.active:
            await self._send_json(ws, {
                "type": "screencast.started",
                "viewport": session.viewport,
            })
            # Send cached frame immediately so viewer sees something instantly
            if session._cached_frame:
                try:
                    await ws.send_bytes(session._cached_frame)
                except Exception:
                    pass

        # Broadcast control state to all
        await self._broadcast_control_state(execution_id)
        await self._broadcast_viewer_count(execution_id)

    async def remove_viewer(self, execution_id: str, ws: WebSocket):
        """Remove a viewer WebSocket connection."""
        async with self._lock:
            viewers = self._viewers.get(execution_id, [])
            removed_user_id = None
            self._viewers[execution_id] = [
                (w, uid) for w, uid in viewers if w is not ws
            ]
            for w, uid in viewers:
                if w is ws:
                    removed_user_id = uid
                    break

            # If driver left, transfer to next viewer
            if removed_user_id and self._driver_seat.get(execution_id) == removed_user_id:
                remaining = self._viewers.get(execution_id, [])
                if remaining:
                    self._driver_seat[execution_id] = remaining[0][1]
                else:
                    self._driver_seat[execution_id] = None
                    removed_user_id = None  # skip grant broadcast

        # Broadcasts outside lock
        if removed_user_id:
            remaining = self._viewers.get(execution_id, [])
            if remaining:
                await self._broadcast_json(execution_id, {
                    "type": "control.granted",
                    "user_id": self._driver_seat.get(execution_id),
                })

        await self._broadcast_control_state(execution_id)
        await self._broadcast_viewer_count(execution_id)

        # Clean up empty viewer lists
        async with self._lock:
            if not self._viewers.get(execution_id):
                self._viewers.pop(execution_id, None)

    async def handle_input(self, execution_id: str, user_id: str, msg: Dict):
        """Handle an input message from a viewer. Only the driver can send input."""
        if self._driver_seat.get(execution_id) != user_id:
            return  # Not the driver, ignore

        session = self._sessions.get(execution_id)
        if not session or not session.active:
            return

        msg_type = msg.get("type", "")

        if msg_type == "mouse.click":
            x, y = msg.get("x", 0), msg.get("y", 0)
            button = msg.get("button", "left")
            await session.dispatch_mouse("mousePressed", x, y, button)
            await session.dispatch_mouse("mouseReleased", x, y, button)

        elif msg_type == "mouse.move":
            await session.dispatch_mouse("mouseMoved", msg.get("x", 0), msg.get("y", 0))

        elif msg_type == "mouse.down":
            await session.dispatch_mouse("mousePressed", msg.get("x", 0), msg.get("y", 0), msg.get("button", "left"))

        elif msg_type == "mouse.up":
            await session.dispatch_mouse("mouseReleased", msg.get("x", 0), msg.get("y", 0), msg.get("button", "left"))

        elif msg_type == "mouse.wheel":
            await session.dispatch_scroll(
                msg.get("x", 0), msg.get("y", 0),
                msg.get("deltaX", 0), msg.get("deltaY", 0),
            )

        elif msg_type == "key.down":
            await session.dispatch_key(
                "keyDown",
                key=msg.get("key", ""),
                code=msg.get("code", ""),
                modifiers=msg.get("modifiers", 0),
                text=msg.get("text", ""),
            )

        elif msg_type == "key.up":
            await session.dispatch_key(
                "keyUp",
                key=msg.get("key", ""),
                code=msg.get("code", ""),
                modifiers=msg.get("modifiers", 0),
            )

        elif msg_type == "key.type":
            await session.dispatch_type(msg.get("text", ""))

    async def request_control(self, execution_id: str, user_id: str, user_name: str = ""):
        """A viewer requests driver seat control."""
        current_driver = self._driver_seat.get(execution_id)
        if current_driver == user_id:
            return  # Already the driver

        # Notify current driver about the request
        await self._broadcast_json(execution_id, {
            "type": "control.requested",
            "user_id": user_id,
            "user_name": user_name,
        })

    async def transfer_control(self, execution_id: str, to_user_id: str):
        """Transfer driver seat to another user."""
        async with self._lock:
            viewers = self._viewers.get(execution_id, [])
            user_ids = [uid for _, uid in viewers]
            if to_user_id not in user_ids:
                return

            old_driver = self._driver_seat.get(execution_id)
            self._driver_seat[execution_id] = to_user_id

        # Broadcasts outside lock
        if old_driver:
            await self._broadcast_json(execution_id, {
                "type": "control.released",
                "user_id": old_driver,
            })
        await self._broadcast_json(execution_id, {
            "type": "control.granted",
            "user_id": to_user_id,
        })
        await self._broadcast_control_state(execution_id)

    async def release_control(self, execution_id: str, user_id: str):
        """Release driver seat (goes to first viewer or None)."""
        async with self._lock:
            if self._driver_seat.get(execution_id) != user_id:
                return

            viewers = self._viewers.get(execution_id, [])
            other_viewers = [(w, uid) for w, uid in viewers if uid != user_id]
            if other_viewers:
                new_driver = other_viewers[0][1]
                self._driver_seat[execution_id] = new_driver
            else:
                new_driver = None
                self._driver_seat[execution_id] = None

        # Broadcasts outside lock
        await self._broadcast_json(execution_id, {
            "type": "control.released",
            "user_id": user_id,
        })
        if new_driver:
            await self._broadcast_json(execution_id, {
                "type": "control.granted",
                "user_id": new_driver,
            })
        await self._broadcast_control_state(execution_id)

    def get_status(self, execution_id: str) -> Dict[str, Any]:
        """Get screencast status for REST endpoint."""
        session = self._sessions.get(execution_id)
        viewers = self._viewers.get(execution_id, [])
        return {
            "active": session.active if session else False,
            "viewer_count": len(viewers),
            "driver_user_id": self._driver_seat.get(execution_id),
            "viewport": session.viewport if session else None,
        }

    def get_cached_frame(self, execution_id: str) -> Optional[bytes]:
        """Get the latest cached JPEG frame for an execution (for remote screenshot relay)."""
        session = self._sessions.get(execution_id)
        if session and session._cached_frame:
            return session._cached_frame
        return None

    # --- Internal broadcasting ---

    async def _broadcast_frame(self, execution_id: str, data: bytes, metadata: Dict):
        """Broadcast a binary JPEG frame to all viewers concurrently."""
        viewers = self._viewers.get(execution_id, [])
        if not viewers:
            return

        async def _send_one(ws, uid):
            try:
                await ws.send_bytes(data)
                return None
            except Exception:
                return (ws, uid)

        results = await asyncio.gather(
            *(_send_one(ws, uid) for ws, uid in viewers),
            return_exceptions=True,
        )

        dead = [r for r in results if r is not None and not isinstance(r, BaseException)]
        if dead:
            async with self._lock:
                for ws, uid in dead:
                    self._viewers[execution_id] = [
                        (w, u) for w, u in self._viewers.get(execution_id, []) if w is not ws
                    ]
            await self._broadcast_viewer_count(execution_id)

    async def _broadcast_json(self, execution_id: str, msg: Dict):
        """Broadcast a JSON message to all viewers."""
        viewers = self._viewers.get(execution_id, [])
        dead = []
        for ws, uid in viewers:
            try:
                await ws.send_json(msg)
            except Exception:
                dead.append((ws, uid))

        for ws, uid in dead:
            self._viewers[execution_id] = [
                (w, u) for w, u in self._viewers.get(execution_id, []) if w is not ws
            ]

    async def _send_json(self, ws: WebSocket, msg: Dict):
        """Send JSON to a single WebSocket."""
        try:
            await ws.send_json(msg)
        except Exception:
            pass

    async def _broadcast_control_state(self, execution_id: str):
        """Broadcast current control state to all viewers."""
        viewers = self._viewers.get(execution_id, [])
        await self._broadcast_json(execution_id, {
            "type": "control.state",
            "driver_user_id": self._driver_seat.get(execution_id),
            "viewers": [{"user_id": uid} for _, uid in viewers],
        })

    async def _broadcast_viewer_count(self, execution_id: str):
        """Broadcast viewer count."""
        viewers = self._viewers.get(execution_id, [])
        await self._broadcast_json(execution_id, {
            "type": "viewer.count",
            "count": len(viewers),
        })


# Global singleton
_screencast_manager: Optional[ScreencastManager] = None


def get_screencast_manager() -> ScreencastManager:
    """Get or create the global ScreencastManager."""
    global _screencast_manager
    if _screencast_manager is None:
        _screencast_manager = ScreencastManager()
    return _screencast_manager
