"""Milvus vector database client for event storage and retrieval.

Provides async interface for connecting to Milvus and performing
vector search operations on event embeddings.

Usage:
    client = MilvusClient(uri="http://localhost:19530")
    await client.connect()
    await client.insert_event("event-123", [0.1, 0.2, ...], {"title": "Test Event"})
    results = await client.search_events([0.1, 0.2, ...], top_k=5)
    await client.close()
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MilvusConfig:
    """Configuration for Milvus connection."""

    uri: str = "http://localhost:19530"
    token: str | None = None
    db_name: str = "default"
    collection_name: str = "novel_events"
    dimension: int = 1536
    max_retry_attempts: int = 3
    retry_delay: float = 1.0
    connection_timeout: float = 30.0


@dataclass
class InsertResult:
    """Result of an insert operation."""

    success: bool
    ids: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class SearchResult:
    """Result of a vector search operation."""

    success: bool
    results: list[dict[str, object]] = field(default_factory=list)
    error: str | None = None


class MilvusClient:
    """Async Milvus client for vector storage and search operations.

    This client provides a high-level interface for interacting with Milvus
    vector database, supporting event insertion and similarity search.

    Attributes:
        config: Milvus connection configuration
        _client: Milvus client instance (lazy initialization)
        _connected: Whether client is connected
    """

    config: MilvusConfig
    _client: Any
    _connected: bool

    def __init__(self, config: MilvusConfig | None = None) -> None:
        """Initialize the Milvus client.

        Args:
            config: Optional configuration object. If None, uses defaults.
        """
        self.config = config or MilvusConfig()
        self._client = None
        self._connected = False

    async def connect(self) -> bool:
        """Establish connection to Milvus database.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            from pymilvus import MilvusClient as PyMilvusClient

            kwargs: dict[str, Any] = {
                "uri": self.config.uri,
                "db_name": self.config.db_name,
                "timeout": self.config.connection_timeout,
            }
            if self.config.token is not None:
                kwargs["token"] = self.config.token

            self._client = PyMilvusClient(**kwargs)  # type: ignore

            # Check if collection exists, create if not
            if not self._client.has_collection(self.config.collection_name):  # type: ignore
                self._client.create_collection(  # type: ignore
                    collection_name=self.config.collection_name,
                    dimension=self.config.dimension,
                    auto_id=False,
                    primary_field_name="event_id",
                    vector_field_name="embedding",
                )
                logger.info(f"Created collection: {self.config.collection_name}")

            self._connected = True
            logger.info(f"Connected to Milvus at {self.config.uri}")
            return True

        except ImportError:
            logger.error(
                "pymilvus package not installed. Install with: pip install pymilvus>=2.3.0"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            self._connected = False
            return False

    async def close(self) -> None:
        """Close the Milvus connection."""
        if self._client:
            self._client.close()  # type: ignore
            self._client = None
            self._connected = False
            logger.info("Milvus connection closed")

    async def insert_event(
        self,
        event_id: str,
        embedding: list[float],
        metadata: dict[str, object] | None = None,
    ) -> InsertResult:
        """Insert an event embedding into Milvus.

        Args:
            event_id: Unique event identifier
            embedding: Vector embedding array
            metadata: Optional metadata dictionary

        Returns:
            InsertResult with operation status
        """
        if not self._connected or not self._client:
            return InsertResult(success=False, error="Not connected to Milvus")

        attempts = 0
        while attempts < self.config.max_retry_attempts:
            try:
                data: dict[str, object] = {
                    "event_id": event_id,
                    "embedding": embedding,
                    "metadata": metadata or {},
                    "created_at": datetime.now().isoformat(),
                }

                _ = self._client.insert(  # type: ignore
                    collection_name=self.config.collection_name,
                    data=[data],
                )

                return InsertResult(success=True, ids=[event_id])

            except Exception as e:
                attempts += 1
                if attempts >= self.config.max_retry_attempts:
                    logger.error(f"Insert failed after {attempts} attempts: {e}")
                    return InsertResult(success=False, error=str(e))

                await asyncio.sleep(self.config.retry_delay)
                logger.warning(
                    f"Insert failed, retrying ({attempts}/{self.config.max_retry_attempts}): {e}"
                )

        return InsertResult(success=False, error="Max retry attempts exceeded")

    async def search_events(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter_expr: str | None = None,
    ) -> SearchResult:
        """Search for similar events using vector similarity.

        Args:
            query_embedding: Query vector embedding
            top_k: Number of results to return
            filter_expr: Optional filter expression for metadata

        Returns:
            SearchResult with matching events
        """
        if not self._connected or not self._client:
            return SearchResult(success=False, error="Not connected to Milvus")

        attempts = 0
        while attempts < self.config.max_retry_attempts:
            try:
                search_kwargs: dict[str, Any] = {
                    "collection_name": self.config.collection_name,
                    "data": [query_embedding],
                    "limit": top_k,
                    "output_fields": ["event_id", "metadata", "created_at"],
                }
                if filter_expr is not None:
                    search_kwargs["filter"] = filter_expr

                results: Any = self._client.search(**search_kwargs)  # type: ignore

                # Process results
                processed: list[dict[str, object]] = []
                for hits in results:
                    for hit in hits:
                        entity: dict[str, Any] = hit["entity"]  # type: ignore
                        processed.append(
                            {
                                "event_id": entity.get("event_id"),
                                "score": hit.get("distance", 0.0),
                                "metadata": entity.get("metadata", {}),
                                "created_at": entity.get("created_at"),
                            }
                        )

                return SearchResult(success=True, results=processed)

            except Exception as e:
                attempts += 1
                if attempts >= self.config.max_retry_attempts:
                    logger.error(f"Search failed after {attempts} attempts: {e}")
                    return SearchResult(success=False, error=str(e))

                await asyncio.sleep(self.config.retry_delay)
                logger.warning(
                    f"Search failed, retrying ({attempts}/{self.config.max_retry_attempts}): {e}"
                )

        return SearchResult(success=False, error="Max retry attempts exceeded")

    async def health_check(self) -> dict[str, object]:
        """Check database health and return stats.

        Returns:
            Dictionary with health status and statistics
        """
        try:
            if not self._connected or not self._client:
                return {
                    "connected": False,
                    "healthy": False,
                    "error": "Not connected to Milvus",
                }

            # Get collection stats
            stats: Any = self._client.get_collection_stats(self.config.collection_name)  # type: ignore
            entity_count: int = stats.get("row_count", 0)  # type: ignore

            return {
                "connected": self._connected,
                "healthy": True,
                "collection_name": self.config.collection_name,
                "entity_count": entity_count,
                "db_name": self.config.db_name,
                "uri": self.config.uri,
            }
        except Exception as e:
            return {
                "connected": False,
                "healthy": False,
                "error": str(e),
            }
