"""
Quality API Routes

Provides endpoints for:
- /api/quality/catalog - Public scrubbed module catalog
- /api/quality/lint - Lint validation reports
- /api/quality/i18n/coverage - Translation coverage metrics
"""

from api.quality.routes import router

__all__ = ["router"]
