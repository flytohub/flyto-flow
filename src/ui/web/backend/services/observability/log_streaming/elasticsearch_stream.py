"""
Elasticsearch Log Stream

Elasticsearch/OpenSearch implementation for log streaming.
Supports bulk API and index templates.
"""

import asyncio
import json
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import aiohttp

from services.observability.log_streaming.interface import LogEvent, LogStreamInterface, StreamConfig

logger = logging.getLogger(__name__)


@dataclass
class ElasticsearchConfig(StreamConfig):
    """Elasticsearch-specific configuration."""
    url: str = "http://localhost:9200"
    index_prefix: str = "flyto-logs"
    index_pattern: str = "daily"  # daily, weekly, monthly
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    verify_ssl: bool = True
    timeout_seconds: float = 30.0
    use_ecs: bool = True  # Use Elastic Common Schema


class ElasticsearchStream(LogStreamInterface):
    """
    Elasticsearch log stream.

    Features:
    - Bulk API for efficient indexing
    - Date-based index rotation
    - ECS (Elastic Common Schema) format
    - Authentication (basic, API key)
    - Connection pooling
    """

    def __init__(
        self,
        url: str = "http://localhost:9200",
        config: Optional[ElasticsearchConfig] = None,
        **kwargs,
    ):
        """
        Initialize Elasticsearch stream.

        Args:
            url: Elasticsearch URL
            config: Stream configuration
            **kwargs: Additional config options
        """
        if config is None:
            config = ElasticsearchConfig(url=url, **kwargs)
        else:
            config.url = url

        super().__init__(config)
        self.es_config = config
        self._buffer: deque = deque(maxlen=config.batch_size * 2)
        self._session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()

    def _get_index_name(self) -> str:
        """
        Get the current index name based on pattern.

        Returns:
            Index name string
        """
        now = datetime.now(timezone.utc)
        prefix = self.es_config.index_prefix

        if self.es_config.index_pattern == "daily":
            return f"{prefix}-{now.strftime('%Y.%m.%d')}"
        elif self.es_config.index_pattern == "weekly":
            return f"{prefix}-{now.strftime('%Y.%W')}"
        elif self.es_config.index_pattern == "monthly":
            return f"{prefix}-{now.strftime('%Y.%m')}"
        else:
            return prefix

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            headers = {"Content-Type": "application/json"}

            # Authentication
            auth = None
            if self.es_config.api_key:
                headers["Authorization"] = f"ApiKey {self.es_config.api_key}"
            elif self.es_config.username and self.es_config.password:
                auth = aiohttp.BasicAuth(
                    self.es_config.username,
                    self.es_config.password,
                )

            connector = aiohttp.TCPConnector(
                ssl=self.es_config.verify_ssl,
            )
            timeout = aiohttp.ClientTimeout(
                total=self.es_config.timeout_seconds,
            )

            self._session = aiohttp.ClientSession(
                headers=headers,
                auth=auth,
                connector=connector,
                timeout=timeout,
            )

        return self._session

    def _format_document(self, event: LogEvent) -> Dict[str, Any]:
        """
        Format event as Elasticsearch document.

        Args:
            event: Log event

        Returns:
            Document dict
        """
        if self.es_config.use_ecs:
            return event.to_ecs()
        else:
            return event.to_dict()

    async def push(self, event: LogEvent) -> bool:
        """
        Push a single log event.

        Args:
            event: Log event to push

        Returns:
            True if successfully pushed
        """
        try:
            session = await self._get_session()
            index = self._get_index_name()
            doc = self._format_document(event)

            url = f"{self.es_config.url}/{index}/_doc"

            async with session.post(url, json=doc) as response:
                if response.status in (200, 201):
                    return True
                else:
                    body = await response.text()
                    logger.warning(
                        f"Elasticsearch returned {response.status}: {body[:200]}"
                    )
                    return False

        except asyncio.TimeoutError:
            logger.warning("Elasticsearch timeout")
            return False

        except aiohttp.ClientError as e:
            logger.error(f"Elasticsearch error: {e}")
            return False

        except Exception as e:
            logger.error(f"Unexpected Elasticsearch error: {e}")
            return False

    async def push_batch(self, events: List[LogEvent]) -> int:
        """
        Push a batch of log events using bulk API.

        Args:
            events: List of log events

        Returns:
            Number of successfully pushed events
        """
        if not events:
            return 0

        try:
            session = await self._get_session()
            index = self._get_index_name()

            # Build bulk request body (NDJSON)
            lines = []
            for event in events:
                # Action line
                action = {"index": {"_index": index}}
                lines.append(json.dumps(action))
                # Document line
                doc = self._format_document(event)
                lines.append(json.dumps(doc))

            body = "\n".join(lines) + "\n"

            url = f"{self.es_config.url}/_bulk"
            headers = {"Content-Type": "application/x-ndjson"}

            async with session.post(url, data=body, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()

                    # Count successful items
                    if result.get("errors"):
                        success_count = sum(
                            1 for item in result.get("items", [])
                            if item.get("index", {}).get("status") in (200, 201)
                        )
                        failed = len(events) - success_count
                        if failed > 0:
                            logger.warning(f"Elasticsearch bulk: {failed} items failed")
                        return success_count
                    else:
                        return len(events)
                else:
                    body_text = await response.text()
                    logger.warning(
                        f"Elasticsearch bulk returned {response.status}: {body_text[:200]}"
                    )
                    return 0

        except Exception as e:
            logger.error(f"Elasticsearch bulk error: {e}")
            # Fall back to individual pushes
            success = 0
            for event in events:
                if await self.push(event):
                    success += 1
            return success

    async def flush(self) -> int:
        """
        Flush any buffered events.

        Returns:
            Number of flushed events
        """
        async with self._lock:
            if not self._buffer:
                return 0

            events = list(self._buffer)
            self._buffer.clear()

        return await self.push_batch(events)

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Elasticsearch cluster health.

        Returns:
            Health status dict
        """
        try:
            session = await self._get_session()
            url = f"{self.es_config.url}/_cluster/health"

            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "healthy": data.get("status") in ("green", "yellow"),
                        "cluster_status": data.get("status"),
                        "cluster_name": data.get("cluster_name"),
                        "number_of_nodes": data.get("number_of_nodes"),
                        "active_shards": data.get("active_shards"),
                    }
                else:
                    return {
                        "healthy": False,
                        "status_code": response.status,
                    }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
            }

    async def ensure_index_template(self) -> bool:
        """
        Ensure index template exists for proper mappings.

        Returns:
            True if template exists or was created
        """
        try:
            session = await self._get_session()
            template_name = f"{self.es_config.index_prefix}-template"

            template = {
                "index_patterns": [f"{self.es_config.index_prefix}-*"],
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 1,
                    "index.lifecycle.name": "flyto-logs-policy",
                },
                "mappings": {
                    "properties": {
                        "@timestamp": {"type": "date"},
                        "message": {"type": "text"},
                        "log.level": {"type": "keyword"},
                        "event.id": {"type": "keyword"},
                        "event.type": {"type": "keyword"},
                        "event.action": {"type": "keyword"},
                        "event.category": {"type": "keyword"},
                        "event.outcome": {"type": "keyword"},
                        "user.id": {"type": "keyword"},
                        "organization.id": {"type": "keyword"},
                        "source.address": {"type": "ip"},
                        "labels": {"type": "object", "dynamic": True},
                        "tags": {"type": "keyword"},
                    }
                },
            }

            url = f"{self.es_config.url}/_index_template/{template_name}"

            async with session.put(url, json=template) as response:
                if response.status in (200, 201):
                    logger.info(f"Index template created: {template_name}")
                    return True
                else:
                    body = await response.text()
                    logger.warning(f"Failed to create template: {body[:200]}")
                    return False

        except Exception as e:
            logger.error(f"Error creating index template: {e}")
            return False

    async def close(self) -> None:
        """Close the stream and cleanup resources."""
        await self.flush()

        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

        logger.info("Elasticsearch stream closed")
