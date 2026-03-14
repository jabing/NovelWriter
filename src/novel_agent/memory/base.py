# src/memory/base.py
"""Base class for memory systems."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryEntry:
    """A single entry in memory."""
    key: str
    value: Any
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseMemory(ABC):
    """Abstract base class for memory systems.

    Memory systems store and retrieve context for agents, including:
    - Character profiles and development
    - Plot points and foreshadowing
    - World settings and rules

    Implementations can use various backends:
    - OpenViking (recommended)
    - Vector databases (Milvus, Chroma)
    - Simple file storage
    """

    def __init__(self, namespace: str = "default") -> None:
        """Initialize the memory system.

        Args:
            namespace: Namespace for isolating different novels/projects
        """
        self.namespace = namespace

    @abstractmethod
    async def store(self, key: str, value: Any, metadata: dict[str, Any] | None = None) -> None:
        """Store a value in memory.

        Args:
            key: Unique key for the entry
            value: Value to store
            metadata: Optional metadata
        """
        pass

    @abstractmethod
    async def retrieve(self, key: str) -> MemoryEntry | None:
        """Retrieve a value from memory.

        Args:
            key: Key to look up

        Returns:
            MemoryEntry if found, None otherwise
        """
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        """Search for relevant entries.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching entries
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete an entry from memory.

        Args:
            key: Key to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def list_keys(self, prefix: str = "") -> list[str]:
        """List all keys with optional prefix filter.

        Args:
            prefix: Prefix to filter keys

        Returns:
            List of matching keys
        """
        pass

    # Synchronous wrappers
    def store_sync(self, key: str, value: Any, metadata: dict[str, Any] | None = None) -> None:
        """Synchronous wrapper for store()."""
        import asyncio
        asyncio.run(self.store(key, value, metadata))

    def retrieve_sync(self, key: str) -> MemoryEntry | None:
        """Synchronous wrapper for retrieve()."""
        import asyncio
        return asyncio.run(self.retrieve(key))

    def search_sync(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        """Synchronous wrapper for search()."""
        import asyncio
        return asyncio.run(self.search(query, limit))
