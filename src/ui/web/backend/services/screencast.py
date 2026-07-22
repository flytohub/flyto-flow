"""Local CDP browser screencast and input bridge."""

from __future__ import annotations

import asyncio
import base64
import logging
import time
from typing import Any, Callable, Coroutine, Dict, Optional

from fastapi import WebSocket


logger = logging.getLogger(__name__)
_FRAME_INTERVAL_MS = 40


class ScreencastSession:
    """One Playwright page streamed to the same-origin Flyto2 Flow UI."""

    def __init__(self, page: Any, execution_id: str):
        self._page = page
        self._execution_id = execution_id
        self._cdp_session: Optional[Any] = None
        self._active = False
        self._latest_metadata: Optional[Dict] = None
        self._last_frame_time = 0.0
        self._cached_frame: Optional[bytes] = None
        self.on_frame_callback: Optional[Callable[[bytes, Dict], Coroutine]] = None

    @property
    def active(self) -> bool:
        return self._active

    @property
    def viewport(self) -> Dict[str, int]:
        if self._latest_metadata:
            return {
                "width": self._latest_metadata.get("deviceWidth", 1280),
                "height": self._latest_metadata.get("deviceHeight", 720),
            }
        viewport = self._page.viewport_size
        return viewport or {"width": 1280, "height": 720}

    async def start(self, quality: int = 40, max_width: int = 1280, max_height: int = 720):
        if self._active:
            return
        try:
            self._cdp_session = await self._page.context.new_cdp_session(self._page)
            self._cdp_session.on("Page.screencastFrame", self._on_frame)
            await self._cdp_session.send(
                "Page.startScreencast",
                {
                    "format": "jpeg",
                    "quality": quality,
                    "maxWidth": max_width,
                    "maxHeight": max_height,
                    "everyNthFrame": 1,
                },
            )
            self._active = True
            logger.info("Screencast started for execution %s", self._execution_id)
        except Exception:
            await self._cleanup()
            raise

    def _on_frame(self, event: Dict):
        try:
            session_id = event.get("sessionId", 0)
            if self._cdp_session:
                asyncio.ensure_future(
                    self._cdp_session.send(
                        "Page.screencastFrameAck", {"sessionId": session_id}
                    )
                )
            self._latest_metadata = event.get("metadata", {})
            now = time.monotonic() * 1000
            if now - self._last_frame_time < _FRAME_INTERVAL_MS:
                return
            self._last_frame_time = now
            encoded = event.get("data", "")
            if encoded:
                frame = base64.b64decode(encoded)
                self._cached_frame = frame
                if self.on_frame_callback:
                    asyncio.ensure_future(
                        self.on_frame_callback(frame, self._latest_metadata)
                    )
        except Exception as exc:
            logger.debug("Frame handling error: %s", exc)

    async def dispatch_mouse(
        self,
        event_type: str,
        x: float,
        y: float,
        button: str = "left",
        click_count: int = 1,
    ):
        if not self._cdp_session or not self._active:
            return
        params: Dict[str, Any] = {
            "type": event_type,
            "x": x,
            "y": y,
            "button": button,
        }
        if event_type in {"mousePressed", "mouseReleased"}:
            params["clickCount"] = click_count
        try:
            await self._cdp_session.send("Input.dispatchMouseEvent", params)
        except Exception as exc:
            logger.debug("Mouse dispatch error: %s", exc)

    async def dispatch_scroll(
        self,
        x: float,
        y: float,
        delta_x: float,
        delta_y: float,
    ):
        if not self._cdp_session or not self._active:
            return
        try:
            await self._cdp_session.send(
                "Input.dispatchMouseEvent",
                {
                    "type": "mouseWheel",
                    "x": x,
                    "y": y,
                    "deltaX": delta_x,
                    "deltaY": delta_y,
                },
            )
        except Exception as exc:
            logger.debug("Scroll dispatch error: %s", exc)

    async def dispatch_key(
        self,
        event_type: str,
        key: str = "",
        code: str = "",
        modifiers: int = 0,
        text: str = "",
    ):
        if not self._cdp_session or not self._active:
            return
        params: Dict[str, Any] = {"type": event_type, "modifiers": modifiers}
        if key:
            params["key"] = key
        if code:
            params["code"] = code
        if text and event_type == "keyDown":
            params["text"] = text
        try:
            await self._cdp_session.send("Input.dispatchKeyEvent", params)
        except Exception as exc:
            logger.debug("Key dispatch error: %s", exc)

    async def dispatch_type(self, text: str):
        if not self._cdp_session or not self._active:
            return
        try:
            await self._cdp_session.send("Input.insertText", {"text": text})
        except Exception as exc:
            logger.debug("Text insertion error: %s", exc)

    async def stop(self):
        if not self._active:
            return
        self._active = False
        await self._cleanup()
        logger.info("Screencast stopped for execution %s", self._execution_id)

    async def _cleanup(self):
        if not self._cdp_session:
            return
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
    """Manage one local browser stream and its same-origin UI connection."""

    def __init__(self):
        self._sessions: Dict[str, ScreencastSession] = {}
        self._connections: Dict[str, list[WebSocket]] = {}
        self._lock = asyncio.Lock()

    def get_session(self, execution_id: str) -> Optional[ScreencastSession]:
        return self._sessions.get(execution_id)

    async def start_screencast(self, execution_id: str, page: Any) -> ScreencastSession:
        if execution_id in self._sessions:
            await self.stop_screencast(execution_id)
        session = ScreencastSession(page, execution_id)
        session.on_frame_callback = lambda data, meta: self._broadcast_frame(
            execution_id, data, meta
        )
        self._sessions[execution_id] = session
        self._connections.setdefault(execution_id, [])
        await session.start()
        await self._broadcast_json(
            execution_id,
            {"type": "screencast.started", "viewport": session.viewport},
        )
        return session

    async def stop_screencast(self, execution_id: str):
        session = self._sessions.pop(execution_id, None)
        if session:
            await session.stop()
        await self._broadcast_json(execution_id, {"type": "screencast.stopped"})

    async def close_browser(self, execution_id: str):
        session = self._sessions.get(execution_id)
        page = session._page if session else None
        await self.stop_screencast(execution_id)
        if page:
            try:
                await page.close()
            except Exception as exc:
                logger.debug("Error closing browser page: %s", exc)
        try:
            from services.runtime.execution import get_execution_manager

            info = get_execution_manager().get_info(execution_id)
            if info:
                info.metadata["has_browser"] = False
        except Exception as exc:
            logger.debug("Error updating execution metadata: %s", exc)

    async def add_connection(self, execution_id: str, websocket: WebSocket):
        async with self._lock:
            self._connections.setdefault(execution_id, []).append(websocket)
        session = self._sessions.get(execution_id)
        if session and session.active:
            await self._send_json(
                websocket,
                {"type": "screencast.started", "viewport": session.viewport},
            )
            if session._cached_frame:
                try:
                    await websocket.send_bytes(session._cached_frame)
                except Exception:
                    pass

    async def remove_connection(self, execution_id: str, websocket: WebSocket):
        async with self._lock:
            remaining = [
                item for item in self._connections.get(execution_id, [])
                if item is not websocket
            ]
            if remaining:
                self._connections[execution_id] = remaining
            else:
                self._connections.pop(execution_id, None)

    async def handle_input(self, execution_id: str, message: Dict):
        session = self._sessions.get(execution_id)
        if not session or not session.active:
            return
        message_type = message.get("type", "")
        if message_type == "mouse.click":
            x, y = message.get("x", 0), message.get("y", 0)
            button = message.get("button", "left")
            await session.dispatch_mouse("mousePressed", x, y, button)
            await session.dispatch_mouse("mouseReleased", x, y, button)
        elif message_type == "mouse.move":
            await session.dispatch_mouse("mouseMoved", message.get("x", 0), message.get("y", 0))
        elif message_type == "mouse.down":
            await session.dispatch_mouse(
                "mousePressed",
                message.get("x", 0),
                message.get("y", 0),
                message.get("button", "left"),
            )
        elif message_type == "mouse.up":
            await session.dispatch_mouse(
                "mouseReleased",
                message.get("x", 0),
                message.get("y", 0),
                message.get("button", "left"),
            )
        elif message_type == "mouse.wheel":
            await session.dispatch_scroll(
                message.get("x", 0),
                message.get("y", 0),
                message.get("deltaX", 0),
                message.get("deltaY", 0),
            )
        elif message_type == "key.down":
            await session.dispatch_key(
                "keyDown",
                key=message.get("key", ""),
                code=message.get("code", ""),
                modifiers=message.get("modifiers", 0),
                text=message.get("text", ""),
            )
        elif message_type == "key.up":
            await session.dispatch_key(
                "keyUp",
                key=message.get("key", ""),
                code=message.get("code", ""),
                modifiers=message.get("modifiers", 0),
            )
        elif message_type == "key.type":
            await session.dispatch_type(message.get("text", ""))

    def get_status(self, execution_id: str) -> Dict[str, Any]:
        session = self._sessions.get(execution_id)
        return {
            "active": session.active if session else False,
            "connection_count": len(self._connections.get(execution_id, [])),
            "viewport": session.viewport if session else None,
        }

    def get_cached_frame(self, execution_id: str) -> Optional[bytes]:
        session = self._sessions.get(execution_id)
        return session._cached_frame if session else None

    async def _broadcast_frame(self, execution_id: str, data: bytes, metadata: Dict):
        del metadata
        connections = list(self._connections.get(execution_id, []))
        if not connections:
            return

        async def send(websocket: WebSocket):
            try:
                await websocket.send_bytes(data)
                return None
            except Exception:
                return websocket

        results = await asyncio.gather(*(send(item) for item in connections))
        for dead in (item for item in results if item is not None):
            await self.remove_connection(execution_id, dead)

    async def _broadcast_json(self, execution_id: str, message: Dict):
        for websocket in list(self._connections.get(execution_id, [])):
            try:
                await websocket.send_json(message)
            except Exception:
                await self.remove_connection(execution_id, websocket)

    @staticmethod
    async def _send_json(websocket: WebSocket, message: Dict):
        try:
            await websocket.send_json(message)
        except Exception:
            pass


_screencast_manager: Optional[ScreencastManager] = None


def get_screencast_manager() -> ScreencastManager:
    global _screencast_manager
    if _screencast_manager is None:
        _screencast_manager = ScreencastManager()
    return _screencast_manager
