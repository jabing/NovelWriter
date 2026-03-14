# src/db/vector_store_factory.py
"""Vector store factory for creating and managing vector database clients.

Provides a unified interface for switching between different vector store
implementations (Chroma, Pinecone) with configuration-based instantiation.
"""

import logging
from typing import Protocol

from src.novel_agent.db.chroma_client import ChromaVectorStore
from src.novel_agent.db.pinecone_client import VectorSearchResult, VectorStore

logger = logging.getLogger(__name__)


class VectorStoreInterface(Protocol):
    """Protocol defining the interface for vector store implementations.

    All vector store implementations must implement these methods to ensure
    compatibility and easy switching between backends.
    """

    async def upsert_vectors(
        self,
        ids: list[str],
        texts: list[str],
        metadata: list[dict] | None = None,
    ) -> bool | list[dict]:
        """Upsert vectors to the vector store.

        Args:
            ids: List of unique IDs for each vector.
            texts: List of texts to embed and store.
            metadata: Optional list of metadata dicts for each vector.

        Returns:
            True/bool for Chroma, list of result dicts for Pinecone.
        """
        ...

    async def query_similar(
        self,
        query_text: str,
        n_results: int = 10,
        where: dict | None = None,
        include_metadata: bool = True,
    ) -> list[dict]:
        """Query for similar vectors using semantic similarity.

        Args:
            query_text: Text to search for similar content.
            n_results: Number of results to return.
            where: Optional metadata filters (Chroma uses 'where', Pinecone uses 'filter_dict').
            include_metadata: Whether to include metadata in results.

        Returns:
            List of result dicts with keys: id, text/metadata, distance/score.
        """
        ...

    async def delete_vectors(self, ids: list[str]) -> bool:
        """Delete vectors by IDs.

        Args:
            ids: List of vector IDs to delete.

        Returns:
            True if deletion was successful.
        """
        ...


class ChromaAdapter:
    """Adapter for ChromaVectorStore to match VectorStoreInterface.

    Wraps the Chroma implementation to provide a consistent interface.
    """

    def __init__(self, store: ChromaVectorStore) -> None:
        """Initialize the adapter with a ChromaVectorStore instance.

        Args:
            store: The ChromaVectorStore instance to wrap.
        """
        self._store = store

    async def upsert_vectors(
        self,
        ids: list[str],
        texts: list[str],
        metadata: list[dict] | None = None,
    ) -> bool:
        """Upsert vectors to the Chroma store.

        Args:
            ids: List of unique IDs for each vector.
            texts: List of texts to embed and store.
            metadata: Optional list of metadata dicts for each vector.

        Returns:
            True if upsert was successful.
        """
        return await self._store.upsert_vectors(ids, texts, metadatas=metadata)

    async def query_similar(
        self,
        query_text: str,
        n_results: int = 10,
        where: dict | None = None,
        include_metadata: bool = True,  # noqa: ARG002
    ) -> list[dict]:
        """Query for similar vectors using semantic similarity.

        Args:
            query_text: Text to search for similar content.
            n_results: Number of results to return.
            where: Optional metadata filters.
            include_metadata: Whether to include metadata in results (ignored, always included).

        Returns:
            List of result dicts with keys: id, text, metadata, distance.
        """
        return await self._store.query_similar(
            query_text=query_text,
            n_results=n_results,
            where=where,
        )

    async def delete_vectors(self, ids: list[str]) -> bool:
        """Delete vectors by IDs.

        Args:
            ids: List of vector IDs to delete.

        Returns:
            True if deletion was successful.
        """
        return await self._store.delete_vectors(ids)


class PineconeAdapter:
    """Adapter for VectorStore to match VectorStoreInterface.

    Wraps the Pinecone implementation to provide a consistent interface.
    """

    def __init__(self, store: VectorStore) -> None:
        """Initialize the adapter with a VectorStore instance.

        Args:
            store: The VectorStore instance to wrap.
        """
        self._store = store

    async def upsert_vectors(
        self,
        ids: list[str],
        texts: list[str],
        metadata: list[dict] | None = None,
    ) -> list[dict]:
        """Upsert vectors to the Pinecone store.

        Args:
            ids: List of unique IDs for each vector.
            texts: List of texts to embed and store.
            metadata: Optional list of metadata dicts for each vector.

        Returns:
            List of result dicts with keys: id, success, error.
        """
        results = await self._store.upsert_vectors(ids, texts, metadata=metadata)
        return [
            {
                "id": r.id,
                "success": r.success,
                "error": r.error,
            }
            for r in results
        ]

    async def query_similar(
        self,
        query_text: str,
        n_results: int = 10,
        where: dict | None = None,  # noqa: ARG002
        include_metadata: bool = True,
    ) -> list[dict]:
        """Query for similar vectors using semantic similarity.

        Args:
            query_text: Text to search for similar content.
            n_results: Number of results to return.
            where: Optional metadata filters (Pinecone uses filter_dict internally).
            include_metadata: Whether to include metadata in results.

        Returns:
            List of result dicts with keys: id, score, metadata.
        """
        results: list[VectorSearchResult] = await self._store.query_similar(
            query_text=query_text,
            top_k=n_results,
            filter_dict=where,
            include_metadata=include_metadata,
        )
        return [
            {
                "id": r.id,
                "score": r.score,
                "metadata": r.metadata,
            }
            for r in results
        ]

    async def delete_vectors(self, ids: list[str]) -> bool:
        """Delete vectors by IDs.

        Args:
            ids: List of vector IDs to delete.

        Returns:
            True if deletion was successful.
        """
        return await self._store.delete_vectors(ids)


class VectorStoreFactory:
    """Factory for creating vector store instances.

    Supports creating different vector store implementations based on
    configuration or runtime selection.
    """

    @staticmethod
    def get_vector_store(
        store_type: str = "chroma",
        **kwargs,
    ) -> VectorStoreInterface:
        """Create a vector store instance based on type.

        Args:
            store_type: Type of vector store to create. Supported values:
                - "chroma": Local Chroma vector store (default)
                - "pinecone": Cloud Pinecone vector store
            **kwargs: Additional configuration parameters passed to the
                      vector store constructor.

        Returns:
            VectorStoreInterface instance.

        Raises:
            ValueError: If store_type is not supported.
            ValueError: If required configuration is missing (e.g., API key for Pinecone).

        Examples:
            >>> # Create Chroma store with default settings
            >>> store = VectorStoreFactory.get_vector_store("chroma")

            >>> # Create Pinecone store with API key
            >>> store = VectorStoreFactory.get_vector_store(
            ...     "pinecone",
            ...     api_key="your-api-key",
            ...     index_name="novel-facts"
            ... )
        """
        logger.info(f"Creating vector store of type: {store_type}")

        if store_type == "chroma":
            return VectorStoreFactory._create_chroma_store(**kwargs)
        elif store_type == "pinecone":
            return VectorStoreFactory._create_pinecone_store(**kwargs)
        else:
            supported = ["chroma", "pinecone"]
            raise ValueError(
                f"Unsupported vector store type: {store_type}. "
                f"Supported types: {', '.join(supported)}"
            )

    @staticmethod
    def _create_chroma_store(**kwargs) -> VectorStoreInterface:
        """Create a Chroma vector store instance wrapped in adapter.

        Args:
            **kwargs: Configuration parameters for ChromaVectorStore:
                - persist_path: Path to store Chroma database (default: "data/chroma")
                - collection_name: Name of the collection (default: "novel-facts")
                - embedding_function: Custom embedding function (optional)

        Returns:
            ChromaAdapter instance implementing VectorStoreInterface.
        """
        persist_path = kwargs.get("persist_path", ChromaVectorStore.DEFAULT_PATH)
        collection_name = kwargs.get(
            "collection_name", ChromaVectorStore.DEFAULT_COLLECTION
        )
        embedding_function = kwargs.get("embedding_function")

        logger.info(
            f"Initializing Chroma store at {persist_path}, "
            f"collection: {collection_name}"
        )

        store = ChromaVectorStore(
            persist_path=persist_path,
            collection_name=collection_name,
            embedding_function=embedding_function,
        )
        return ChromaAdapter(store)

    @staticmethod
    def _create_pinecone_store(**kwargs) -> VectorStoreInterface:
        """Create a Pinecone vector store instance wrapped in adapter.

        Args:
            **kwargs: Configuration parameters for VectorStore:
                - api_key: Pinecone API key (required)
                - index_name: Name of the Pinecone index (default: "novel-facts")
                - namespace: Namespace for isolation (default: "default")
                - embedding_generator: Optional embedding generator instance
                - environment: Cloud region (default: "us-east-1", for legacy compat)

        Returns:
            PineconeAdapter instance implementing VectorStoreInterface.

        Raises:
            ValueError: If api_key is not provided.
        """
        api_key = kwargs.get("api_key")
        if not api_key:
            raise ValueError(
                "Pinecone API key is required. "
                "Provide it via 'api_key' parameter or set PINECONE_API_KEY environment variable."
            )

        index_name = kwargs.get("index_name", VectorStore.DEFAULT_INDEX_NAME)
        namespace = kwargs.get("namespace", VectorStore.DEFAULT_NAMESPACE)
        embedding_generator = kwargs.get("embedding_generator")
        environment = kwargs.get("environment", "us-east-1")

        logger.info(
            f"Initializing Pinecone store with index: {index_name}, "
            f"namespace: {namespace}"
        )

        store = VectorStore(
            api_key=api_key,
            index_name=index_name,
            namespace=namespace,
            embedding_generator=embedding_generator,
            environment=environment,
        )
        return PineconeAdapter(store)

    @staticmethod
    def get_default_store_type() -> str:
        """Get the default vector store type from environment or settings.

        Checks for VECTOR_STORE_TYPE environment variable, defaults to 'chroma'.

        Returns:
            Default vector store type ('chroma' or 'pinecone').
        """
        import os

        store_type = os.getenv("VECTOR_STORE_TYPE", "chroma").lower()
        if store_type not in ["chroma", "pinecone"]:
            logger.warning(
                f"Invalid VECTOR_STORE_TYPE '{store_type}', defaulting to 'chroma'"
            )
            store_type = "chroma"
        return store_type

    @staticmethod
    def create_default(**kwargs) -> VectorStoreInterface:
        """Create a vector store instance using default configuration.

        Uses VECTOR_STORE_TYPE environment variable to determine which
        store to create, defaults to 'chroma' if not set.

        Args:
            **kwargs: Additional configuration parameters.

        Returns:
            VectorStoreInterface instance.
        """
        store_type = VectorStoreFactory.get_default_store_type()
        logger.info(f"Creating default vector store: {store_type}")
        return VectorStoreFactory.get_vector_store(store_type, **kwargs)
