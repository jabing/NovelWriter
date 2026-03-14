# src/db/pinecone_client.py
"""Pinecone vector database client for semantic similarity search."""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from pinecone import Pinecone

from src.novel_agent.db.embedding_generator import EmbeddingGenerator

logger = logging.getLogger(__name__)


@dataclass
class VectorSearchResult:
    """Result from a vector similarity search."""

    id: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class VectorUpsertResult:
    """Result from a vector upsert operation."""

    id: str
    success: bool
    error: str | None = None


class VectorStore:
    """Pinecone vector database client for semantic similarity search.

    Provides efficient storage and retrieval of text embeddings for:
    - Fact retrieval and verification
    - Semantic similarity search
    - Hallucination detection support

    Uses cosine similarity metric and supports free tier (100K vectors).
    """

    DEFAULT_INDEX_NAME = "novel-facts"
    DEFAULT_NAMESPACE = "default"
    DEFAULT_TOP_K = 10
    BATCH_SIZE = 100  # Pinecone batch upsert limit

    def __init__(
        self,
        api_key: str,
        index_name: str = DEFAULT_INDEX_NAME,
        namespace: str = DEFAULT_NAMESPACE,
        embedding_generator: EmbeddingGenerator | None = None,
        environment: str = "us-east-1",  # Pinecone cloud region
    ) -> None:
        """Initialize the Pinecone vector store.

        Args:
            api_key: Pinecone API key.
            index_name: Name of the Pinecone index.
            namespace: Namespace for isolating different novels/projects.
            embedding_generator: Optional embedding generator instance.
                               If not provided, creates a default one.
            environment: Pinecone cloud region (ignored in new API, kept for compat).
        """
        self.api_key = api_key
        self.index_name = index_name
        self.namespace = namespace
        self.environment = environment
        self._pc: Pinecone | None = None
        self._index = None
        self._embedding_generator = embedding_generator or EmbeddingGenerator()

        # Validate index name (must be lowercase, alphanumeric, hyphens only)
        if not self._is_valid_index_name(index_name):
            raise ValueError(
                f"Invalid index name '{index_name}'. "
                "Must be lowercase alphanumeric with hyphens only."
            )

    def _is_valid_index_name(self, name: str) -> bool:
        """Validate Pinecone index name format."""
        import re

        return bool(re.match(r"^[a-z0-9-]+$", name))

    @property
    def pc(self) -> Pinecone:
        """Lazy-load Pinecone client."""
        if self._pc is None:
            logger.info("Initializing Pinecone client")
            self._pc = Pinecone(api_key=self.api_key)
        return self._pc

    @property
    def index(self):
        """Lazy-load Pinecone index."""
        if self._index is None:
            logger.info(f"Connecting to Pinecone index: {self.index_name}")
            self._index = self.pc.Index(self.index_name)
        return self._index

    async def create_index_if_not_exists(
        self,
        dimension: int = EmbeddingGenerator.VECTOR_DIMENSION,
        metric: str = "cosine",
        cloud: str = "aws",
        region: str = "us-east-1",
    ) -> bool:
        """Create the Pinecone index if it doesn't exist.

        Args:
            dimension: Vector dimension (384 for all-MiniLM-L6-v2).
            metric: Similarity metric (cosine, dotproduct, euclidean).
            cloud: Cloud provider (aws, gcp, azure).
            region: Cloud region.

        Returns:
            True if index was created, False if already exists.
        """
        try:
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]

            if self.index_name in existing_indexes:
                logger.info(f"Index '{self.index_name}' already exists")
                return False

            logger.info(f"Creating Pinecone index: {self.index_name}")
            self.pc.create_index_for_model(
                name=self.index_name,
                cloud=cloud,
                region=region,
                embed={
                    "model": "llama-text-embed-v2",
                    "field_map": {"text": "text"},
                },
            )

            # Wait for index to be ready
            import time

            max_wait = 120  # seconds
            start = time.time()
            while time.time() - start < max_wait:
                try:
                    # Try to describe the index
                    self.pc.describe_index(self.index_name)
                    logger.info(f"Index '{self.index_name}' is ready")
                    return True
                except Exception:
                    await asyncio.sleep(2)

            logger.warning(f"Index creation timeout after {max_wait}s")
            return True

        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            raise

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for text.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector.
        """
        # Run in thread pool since sentence-transformers is synchronous
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._embedding_generator.embed_text, text
        )

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._embedding_generator.embed_batch, texts
        )

    async def upsert_vectors(
        self,
        ids: list[str],
        texts: list[str],
        metadata: list[dict[str, Any]] | None = None,
    ) -> list[VectorUpsertResult]:
        """Upsert vectors to the Pinecone index.

        Automatically generates embeddings from text and stores them
        with associated metadata.

        Args:
            ids: List of unique IDs for each vector.
            texts: List of texts to embed and store.
            metadata: Optional list of metadata dicts for each vector.

        Returns:
            List of VectorUpsertResult indicating success/failure.
        """
        if len(ids) != len(texts):
            raise ValueError("ids and texts must have the same length")

        if metadata and len(metadata) != len(ids):
            raise ValueError("metadata must have the same length as ids")

        # Generate embeddings
        vectors = await self.embed_batch(texts)

        # Prepare metadata
        if metadata is None:
            metadata = [{} for _ in ids]

        # Add text to metadata for reference
        for i, text in enumerate(texts):
            metadata[i]["text"] = text[:1000]  # Limit text stored in metadata

        # Prepare vectors for upsert
        vectors_to_upsert = [
            {"id": id_, "values": vec, "metadata": meta}
            for id_, vec, meta in zip(ids, vectors, metadata, strict=False)
        ]

        results = []

        # Batch upsert (Pinecone has limits)
        for i in range(0, len(vectors_to_upsert), self.BATCH_SIZE):
            batch = vectors_to_upsert[i : i + self.BATCH_SIZE]
            try:
                # Run in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda b: self.index.upsert(vectors=b, namespace=self.namespace),
                    batch,
                )
                for item in batch:
                    results.append(
                        VectorUpsertResult(id=item["id"], success=True)
                    )
                logger.debug(f"Upserted batch of {len(batch)} vectors")
            except Exception as e:
                logger.error(f"Failed to upsert batch: {e}")
                for item in batch:
                    results.append(
                        VectorUpsertResult(id=item["id"], success=False, error=str(e))
                    )

        return results

    async def upsert_single(
        self,
        id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> VectorUpsertResult:
        """Upsert a single vector.

        Args:
            id: Unique ID for the vector.
            text: Text to embed and store.
            metadata: Optional metadata dict.

        Returns:
            VectorUpsertResult indicating success/failure.
        """
        results = await self.upsert_vectors(
            ids=[id], texts=[text], metadata=[metadata] if metadata else None
        )
        return results[0] if results else VectorUpsertResult(id=id, success=False)

    async def query_similar(
        self,
        query_text: str,
        top_k: int = DEFAULT_TOP_K,
        filter_dict: dict[str, Any] | None = None,
        include_metadata: bool = True,
    ) -> list[VectorSearchResult]:
        """Query for similar vectors using semantic similarity.

        Args:
            query_text: Text to search for similar content.
            top_k: Number of results to return.
            filter_dict: Optional metadata filters.
            include_metadata: Whether to include metadata in results.

        Returns:
            List of VectorSearchResult ordered by similarity score.
        """
        # Generate query embedding
        query_vector = await self.embed_text(query_text)

        # Build query kwargs
        query_kwargs: dict[str, Any] = {
            "vector": query_vector,
            "top_k": top_k,
            "namespace": self.namespace,
            "include_metadata": include_metadata,
        }

        if filter_dict:
            query_kwargs["filter"] = filter_dict

        try:
            # Run in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: self.index.query(**query_kwargs)
            )

            results = []
            for match in response.matches:
                results.append(
                    VectorSearchResult(
                        id=match.id,
                        score=match.score,
                        metadata=dict(match.metadata) if match.metadata else {},
                    )
                )

            logger.debug(f"Found {len(results)} similar vectors")
            return results

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []

    async def query_by_vector(
        self,
        vector: list[float],
        top_k: int = DEFAULT_TOP_K,
        filter_dict: dict[str, Any] | None = None,
        include_metadata: bool = True,
    ) -> list[VectorSearchResult]:
        """Query using a pre-computed vector.

        Args:
            vector: Pre-computed embedding vector.
            top_k: Number of results to return.
            filter_dict: Optional metadata filters.
            include_metadata: Whether to include metadata in results.

        Returns:
            List of VectorSearchResult ordered by similarity score.
        """
        query_kwargs: dict[str, Any] = {
            "vector": vector,
            "top_k": top_k,
            "namespace": self.namespace,
            "include_metadata": include_metadata,
        }

        if filter_dict:
            query_kwargs["filter"] = filter_dict

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: self.index.query(**query_kwargs)
            )

            return [
                VectorSearchResult(
                    id=match.id,
                    score=match.score,
                    metadata=dict(match.metadata) if match.metadata else {},
                )
                for match in response.matches
            ]

        except Exception as e:
            logger.error(f"Query by vector failed: {e}")
            return []

    async def delete_vectors(self, ids: list[str]) -> bool:
        """Delete vectors by IDs.

        Args:
            ids: List of vector IDs to delete.

        Returns:
            True if deletion was successful.
        """
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.index.delete(ids=ids, namespace=self.namespace),
            )
            logger.info(f"Deleted {len(ids)} vectors")
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False

    async def delete_all(self) -> bool:
        """Delete all vectors in the current namespace.

        Returns:
            True if deletion was successful.
        """
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.index.delete(delete_all=True, namespace=self.namespace),
            )
            logger.info(f"Deleted all vectors in namespace '{self.namespace}'")
            return True
        except Exception as e:
            logger.error(f"Delete all failed: {e}")
            return False

    async def fetch_vectors(self, ids: list[str]) -> dict[str, dict[str, Any]]:
        """Fetch vectors by IDs.

        Args:
            ids: List of vector IDs to fetch.

        Returns:
            Dictionary mapping ID to vector data (values and metadata).
        """
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.index.fetch(ids=ids, namespace=self.namespace),
            )

            results = {}
            if response.vectors:
                for vid, data in response.vectors.items():
                    results[vid] = {
                        "values": list(data.values) if data.values else [],
                        "metadata": dict(data.metadata) if data.metadata else {},
                    }
            return results

        except Exception as e:
            logger.error(f"Fetch failed: {e}")
            return {}

    async def get_index_stats(self) -> dict[str, Any]:
        """Get statistics about the index.

        Returns:
            Dictionary with index statistics.
        """
        try:
            loop = asyncio.get_event_loop()
            stats = await loop.run_in_executor(
                None,
                lambda: self.index.describe_index_stats(),
            )
            return {
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "total_vector_count": stats.total_vector_count,
                "namespaces": dict(stats.namespaces) if stats.namespaces else {},
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    def set_namespace(self, namespace: str) -> None:
        """Change the current namespace.

        Args:
            namespace: New namespace to use.
        """
        self.namespace = namespace
        logger.info(f"Switched to namespace: {namespace}")

    def close(self) -> None:
        """Close the Pinecone client connection."""
        self._index = None
        self._pc = None
        logger.info("Pinecone client closed")
