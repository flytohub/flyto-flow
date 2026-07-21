"""Common DTO Models"""

from typing import Any, Callable, List, Optional
from enum import Enum
from pydantic import BaseModel


class DataSource(str, Enum):
    """Where the data originates from"""
    USER = "user"           # User created
    ORGANIZATION = "org"    # Organization shared
    OFFICIAL = "official"   # Official/marketplace
    IMPORTED = "imported"   # Imported from file


class PaginatedResponse(BaseModel):
    """Paginated list response"""
    items: List[Any]
    total: int
    page: int = 1
    page_size: int = 20
    has_next: bool = False
    has_prev: bool = False


def paginate(
    items: list,
    page: int,
    page_size: int,
    mapper: Optional[Callable] = None,
) -> PaginatedResponse:
    """Slice a list and build a PaginatedResponse."""
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]
    if mapper:
        page_items = [mapper(item) for item in page_items]
    return PaginatedResponse(
        items=page_items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=end < total,
        has_prev=page > 1,
    )


def empty_page(page: int = 1, page_size: int = 20) -> PaginatedResponse:
    """Return an empty PaginatedResponse (for error fallbacks)."""
    return PaginatedResponse(items=[], total=0, page=page, page_size=page_size)
