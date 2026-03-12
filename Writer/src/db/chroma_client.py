"""Chroma vector database client for semantic similarity search."""

import asyncio
import logging
from typing import Any

import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class ChineseEmbeddingFunction(EmbeddingFunction):
    """Support Chinese embedding function.

    Uses sentence-transformers for multilingual text embeddings.
    Implements model caching to avoid redundant loading.

    Note:
        First model load downloads ~100MB. Consider preloading for production.

    Attributes:
        model_id: The sentence-transformers model identifier.
        device: Device to run inference on (cpu/cuda).
    """

    # Model cache - avoid redundant loading across instances
    _model_cache: dict[str, SentenceTransformer] = {}

    def __init__(
        self,
        model_id: str = "shibing624/text2vec-base-multilingual",
        device: str = "cpu",
    ) -> None:
        """Initialize the embedding function.

        Args:
            model_id: Sentence-transformers model ID.
            device: Device for inference (cpu/cuda).
        """
        self.model_id = model_id
        self.device = device

        # Use cache to avoid redundant model loading
        if model_id not in self._model_cache:
            logger.info(f"Loading embedding model: {model_id}")
            self._model_cache[model_id] = SentenceTransformer(
                model_id, device=device
            )
        self._model = self._model_cache[model_id]

    def __call__(self, input: Documents) -> Embeddings:
        """Generate embeddings for input documents.

        Args:
            input: List of text documents to embed.

        Returns:
            List of embedding vectors.
        """
        embeddings = self._model.encode(
            input,
            normalize_embeddings=True,  # Normalize for better cosine similarity
            convert_to_numpy=True,
        )
        return embeddings.tolist()


class ChromaVectorStore:
    """Chroma vector storage client.

    Provides efficient local storage and retrieval of text embeddings for:
    - Fact retrieval and verification
    - Semantic similarity search
    - Hallucination detection support

    Compatible with Pinecone API for easy migration.

    Attributes:
        collection: Chroma collection instance.
    """

    DEFAULT_COLLECTION = "novel-facts"
    DEFAULT_PATH = "data/chroma"

    def __init__(
        self,
        persist_path: str = DEFAULT_PATH,
        collection_name: str = DEFAULT_COLLECTION,
        embedding_function: EmbeddingFunction | None = None,
    ) -> None:
        """Initialize the Chroma vector store.

        Args:
            persist_path: Path to store Chroma database.
            collection_name: Name of the collection.
            embedding_function: Custom embedding function. If None, uses
                               ChineseEmbeddingFunction.
        """
        self.client = chromadb.PersistentClient(path=persist_path)
        self.embedding_function = (
            embedding_function or ChineseEmbeddingFunction()
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"},
        )

    async def upsert_vectors(
        self,
        ids: list[str],
        texts: list[str],
        metadatas: list[dict] | None = None,
    ) -> bool:
        """Upsert vectors to the Chroma collection.

        Automatically generates embeddings from text and stores them
        with associated metadata.

        Args:
            ids: List of unique IDs for each vector.
            texts: List of texts to embed and store.
            metadatas: Optional list of metadata dicts for each vector.

        Returns:
            True if upsert was successful.
        """
        if len(ids) != len(texts):
            raise ValueError("ids and texts must have the same length")

        if metadatas and len(metadatas) != len(ids):
            raise ValueError("metadatas must have the same length as ids")

        # Run in thread pool since Chroma is synchronous
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.collection.upsert(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
            ),
        )
        logger.debug(f"Upserted {len(ids)} vectors")
        return True

    async def query_similar(
        self,
        query_text: str,
        n_results: int = 10,
        where: dict | None = None,
    ) -> list[dict]:
        """Query for similar vectors using semantic similarity.

        Args:
            query_text: Text to search for similar content.
            n_results: Number of results to return.
            where: Optional metadata filters.

        Returns:
            List of result dicts with keys: id, text, metadata, distance.
        """
        # Run in thread pool since Chroma is synchronous
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where,
            ),
        )

        formatted_results = self._format_results(results)
        logger.debug(f"Found {len(formatted_results)} similar vectors")
        return formatted_results

    async def delete_vectors(self, ids: list[str]) -> bool:
        """Delete vectors by IDs.

        Args:
            ids: List of vector IDs to delete.

        Returns:
            True if deletion was successful.
        """
        # Run in thread pool since Chroma is synchronous
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.collection.delete(ids=ids),
        )
        logger.info(f"Deleted {len(ids)} vectors")
        return True

    async def get_stats(self) -> dict[str, Any]:
        """Get statistics about the collection.

        Returns:
            Dictionary with collection statistics.
        """
        return {
            "count": self.collection.count(),
            "name": self.collection.name,
        }

    def _format_results(self, results: dict) -> list[dict]:
        """Format Chroma query results into standardized format.

        Args:
            results: Raw Chroma query results.

        Returns:
            List of formatted result dicts.
        """
        formatted = []
        if not results.get("ids") or not results["ids"][0]:
            return formatted

        for id_, doc, meta, dist in zip(
            results["ids"][0],
            results.get("documents", [[]])[0],
            results.get("metadatas", [[]])[0],
            results.get("distances", [[]])[0],
            strict=False,
        ):
            formatted.append(
                {
                    "id": id_,
                    "text": doc if doc is not None else "",
                    "metadata": meta if meta is not None else {},
                    "distance": dist if dist is not None else 0.0,
                }
            )
        return formatted
