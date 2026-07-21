"""Vector-store ports with memory and Qdrant adapters."""

import asyncio
import hashlib
import logging
import math
import os
import random
import re
import uuid
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any, Optional

logger = logging.getLogger(__name__)


class VectorStoreError(RuntimeError):
    """A vector backend could not complete an operation."""


class VectorStoreNotFoundError(VectorStoreError):
    """A requested vector collection does not exist."""


class VectorStoreConflictError(VectorStoreError):
    """A vector resource conflicts with existing state."""


class VectorStoreValidationError(VectorStoreError):
    """A vector operation is incompatible with provider configuration."""


class EmbeddingProvider:
    """Embedding adapter with explicit vendor selection and a local fallback."""

    def __init__(self, dimension: int = 768, max_retries: int = 3):
        self.dimension = dimension
        self.max_retries = max_retries

    async def embed(self, text: str) -> list[float]:
        mode = os.getenv("EMBEDDING_PROVIDER", "auto").strip().lower()
        if mode not in {"auto", "ollama", "openai", "local"}:
            raise VectorStoreError(f"unsupported embedding provider: {mode}")
        if mode == "ollama" or (mode == "auto" and os.getenv("OLLAMA_EMBEDDING_URL")):
            result = await self._embed_ollama(text)
            if result:
                return result
            if mode == "ollama":
                raise VectorStoreError("Ollama embedding provider is unavailable")
        if mode == "openai" or (mode == "auto" and os.getenv("OPENAI_API_KEY")):
            result = await self._embed_openai(text)
            if result:
                return result
            if mode == "openai":
                raise VectorStoreError("OpenAI embedding provider is unavailable")
        return self._embed_local(text)

    async def _embed_ollama(self, text: str) -> Optional[list[float]]:
        try:
            import httpx
        except ImportError:
            return None

        url = os.getenv(
            "OLLAMA_EMBEDDING_URL",
            "http://localhost:11434/api/embeddings",
        )
        model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        url,
                        json={"model": model, "prompt": text},
                    )
                if response.status_code == 200:
                    embedding = response.json().get("embedding", [])
                    if len(embedding) == self.dimension:
                        return embedding
                    logger.warning(
                        "Ollama embedding dimension mismatch: expected %d, got %d",
                        self.dimension,
                        len(embedding),
                    )
                    return None
                if response.status_code < 500:
                    return None
            except Exception as exc:
                logger.info("Ollama embedding attempt failed: %s", type(exc).__name__)
            await self._backoff(attempt)
        return None

    async def _embed_openai(self, text: str) -> Optional[list[float]]:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        try:
            import openai
        except ImportError:
            return None

        for attempt in range(self.max_retries):
            try:
                client = openai.AsyncOpenAI(api_key=api_key, timeout=30.0)
                response = await client.embeddings.create(
                    model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
                    input=text,
                    dimensions=self.dimension,
                )
                embedding = response.data[0].embedding
                if len(embedding) == self.dimension:
                    return embedding
                return None
            except Exception as exc:
                logger.info("OpenAI embedding attempt failed: %s", type(exc).__name__)
            await self._backoff(attempt)
        return None

    def _embed_local(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = re.findall(r"\w+", text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            vector[index] += 1.0 if digest[4] & 1 else -1.0
        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            return [value / norm for value in vector]
        return vector

    async def _backoff(self, attempt: int) -> None:
        if attempt < self.max_retries - 1:
            await asyncio.sleep((2**attempt) + random.uniform(0, 1))


class VectorStoreProvider(ABC):
    """Deployment-neutral vector-store port."""

    @abstractmethod
    async def list_collections(self) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def create_collection(self, name: str, dimension: int) -> dict[str, Any]:
        pass

    @abstractmethod
    async def get_collection_stats(self, name: str) -> dict[str, Any]:
        pass

    @abstractmethod
    async def insert_document(
        self,
        *,
        collection: str,
        content: str,
        document_id: Optional[str],
        metadata: Optional[dict[str, Any]],
    ) -> dict[str, Any]:
        pass

    @abstractmethod
    async def search_documents(
        self,
        *,
        collection: str,
        query: str,
        top_k: int,
        score_threshold: float,
        filters: Optional[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def delete_documents(
        self,
        *,
        collection: str,
        ids: Optional[list[str]],
        filters: Optional[dict[str, Any]],
    ) -> dict[str, Any]:
        pass


class MemoryVectorStoreProvider(VectorStoreProvider):
    """Process-local vector store for offline and unconfigured deployments."""

    def __init__(self, embedding_provider: Optional[EmbeddingProvider] = None):
        self._embedding_provider = embedding_provider or EmbeddingProvider()
        self._collections: dict[str, dict[str, Any]] = {
            "flyto_knowledge": {
                "dimension": self._embedding_provider.dimension,
                "documents": {},
            }
        }

    def _require_collection(self, name: str) -> dict[str, Any]:
        try:
            return self._collections[name]
        except KeyError as exc:
            raise VectorStoreNotFoundError(
                f"vector collection does not exist: {name}"
            ) from exc

    async def list_collections(self) -> list[dict[str, Any]]:
        return [
            {
                "name": name,
                "count": len(data["documents"]),
                "dimension": data["dimension"],
            }
            for name, data in self._collections.items()
        ]

    async def create_collection(self, name: str, dimension: int) -> dict[str, Any]:
        if name in self._collections:
            raise VectorStoreConflictError(f"vector collection already exists: {name}")
        if dimension != self._embedding_provider.dimension:
            raise VectorStoreValidationError(
                "collection dimension does not match the embedding provider"
            )
        self._collections[name] = {"dimension": dimension, "documents": {}}
        return {"name": name, "count": 0, "dimension": dimension}

    async def get_collection_stats(self, name: str) -> dict[str, Any]:
        collection = self._require_collection(name)
        count = len(collection["documents"])
        return {
            "ok": True,
            "name": name,
            "points_count": count,
            "indexed_vectors_count": count,
            "dimension": collection["dimension"],
        }

    async def insert_document(
        self,
        *,
        collection: str,
        content: str,
        document_id: Optional[str],
        metadata: Optional[dict[str, Any]],
    ) -> dict[str, Any]:
        resolved_id = document_id or str(uuid.uuid4())
        target = self._require_collection(collection)
        target["documents"][resolved_id] = {
            "content": content,
            "embedding": await self._embedding_provider.embed(content),
            "metadata": metadata or {},
        }
        return {
            "document_id": resolved_id,
            "message": "Document inserted successfully",
        }

    async def search_documents(
        self,
        *,
        collection: str,
        query: str,
        top_k: int,
        score_threshold: float,
        filters: Optional[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        query_embedding = await self._embedding_provider.embed(query)
        documents = self._require_collection(collection)["documents"]
        results = []
        for document_id, document in documents.items():
            metadata = document["metadata"]
            if filters and any(metadata.get(key) != value for key, value in filters.items()):
                continue
            score = sum(
                left * right
                for left, right in zip(query_embedding, document["embedding"])
            )
            if score >= score_threshold:
                results.append(
                    {
                        "id": document_id,
                        "score": score,
                        "content": document["content"],
                        "metadata": metadata,
                    }
                )
        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:top_k]

    async def delete_documents(
        self,
        *,
        collection: str,
        ids: Optional[list[str]],
        filters: Optional[dict[str, Any]],
    ) -> dict[str, Any]:
        documents = self._require_collection(collection)["documents"]
        if ids:
            targets = [document_id for document_id in ids if document_id in documents]
        else:
            targets = [
                document_id
                for document_id, document in documents.items()
                if filters
                and all(
                    document["metadata"].get(key) == value
                    for key, value in filters.items()
                )
            ]
        for document_id in targets:
            del documents[document_id]
        return {
            "deleted_count": len(targets),
            "message": f"Deleted {len(targets)} documents",
        }


class QdrantVectorStoreProvider(VectorStoreProvider):
    """Qdrant adapter; all vendor types remain inside this module."""

    def __init__(self, embedding_provider: Optional[EmbeddingProvider] = None):
        try:
            from qdrant_client import QdrantClient
        except ImportError as exc:
            raise VectorStoreError("Qdrant provider is not installed") from exc

        url = os.getenv("QDRANT_URL", "http://localhost:6333")
        api_key = os.getenv("QDRANT_API_KEY")
        kwargs = {"url": url}
        if api_key:
            kwargs["api_key"] = api_key
        self._client = QdrantClient(**kwargs)
        self._embedding_provider = embedding_provider or EmbeddingProvider()

    async def list_collections(self) -> list[dict[str, Any]]:
        try:
            response = await asyncio.to_thread(self._client.get_collections)
            result = []
            for collection in response.collections:
                info = await asyncio.to_thread(self._client.get_collection, collection.name)
                result.append(
                    {
                        "name": collection.name,
                        "count": info.points_count,
                        "dimension": info.config.params.vectors.size,
                    }
                )
            return result
        except Exception as exc:
            raise VectorStoreError("failed to list vector collections") from exc

    async def create_collection(self, name: str, dimension: int) -> dict[str, Any]:
        if dimension != self._embedding_provider.dimension:
            raise VectorStoreValidationError(
                "collection dimension does not match the embedding provider"
            )
        try:
            from qdrant_client.models import Distance, VectorParams

            await asyncio.to_thread(
                self._client.create_collection,
                collection_name=name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            )
            return {"name": name, "count": 0, "dimension": dimension}
        except Exception as exc:
            raise VectorStoreError("failed to create vector collection") from exc

    async def get_collection_stats(self, name: str) -> dict[str, Any]:
        try:
            info = await asyncio.to_thread(self._client.get_collection, name)
            return {
                "ok": True,
                "name": name,
                "points_count": info.points_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "dimension": info.config.params.vectors.size,
            }
        except Exception as exc:
            raise VectorStoreError("failed to read vector collection") from exc

    async def insert_document(
        self,
        *,
        collection: str,
        content: str,
        document_id: Optional[str],
        metadata: Optional[dict[str, Any]],
    ) -> dict[str, Any]:
        try:
            from qdrant_client.models import PointStruct

            resolved_id = document_id or str(uuid.uuid4())
            payload = {"content": content, **(metadata or {})}
            embedding = await self._embedding_provider.embed(content)
            await asyncio.to_thread(
                self._client.upsert,
                collection_name=collection,
                points=[PointStruct(id=resolved_id, vector=embedding, payload=payload)],
            )
            return {
                "document_id": resolved_id,
                "message": "Document inserted successfully",
            }
        except VectorStoreError:
            raise
        except Exception as exc:
            raise VectorStoreError("failed to insert vector document") from exc

    async def search_documents(
        self,
        *,
        collection: str,
        query: str,
        top_k: int,
        score_threshold: float,
        filters: Optional[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        try:
            query_filter = self._filter(filters)
            embedding = await self._embedding_provider.embed(query)
            hits = await asyncio.to_thread(
                self._client.search,
                collection_name=collection,
                query_vector=embedding,
                query_filter=query_filter,
                limit=top_k,
                score_threshold=score_threshold,
            )
            return [
                {
                    "id": str(hit.id),
                    "score": hit.score,
                    "content": hit.payload.get("content", ""),
                    "metadata": {
                        key: value
                        for key, value in hit.payload.items()
                        if key != "content"
                    },
                }
                for hit in hits
            ]
        except VectorStoreError:
            raise
        except Exception as exc:
            raise VectorStoreError("failed to search vector documents") from exc

    async def delete_documents(
        self,
        *,
        collection: str,
        ids: Optional[list[str]],
        filters: Optional[dict[str, Any]],
    ) -> dict[str, Any]:
        try:
            from qdrant_client.models import PointIdsList

            selector = PointIdsList(points=ids) if ids else self._filter(filters)
            await asyncio.to_thread(
                self._client.delete,
                collection_name=collection,
                points_selector=selector,
            )
            count = len(ids) if ids else 0
            return {
                "deleted_count": count,
                "message": (
                    f"Deleted {count} documents"
                    if ids
                    else "Documents deleted by filter"
                ),
            }
        except Exception as exc:
            raise VectorStoreError("failed to delete vector documents") from exc

    @staticmethod
    def _filter(filters: Optional[dict[str, Any]]):
        if not filters:
            return None
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        return Filter(
            must=[
                FieldCondition(key=key, match=MatchValue(value=value))
                for key, value in filters.items()
            ]
        )


@lru_cache(maxsize=1)
def get_vector_store_provider() -> VectorStoreProvider:
    """Build the configured vector backend once per process."""
    mode = os.getenv("VECTOR_STORE_PROVIDER", "auto").strip().lower()
    if mode == "auto":
        mode = "qdrant" if os.getenv("QDRANT_URL") else "memory"
    if mode == "memory":
        return MemoryVectorStoreProvider()
    if mode == "qdrant":
        return QdrantVectorStoreProvider()
    raise VectorStoreError(f"unsupported vector store provider: {mode}")


def reset_vector_store_provider() -> None:
    """Clear the provider factory cache for tests and configuration reloads."""
    get_vector_store_provider.cache_clear()
