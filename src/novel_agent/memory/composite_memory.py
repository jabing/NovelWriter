# src/memory/composite_memory.py
"""Composite memory system that routes to specialized memory implementations."""

import logging
from typing import Any

from src.novel_agent.memory.base import BaseMemory, MemoryEntry
from src.novel_agent.memory.character_memory import CharacterMemory
from src.novel_agent.memory.memsearch_adapter import ContextLevel
from src.novel_agent.memory.plot_memory import PlotMemory
from src.novel_agent.memory.world_memory import WorldMemory

logger = logging.getLogger(__name__)


class CompositeMemory(BaseMemory):
    """Composite memory that routes to specialized memory implementations.

    Routes calls based on key patterns:
    - /memory/characters/* → CharacterMemory
    - /memory/plot/* → PlotMemory
    - /memory/world/* → WorldMemory

    Provides backward compatibility with existing agents while enabling
    specialized semantic search capabilities.
    """

    def __init__(
        self,
        base_path: str | None = None,
        namespace: str = "default",
        embedding_provider: str | None = None,
        milvus_uri: str | None = None,
    ) -> None:
        """Initialize composite memory with specialized components.

        Args:
            base_path: Base path for memory storage
            namespace: Namespace for isolating different novels/projects
            embedding_provider: Embedding provider for semantic search
            milvus_uri: Milvus URI for vector storage
        """
        super().__init__(namespace=namespace)

        # Initialize specialized memory instances
        self.character_memory = CharacterMemory(
            base_path=base_path,
            namespace=namespace,
            embedding_provider=embedding_provider,
            milvus_uri=milvus_uri,
            collection=f"{namespace}_character_memory",
        )

        self.plot_memory = PlotMemory(
            base_path=base_path,
            namespace=namespace,
            embedding_provider=embedding_provider,
            milvus_uri=milvus_uri,
            collection=f"{namespace}_plot_memory",
        )

        self.world_memory = WorldMemory(
            base_path=base_path,
            namespace=namespace,
            embedding_provider=embedding_provider,
            milvus_uri=milvus_uri,
            collection=f"{namespace}_world_memory",
        )

        logger.info(f"CompositeMemory initialized for namespace '{namespace}'")

    def _route_key(self, key: str) -> tuple[BaseMemory, str]:
        """Route a key to the appropriate specialized memory.

        Args:
            key: Memory key

        Returns:
            Tuple of (memory_instance, normalized_key)
        """
        # Normalize key
        normalized = key.lstrip("/")

        # Route based on patterns
        if normalized.startswith("memory/characters/"):
            return self.character_memory, key
        elif normalized.startswith("memory/plot/"):
            return self.plot_memory, key
        elif normalized.startswith("memory/world/"):
            return self.world_memory, key
        else:
            # Default to character memory for backward compatibility
            # (most agents use character-related keys)
            return self.character_memory, key

    async def store(self, key: str, value: Any, metadata: dict[str, Any] | None = None) -> None:
        """Store a value in the appropriate specialized memory.

        Args:
            key: Unique key for the entry
            value: Value to store
            metadata: Optional metadata
        """
        memory, routed_key = self._route_key(key)
        await memory.store(routed_key, value, metadata)
        logger.debug(f"CompositeMemory stored {key} → {memory.__class__.__name__}")

    async def retrieve(self, key: str) -> MemoryEntry | None:
        """Retrieve a value from the appropriate specialized memory.

        Args:
            key: Key to look up

        Returns:
            MemoryEntry if found, None otherwise
        """
        memory, routed_key = self._route_key(key)
        entry = await memory.retrieve(routed_key)
        if entry:
            logger.debug(f"CompositeMemory retrieved {key} from {memory.__class__.__name__}")
        return entry

    async def search(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        """Search across all specialized memories.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching entries from all memory systems
        """
        # Search each memory system and combine results
        all_results: list[MemoryEntry] = []

        # Search character memory
        char_results = await self.character_memory.search(query, limit=limit)
        all_results.extend(char_results)

        # Search plot memory
        plot_results = await self.plot_memory.search(query, limit=limit)
        all_results.extend(plot_results)

        # Search world memory
        world_results = await self.world_memory.search(query, limit=limit)
        all_results.extend(world_results)

        # Deduplicate by key and sort by relevance score
        seen = set()
        deduped = []
        for entry in all_results:
            if entry.key not in seen:
                seen.add(entry.key)
                deduped.append(entry)

        # Sort by score if available
        deduped.sort(
            key=lambda e: e.metadata.get("score", 0) if e.metadata else 0,
            reverse=True,
        )

        # Return top results
        result = deduped[:limit]
        logger.debug(f"CompositeMemory search '{query}' found {len(result)} results")
        return result

    async def delete(self, key: str) -> bool:
        """Delete an entry from the appropriate specialized memory.

        Args:
            key: Key to delete

        Returns:
            True if deleted, False if not found
        """
        memory, routed_key = self._route_key(key)
        deleted = await memory.delete(routed_key)
        if deleted:
            logger.debug(f"CompositeMemory deleted {key} from {memory.__class__.__name__}")
        return deleted

    async def list_keys(self, prefix: str = "") -> list[str]:
        """List all keys from all specialized memories.

        Args:
            prefix: Prefix to filter keys

        Returns:
            List of matching keys from all memory systems
        """
        all_keys: list[str] = []

        # Get keys from each memory system
        char_keys = await self.character_memory.list_keys(prefix)
        all_keys.extend(char_keys)

        plot_keys = await self.plot_memory.list_keys(prefix)
        all_keys.extend(plot_keys)

        world_keys = await self.world_memory.list_keys(prefix)
        all_keys.extend(world_keys)

        # Deduplicate and sort
        result = sorted(set(all_keys))
        logger.debug(f"CompositeMemory list_keys with prefix '{prefix}' found {len(result)} keys")
        return result

    # Convenience methods for accessing specialized memories directly
    @property
    def characters(self) -> CharacterMemory:
        """Direct access to character memory."""
        return self.character_memory

    @property
    def plot(self) -> PlotMemory:
        """Direct access to plot memory."""
        return self.plot_memory

    @property
    def world(self) -> WorldMemory:
        """Direct access to world memory."""
        return self.world_memory

    async def get_context(
        self,
        level: str = ContextLevel.L0,
        context_keys: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get context from all specialized memories.

        Args:
            level: Context level (L0/L1/L2)
            context_keys: Optional specific keys to retrieve

        Returns:
            Context dictionary
        """
        context = {}
        if context_keys:
            for key in context_keys:
                entry = await self.retrieve(key)
                if entry:
                    context[key] = entry.value
        else:
            # Use composite search with tiered queries
            if level == ContextLevel.L0:
                queries = ["main character protagonist", "current plot"]
                limit = 5
            elif level == ContextLevel.L1:
                queries = ["characters plot world", "supporting"]
                limit = 15
            else:
                queries = ["all characters plot world settings"]
                limit = 50
            seen = set()
            for q in queries:
                for entry in await self.search(q, limit=limit):
                    if entry.key not in seen:
                        context[entry.key] = entry.value
                        seen.add(entry.key)
        return context

    async def retrieve_batch(self, keys: list[str]) -> dict[str, MemoryEntry]:
        """Retrieve multiple entries in batch.

        Args:
            keys: List of keys to retrieve

        Returns:
            Dictionary mapping keys to MemoryEntry objects
        """
        results = {}
        for key in keys:
            entry = await self.retrieve(key)
            if entry:
                results[key] = entry
        return results

    def close(self) -> None:
        """Close all underlying adapters."""
        self.character_memory.close()
        self.plot_memory.close()
        self.world_memory.close()
        logger.debug("CompositeMemory closed all adapters")
