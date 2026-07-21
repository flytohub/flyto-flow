"""
Local Runner sub-modules.

Split from main_local.py for maintainability:
- cloud_proxy: Cloud API proxy client and catch-all route
- device_manager: Device auto-registration and token capture
- job_executor: Job polling, claiming, and execution
- browser_bootstrap: Node.js and Playwright Chromium download
- wake_management: Wake daemon enable/disable/status routes + OS service helpers
- oauth_routes: Desktop OAuth flow (system browser + cloud proxy)
- websocket_routes: All WebSocket endpoint handlers
- collaboration_local: Local collaboration REST endpoints
- static_files: SPA static file mounting
"""
