"""CE BYOK AI routes without private hosted policy modules."""

try:
    from api.ai.routes import router
except ImportError:
    router = None

__all__ = ["router"]
