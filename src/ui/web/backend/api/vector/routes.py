"""Authenticated HTTP routes for the configured vector-store provider."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from gateway.local_context import get_local_actor

get_workspace_context = get_local_actor
from gateway.providers.vector import (
    VectorStoreConflictError,
    VectorStoreError,
    VectorStoreNotFoundError,
    VectorStoreValidationError,
    get_vector_store_provider,
)

logger = logging.getLogger(__name__)

# Deprecated local vector API retained for workflow compatibility.
router = APIRouter(
    prefix="/vector",
    tags=["Vector Store"],
    dependencies=[Depends(get_workspace_context)],
)


class CollectionInfo(BaseModel):
    name: str
    count: int = 0
    dimension: int = 768


class CollectionCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$",
    )
    dimension: int = Field(768, ge=1, le=65536)


class CollectionsResponse(BaseModel):
    ok: bool
    collections: List[CollectionInfo]


class InsertRequest(BaseModel):
    collection: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$",
    )
    content: str = Field(..., min_length=1, max_length=1_000_000)
    document_id: Optional[str] = Field(None, max_length=256)
    metadata: Optional[Dict[str, Any]] = None


class InsertResponse(BaseModel):
    ok: bool
    document_id: str
    message: str


class SearchRequest(BaseModel):
    collection: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$",
    )
    query: str = Field(..., min_length=1, max_length=100_000)
    top_k: int = Field(5, ge=1, le=100)
    score_threshold: float = Field(0.7, ge=-1.0, le=1.0)
    filters: Optional[Dict[str, Any]] = None


class SearchResult(BaseModel):
    id: str
    score: float
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    ok: bool
    results: List[SearchResult]
    count: int


class DeleteRequest(BaseModel):
    collection: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$",
    )
    ids: Optional[List[str]] = Field(None, max_length=1000)
    filter: Optional[Dict[str, Any]] = None


class DeleteResponse(BaseModel):
    ok: bool
    deleted_count: int
    message: str


def _provider():
    try:
        return get_vector_store_provider()
    except VectorStoreError as exc:
        logger.error("Vector store provider initialization failed: %s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Vector store is unavailable") from exc


def _provider_error(exc: VectorStoreError) -> HTTPException:
    logger.warning("Vector store operation failed: %s", type(exc).__name__)
    if isinstance(exc, VectorStoreNotFoundError):
        return HTTPException(status_code=404, detail="Vector collection was not found")
    if isinstance(exc, VectorStoreConflictError):
        return HTTPException(status_code=409, detail="Vector collection already exists")
    if isinstance(exc, VectorStoreValidationError):
        return HTTPException(status_code=422, detail="Vector configuration is invalid")
    return HTTPException(status_code=503, detail="Vector store is unavailable")


@router.get("/health")
async def vector_health():
    provider = _provider()
    return {
        "ok": True,
        "status": "healthy",
        "service": "vector",
        "provider": provider.__class__.__name__,
        "version": "1.0.0",
    }


@router.get("/collections", response_model=CollectionsResponse)
async def list_collections():
    try:
        collections = await _provider().list_collections()
    except VectorStoreError as exc:
        raise _provider_error(exc) from exc
    return CollectionsResponse(
        ok=True,
        collections=[CollectionInfo(**collection) for collection in collections],
    )


@router.post("/collections", response_model=CollectionInfo)
async def create_collection(request: CollectionCreateRequest):
    try:
        collection = await _provider().create_collection(
            request.name,
            request.dimension,
        )
    except VectorStoreError as exc:
        raise _provider_error(exc) from exc
    return CollectionInfo(**collection)


@router.get("/collections/{name}/stats")
async def get_collection_stats(name: str):
    try:
        return await _provider().get_collection_stats(name)
    except VectorStoreError as exc:
        raise _provider_error(exc) from exc


@router.post("/insert", response_model=InsertResponse)
async def insert_document(request: InsertRequest):
    try:
        result = await _provider().insert_document(
            collection=request.collection,
            content=request.content,
            document_id=request.document_id,
            metadata=request.metadata,
        )
    except VectorStoreError as exc:
        raise _provider_error(exc) from exc
    return InsertResponse(ok=True, **result)


@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    try:
        result = await _provider().search_documents(
            collection=request.collection,
            query=request.query,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            filters=request.filters,
        )
    except VectorStoreError as exc:
        raise _provider_error(exc) from exc
    items = [SearchResult(**item) for item in result]
    return SearchResponse(ok=True, results=items, count=len(items))


@router.post("/delete", response_model=DeleteResponse)
async def delete_documents(request: DeleteRequest):
    if not request.ids and not request.filter:
        raise HTTPException(
            status_code=400,
            detail="Either 'ids' or 'filter' must be provided",
        )
    try:
        result = await _provider().delete_documents(
            collection=request.collection,
            ids=request.ids,
            filters=request.filter,
        )
    except VectorStoreError as exc:
        raise _provider_error(exc) from exc
    return DeleteResponse(ok=True, **result)
