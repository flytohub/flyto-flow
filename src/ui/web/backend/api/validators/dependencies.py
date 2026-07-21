"""
FastAPI Dependency Validators

Reusable dependencies for common validation patterns.
Use these with FastAPI's Depends() for cleaner route definitions.

Usage:
    @router.get("/items")
    async def list_items(
        pagination: PaginationParams = Depends(get_pagination),
    ):
        items = await get_items(
            page=pagination.page,
            page_size=pagination.page_size
        )
"""

from typing import Optional
from dataclasses import dataclass

from fastapi import Query


@dataclass
class PaginationParams:
    """Validated pagination parameters."""
    page: int
    page_size: int
    offset: int  # Calculated: (page - 1) * page_size


def get_pagination(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> PaginationParams:
    """
    Get validated pagination parameters.

    FastAPI Query validation handles the constraints automatically.

    Returns:
        PaginationParams with page, page_size, and calculated offset
    """
    return PaginationParams(
        page=page,
        page_size=page_size,
        offset=(page - 1) * page_size,
    )


def get_pagination_flexible(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),  # Allow larger for exports
) -> PaginationParams:
    """
    Get pagination with larger max page size.

    Use for endpoints that support bulk exports.
    """
    return PaginationParams(
        page=page,
        page_size=page_size,
        offset=(page - 1) * page_size,
    )


@dataclass
class SortParams:
    """Validated sorting parameters."""
    sort_by: str
    sort_order: str  # 'asc' or 'desc'


def get_sort(
    sort_by: Optional[str] = Query(default=None, description="Field to sort by"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$", description="Sort order"),
    allowed_fields: Optional[list] = None,
) -> Optional[SortParams]:
    """
    Get validated sorting parameters.

    Args:
        sort_by: Field name to sort by
        sort_order: 'asc' or 'desc'
        allowed_fields: List of allowed field names (for security)

    Returns:
        SortParams or None if no sorting requested
    """
    if not sort_by:
        return None

    # Validate against allowed fields if provided
    if allowed_fields and sort_by not in allowed_fields:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=f"Cannot sort by '{sort_by}'. Allowed fields: {', '.join(allowed_fields)}"
        )

    return SortParams(
        sort_by=sort_by,
        sort_order=sort_order,
    )


@dataclass
class SearchParams:
    """Validated search parameters."""
    query: str
    fields: Optional[list]


def get_search(
    q: Optional[str] = Query(default=None, min_length=1, max_length=200, description="Search query"),
    search_fields: Optional[str] = Query(default=None, description="Comma-separated fields to search"),
    allowed_fields: Optional[list] = None,
) -> Optional[SearchParams]:
    """
    Get validated search parameters.

    Args:
        q: Search query string
        search_fields: Comma-separated list of fields to search
        allowed_fields: List of allowed search fields (for security)

    Returns:
        SearchParams or None if no search query
    """
    if not q:
        return None

    fields = None
    if search_fields:
        fields = [f.strip() for f in search_fields.split(",")]

        # Validate against allowed fields if provided
        if allowed_fields:
            invalid_fields = [f for f in fields if f not in allowed_fields]
            if invalid_fields:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot search in fields: {', '.join(invalid_fields)}. "
                           f"Allowed: {', '.join(allowed_fields)}"
                )

    return SearchParams(
        query=q,
        fields=fields,
    )
