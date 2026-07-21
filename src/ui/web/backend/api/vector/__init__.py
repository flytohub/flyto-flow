"""
Vector Store API

Provides endpoints for vector database operations:
- Collection management
- Document insert/search/delete
- Embedding generation
"""
from api.vector.routes import router

__all__ = ["router"]
