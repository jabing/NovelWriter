"""Simple JSON-based glossary manager without Milvus dependency.

Provides basic glossary term storage and semantic search using sentence embeddings.
This is a fallback for when Milvus is not available (e.g., Windows environments).
"""

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from src.memory.base import BaseMemory, MemoryEntry
from src.novel.glossary import GlossaryTerm, TermStatus, TermType

logger = logging.getLogger(__name__)


class SimpleGlossaryManager(BaseMemory):
    """Glossary manager using JSON file storage and local embeddings for semantic search.

    This implementation provides:
    - JSON file storage for glossary terms
    - Semantic search using sentence-transformers embeddings
    - Cosine similarity for ranking results
    - Basic CRUD operations compatible with GlossaryManager interface

    Limitations:
    - Slower for large datasets (>10k terms)
    - No advanced indexing like Milvus
    - In-memory search after loading all embeddings
    """

    DEFAULT_STORAGE_PATH = "data/glossary.json"

    def __init__(
        self,
        storage_path: str | None = None,
        namespace: str = "default",
        embedding_model: str = "all-MiniLM-L6-v2",
    ) -> None:
        """Initialize the simple glossary manager.

        Args:
            storage_path: Path to JSON storage file
            namespace: Namespace for isolating glossaries
            embedding_model: Sentence transformer model name
        """
        super().__init__(namespace=namespace)
        self.storage_path = Path(storage_path or self.DEFAULT_STORAGE_PATH)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Load or initialize storage
        self._data = self._load_data()

        # Initialize embedding model (lazy load)
        self._embedding_model_name = embedding_model
        self._embedding_model = None

        logger.info(f"SimpleGlossaryManager initialized for namespace '{namespace}'")

    def _load_data(self) -> dict:
        """Load glossary data from JSON file."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load glossary data: {e}. Starting fresh.")

        # Default structure
        return {
            "terms": [],  # List of term objects
            "embeddings": {},  # Mapping term_id -> embedding vector
            "namespace": self.namespace,
            "version": "1.0",
        }

    def _save_data(self) -> None:
        """Save glossary data to JSON file."""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            logger.error(f"Failed to save glossary data: {e}")

    def _get_embedding_model(self):
        """Lazy load the sentence transformer model."""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._embedding_model = SentenceTransformer(self._embedding_model_name)
                logger.info(f"Loaded embedding model: {self._embedding_model_name}")
            except ImportError as e:
                logger.error(
                    f"Failed to load sentence-transformers: {e}. Semantic search will be limited."
                )
                self._embedding_model = None
        return self._embedding_model

    def _compute_embedding(self, text: str) -> list[float]:
        """Compute embedding vector for text."""
        model = self._get_embedding_model()
        if model is None:
            # Fallback: return empty embedding (search will be keyword-based)
            return []

        try:
            embedding = model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.warning(f"Failed to compute embedding: {e}")
            return []

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0

        v1 = np.array(vec1)
        v2 = np.array(vec2)

        # Avoid division by zero
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(v1, v2) / (norm1 * norm2))

    # BaseMemory interface implementation
    async def store(self, key: str, value: Any, metadata: dict[str, Any] | None = None) -> None:
        """Store a glossary term.

        Args:
            key: Term identifier (e.g., 'aethelgard')
            value: GlossaryTerm or dictionary
            metadata: Optional metadata
        """
        # Normalize key
        if key.startswith("/"):
            key = key[1:]

        # Convert GlossaryTerm to dict if needed
        if isinstance(value, GlossaryTerm):
            term_dict = asdict(value)
            term_dict["_type"] = "GlossaryTerm"
            term_id = f"terms/{value.term.lower().replace(' ', '_')}"
        else:
            term_dict = value
            term_id = key

        # Store term
        self._data["terms"].append(
            {
                "id": term_id,
                "key": key,
                "value": term_dict,
                "metadata": metadata or {},
                "namespace": self.namespace,
            }
        )

        # Compute and store embedding if possible
        if isinstance(value, GlossaryTerm):
            text_for_embedding = f"{value.term}: {value.definition}"
        else:
            text_for_embedding = str(value)

        embedding = self._compute_embedding(text_for_embedding)
        if embedding:
            self._data["embeddings"][term_id] = embedding

        self._save_data()
        logger.debug(f"Stored glossary term: {key}")

    async def retrieve(self, key: str) -> MemoryEntry | None:
        """Retrieve a glossary term.

        Args:
            key: Term identifier

        Returns:
            MemoryEntry if found, None otherwise
        """
        if key.startswith("/"):
            key = key[1:]

        for item in self._data["terms"]:
            if item["key"] == key:
                value = item["value"]
                # Convert back to GlossaryTerm if needed
                if isinstance(value, dict) and value.get("_type") == "GlossaryTerm":
                    term_data = {k: v for k, v in value.items() if k != "_type"}
                    try:
                        value = GlossaryTerm.from_dict(term_data)
                    except Exception as e:
                        logger.warning(f"Failed to reconstruct GlossaryTerm: {e}")

                return MemoryEntry(
                    key=key,
                    value=value,
                    metadata=item.get("metadata", {}),
                )

        return None

    async def search(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        """Search for glossary terms by semantic similarity.

        Args:
            query: Natural language query
            limit: Maximum results

        Returns:
            List of matching glossary entries
        """
        # Compute query embedding
        query_embedding = self._compute_embedding(query)

        # If no embedding model, fall back to keyword search
        if not query_embedding:
            return await self._keyword_search(query, limit)

        # Compute similarity scores
        scored_items = []
        for item in self._data["terms"]:
            term_id = item["id"]
            term_embedding = self._data["embeddings"].get(term_id)

            if not term_embedding:
                # No embedding for this term, skip semantic ranking
                continue

            similarity = self._cosine_similarity(query_embedding, term_embedding)

            # Extract value
            value = item["value"]
            if isinstance(value, dict) and value.get("_type") == "GlossaryTerm":
                term_data = {k: v for k, v in value.items() if k != "_type"}
                try:
                    value = GlossaryTerm.from_dict(term_data)
                except Exception as e:
                    logger.warning(f"Failed to reconstruct GlossaryTerm: {e}")

            scored_items.append(
                (
                    similarity,
                    MemoryEntry(
                        key=item["key"],
                        value=value,
                        metadata={**item.get("metadata", {}), "score": similarity},
                    ),
                )
            )

        # Sort by similarity (descending)
        scored_items.sort(key=lambda x: x[0], reverse=True)

        # Return top results
        return [item[1] for item in scored_items[:limit]]

    async def _keyword_search(self, query: str, limit: int) -> list[MemoryEntry]:
        """Fallback keyword search when embeddings are not available.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching entries
        """
        query_lower = query.lower()
        matches = []

        for item in self._data["terms"]:
            value = item["value"]
            text_to_search = ""

            if isinstance(value, dict):
                # Extract relevant fields
                if value.get("_type") == "GlossaryTerm":
                    text_to_search = f"{value.get('term', '')} {value.get('definition', '')} {value.get('notes', '')}"
                else:
                    text_to_search = str(value)
            else:
                text_to_search = str(value)

            if query_lower in text_to_search.lower():
                # Convert back to GlossaryTerm if needed
                if isinstance(value, dict) and value.get("_type") == "GlossaryTerm":
                    term_data = {k: v for k, v in value.items() if k != "_type"}
                    try:
                        value = GlossaryTerm.from_dict(term_data)
                    except Exception as e:
                        logger.warning(f"Failed to reconstruct GlossaryTerm: {e}")

                matches.append(
                    MemoryEntry(
                        key=item["key"],
                        value=value,
                        metadata={**item.get("metadata", {}), "score": 0.5},
                    )
                )

        return matches[:limit]

    async def delete(self, key: str) -> bool:
        """Delete a glossary term.

        Args:
            key: Term identifier

        Returns:
            True if deleted, False if not found
        """
        if key.startswith("/"):
            key = key[1:]

        original_count = len(self._data["terms"])

        # Remove term
        self._data["terms"] = [item for item in self._data["terms"] if item["key"] != key]

        # Remove embedding if exists
        term_id = f"terms/{key.lower().replace(' ', '_')}"
        if term_id in self._data["embeddings"]:
            del self._data["embeddings"][term_id]

        if len(self._data["terms"]) < original_count:
            self._save_data()
            logger.debug(f"Deleted glossary term: {key}")
            return True

        return False

    async def list_keys(self, prefix: str = "") -> list[str]:
        """List all glossary keys.

        Args:
            prefix: Optional prefix filter

        Returns:
            List of keys
        """
        all_keys = [item["key"] for item in self._data["terms"]]

        if prefix:
            all_keys = [key for key in all_keys if key.startswith(prefix)]

        return sorted(all_keys)

    # Glossary-specific methods (compatible with GlossaryManager interface)
    async def store_term(self, term: GlossaryTerm) -> None:
        """Store a glossary term.

        Args:
            term: GlossaryTerm instance
        """
        key = f"terms/{term.term.lower().replace(' ', '_')}"
        metadata = {
            "type": term.type.value,
            "status": term.status.value,
            "aliases": term.aliases,
        }
        await self.store(key, term, metadata)

    async def retrieve_term(self, term: str) -> GlossaryTerm | None:
        """Retrieve a glossary term by name.

        Args:
            term: Term name

        Returns:
            GlossaryTerm if found, None otherwise
        """
        key = f"terms/{term.lower().replace(' ', '_')}"
        entry = await self.retrieve(key)

        if entry and entry.value:
            if isinstance(entry.value, GlossaryTerm):
                return entry.value
            elif isinstance(entry.value, dict) and entry.value.get("term"):
                try:
                    return GlossaryTerm.from_dict(entry.value)
                except Exception as e:
                    logger.warning(f"Failed to parse glossary term {term}: {e}")

        return None

    async def search_terms(
        self,
        query: str,
        term_type: TermType | None = None,
        status: TermStatus | None = None,
        limit: int = 20,
    ) -> list[GlossaryTerm]:
        """Search glossary terms with filters.

        Args:
            query: Search query
            term_type: Optional type filter
            status: Optional status filter
            limit: Maximum results

        Returns:
            List of matching GlossaryTerm instances
        """
        entries = await self.search(query, limit=limit)
        terms = []

        for entry in entries:
            if not isinstance(entry.value, GlossaryTerm):
                continue

            term = entry.value
            if term_type and term.type != term_type:
                continue
            if status and term.status != status:
                continue

            terms.append(term)

        return terms

    async def get_all_terms(
        self,
        term_type: TermType | None = None,
        status: TermStatus | None = None,
    ) -> list[GlossaryTerm]:
        """Get all glossary terms with optional filters.

        Args:
            term_type: Optional type filter
            status: Optional status filter

        Returns:
            List of GlossaryTerm instances
        """
        terms = []

        for item in self._data["terms"]:
            value = item["value"]
            if isinstance(value, dict) and value.get("_type") == "GlossaryTerm":
                try:
                    term = GlossaryTerm.from_dict({k: v for k, v in value.items() if k != "_type"})
                except Exception as e:
                    logger.warning(f"Failed to parse glossary term: {e}")
                    continue

                if term_type and term.type != term_type:
                    continue
                if status and term.status != status:
                    continue

                terms.append(term)

        return terms

    def close(self) -> None:
        """Close underlying resources."""
        # Nothing to close for JSON storage
        pass
