"""Small pagination models shared by local CE stores."""

from typing import Any, Callable

from pydantic import BaseModel


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int = 1
    page_size: int = 20
    has_next: bool = False
    has_prev: bool = False


def paginate(items: list, page: int, page_size: int, mapper: Callable | None = None) -> PaginatedResponse:
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]
    if mapper:
        page_items = [mapper(item) for item in page_items]
    return PaginatedResponse(
        items=page_items,
        total=len(items),
        page=page,
        page_size=page_size,
        has_next=end < len(items),
        has_prev=page > 1,
    )


def empty_page(page: int = 1, page_size: int = 20) -> PaginatedResponse:
    return PaginatedResponse(items=[], total=0, page=page, page_size=page_size)
