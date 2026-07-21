"""
Browser Screencast API

WebSocket endpoint for real-time browser viewing and REST status endpoint.
"""

from api.browser.routes import router, handle_browser_websocket

__all__ = ["router", "handle_browser_websocket"]
