"""
WebSocket Breakpoint Notifier

Bridges flyto-core's BreakpointNotifier protocol to the WebSocket manager.
Used when initializing the BreakpointManager in the local/cloud server.
"""

import logging

logger = logging.getLogger(__name__)


class WebSocketBreakpointNotifier:
    """
    Notifier that pushes breakpoint events to frontend via WebSocket.

    Implements the BreakpointNotifier protocol from flyto-core.
    """

    def __init__(self):
        self._ws_manager = None

    def _get_ws_manager(self):
        if self._ws_manager is None:
            from websocket.breakpoint_ws import get_breakpoint_ws_manager
            self._ws_manager = get_breakpoint_ws_manager()
        return self._ws_manager

    async def notify_pending(self, request) -> None:
        """Notify the local frontend of a pending breakpoint."""
        # Serialize breakpoint for frontend
        bp_data = request.to_dict()

        # Strip large screenshot data from WS push — frontend will fetch it
        ctx = bp_data.get("context_snapshot", {})
        if ctx.get("screenshot_base64") and len(ctx["screenshot_base64"]) > 1000:
            # Keep URL if available, remove base64 from push
            if ctx.get("screenshot_url"):
                ctx["screenshot_base64"] = ""
            else:
                # Truncate for push, frontend will get full data via polling
                ctx["_screenshot_truncated"] = True

        # WebSocket push to connected clients
        ws = self._get_ws_manager()
        if ws.client_count > 0:
            await ws.notify_pending(bp_data)
            logger.debug("Pushed breakpoint.pending to %d clients", ws.client_count)

    async def notify_resolved(self, result) -> None:
        """Notify frontend that breakpoint was resolved."""
        ws = self._get_ws_manager()
        if ws.client_count == 0:
            return

        await ws.notify_resolved(
            breakpoint_id=result.breakpoint_id,
            status=result.status.value,
        )
        logger.debug("Pushed breakpoint.resolved to %d clients", ws.client_count)
