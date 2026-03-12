# src/db/embedding_generator.py
"""Text to vector embedding generation with caching."""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate text embeddings using sentence-transformers with local caching.

    Uses 'all-MiniLM-L6-v2' model by default - good balance of speed and quality.
    Produces 384-dimensional vectors suitable for semantic similarity search.
    """

    DEFAULT_MODEL = "all-MiniLM-L6-v2"
    DEFAULT_CACHE_DIR = "data/embedding_cache"
    VECTOR_DIMENSION = 384  # all-MiniLM-L6-v2 output dimension

    def __init__(
        self,
        model_name: str | None = None,
        cache_dir: str | None = None,
        enable_cache: bool = True,
    ) -> None:
        """Initialize the embedding generator.

        Args:
            model_name: Name of the sentence-transformer model to use.
                       Defaults to 'all-MiniLM-L6-v2'.
            cache_dir: Directory to store embedding cache. Defaults to
                      'data/embedding_cache'.
            enable_cache: Whether to enable local caching of embeddings.
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self.cache_dir = Path(cache_dir or self.DEFAULT_CACHE_DIR)
        self.enable_cache = enable_cache
        self._model: SentenceTransformer | None = None
        self._cache: dict[str, list[float]] = {}

        if self.enable_cache:
            self._ensure_cache_dir()
            self._load_cache()

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_file_path(self) -> Path:
        """Get the path to the cache file for current model."""
        safe_model_name = self.model_name.replace("/", "_")
        return self.cache_dir / f"{safe_model_name}_cache.json"

    def _load_cache(self) -> None:
        """Load cached embeddings from disk."""
        cache_file = self._get_cache_file_path()
        if cache_file.exists():
            try:
                with open(cache_file, encoding="utf-8") as f:
                    self._cache = json.load(f)
                logger.info(f"Loaded {len(self._cache)} cached embeddings")
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load embedding cache: {e}")
                self._cache = {}

    def _save_cache(self) -> None:
        """Save cached embeddings to disk."""
        if not self.enable_cache:
            return
        cache_file = self._get_cache_file_path()
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f)
            logger.debug(f"Saved {len(self._cache)} embeddings to cache")
        except OSError as e:
            logger.warning(f"Failed to save embedding cache: {e}")

    def _get_text_hash(self, text: str) -> str:
        """Generate a hash key for text content.

        Args:
            text: Text to hash.

        Returns:
            SHA256 hash of the text.
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load the sentence-transformer model."""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Checks cache first, computes embedding only if not cached.

        Args:
            text: Text to embed.

        Returns:
            List of floats representing the embedding vector.
        """
        if not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.VECTOR_DIMENSION

        text_hash = self._get_text_hash(text)

        # Check cache
        if self.enable_cache and text_hash in self._cache:
            logger.debug(f"Cache hit for text hash: {text_hash[:16]}...")
            return self._cache[text_hash]

        # Generate embedding
        embedding = self.model.encode(text, convert_to_numpy=True)
        vector = embedding.tolist()

        # Cache the result
        if self.enable_cache:
            self._cache[text_hash] = vector
            # Save cache periodically (every 100 new embeddings)
            if len(self._cache) % 100 == 0:
                self._save_cache()

        return vector

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        More efficient than calling embed_text multiple times
        as it batches the encoding operation.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []

        # Separate cached and uncached texts
        cached_results: dict[int, list[float]] = {}
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []

        if self.enable_cache:
            for i, text in enumerate(texts):
                if not text.strip():
                    cached_results[i] = [0.0] * self.VECTOR_DIMENSION
                else:
                    text_hash = self._get_text_hash(text)
                    if text_hash in self._cache:
                        cached_results[i] = self._cache[text_hash]
                    else:
                        uncached_indices.append(i)
                        uncached_texts.append(text)
        else:
            uncached_indices = list(range(len(texts)))
            uncached_texts = texts

        # Batch encode uncached texts
        if uncached_texts:
            embeddings = self.model.encode(uncached_texts, convert_to_numpy=True)
            for idx, embedding, text in zip(uncached_indices, embeddings, uncached_texts, strict=False):
                vector = embedding.tolist()
                cached_results[idx] = vector
                if self.enable_cache:
                    text_hash = self._get_text_hash(text)
                    self._cache[text_hash] = vector

            # Save cache if we added new embeddings
            if self.enable_cache and uncached_texts:
                self._save_cache()

        # Return in original order
        return [cached_results[i] for i in range(len(texts))]

    def get_vector_dimension(self) -> int:
        """Get the dimension of the embedding vectors.

        Returns:
            Number of dimensions in the embedding vectors.
        """
        return self.VECTOR_DIMENSION

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._cache.clear()
        if self.enable_cache:
            cache_file = self._get_cache_file_path()
            if cache_file.exists():
                cache_file.unlink()
        logger.info("Embedding cache cleared")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get statistics about the cache.

        Returns:
            Dictionary with cache statistics.
        """
        return {
            "cached_embeddings": len(self._cache),
            "cache_enabled": self.enable_cache,
            "cache_dir": str(self.cache_dir),
            "model_name": self.model_name,
            "vector_dimension": self.VECTOR_DIMENSION,
        }

    def __del__(self) -> None:
        """Save cache on object destruction."""
        if self.enable_cache and self._cache:
            self._save_cache()
