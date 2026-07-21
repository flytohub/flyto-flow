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
        """Notify frontend of new pending breakpoint via WebSocket + FCM push."""
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

        # FCM push to mobile app (even if not connected to WebSocket)
        await self._send_fcm_push(request, bp_data)

    async def _send_fcm_push(self, request, bp_data) -> None:
        """Send FCM push notification for breakpoint. Best-effort, never raises."""
        try:
            # Resolve user_id from execution metadata
            user_id = self._resolve_user_id(request)
            if not user_id:
                return

            from services.device.notification import notify_breakpoint_pending

            ctx = bp_data.get("context_snapshot", {})
            await notify_breakpoint_pending(
                user_id=user_id,
                breakpoint_id=request.breakpoint_id,
                execution_id=request.execution_id,
                title=request.title,
                is_interact=bool(ctx.get("_interact")),
            )
        except Exception as e:
            logger.debug("FCM breakpoint push skipped: %s", e)

    @staticmethod
    def _resolve_user_id(request) -> str | None:
        """Try to resolve user_id from breakpoint request metadata."""
        # Check required_approvers first (most common)
        if request.required_approvers:
            return request.required_approvers[0]
        # Check metadata
        meta = getattr(request, "metadata", {}) or {}
        return meta.get("user_id") or meta.get("owner_id")

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
