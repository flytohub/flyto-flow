"""
System Package Manager API

Manage system-level packages: flyto-core, flyto-ai, Playwright, Chromium, pyngrok, etc.
Local-only routes — no auth required (runs on user's machine).

Split into sub-modules for maintainability.
"""

from .routes import router

__all__ = ["router"]
