"""Simple file-based memory implementation."""

import json
import logging
from pathlib import Path
from typing import Any

from src.novel_agent.memory.base import BaseMemory, MemoryEntry

logger = logging.getLogger(__name__)


class FileMemory(BaseMemory):
    """Simple file-based memory system for persistent storage.

    Stores memory entries as JSON files in a directory structure.
    Suitable for local development and simple use cases.
    """

    def __init__(
        self,
        base_path: str | Path | None = None,
        namespace: str = "default",
    ) -> None:
        """Initialize file-based memory.

        Args:
            base_path: Base directory for memory storage. Defaults to data/memory.
            namespace: Namespace for isolating different novels/projects.
        """
        super().__init__(namespace=namespace)
        self.base_path = Path(base_path) if base_path else Path("data/memory")
        self.namespace_path = self.base_path / namespace
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure memory directories exist."""
        self.namespace_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"FileMemory initialized at {self.namespace_path}")

    def _get_entry_path(self, key: str) -> Path:
        """Get the file path for a memory entry.

        Args:
            key: Memory key (can include / for subdirectories).

        Returns:
            Path to the entry file.
        """
        # Sanitize key for filesystem
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.namespace_path / f"{safe_key}.json"

    async def store(
        self, key: str, value: Any, metadata: dict[str, Any] | None = None
    ) -> None:
        """Store a value in memory.

        Args:
            key: Unique key for the entry.
            value: Value to store.
            metadata: Optional metadata.
        """
        entry = MemoryEntry(
            key=key,
            value=value,
            metadata=metadata or {},
        )
        entry_path = self._get_entry_path(key)

        with open(entry_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "key": entry.key,
                    "value": entry.value,
                    "metadata": entry.metadata,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        logger.debug(f"Stored memory entry: {key}")

    async def retrieve(self, key: str) -> MemoryEntry | None:
        """Retrieve a value from memory.

        Args:
            key: Unique key for the entry.

        Returns:
            MemoryEntry if found, None otherwise.
        """
        entry_path = self._get_entry_path(key)

        if not entry_path.exists():
            return None

        try:
            with open(entry_path, encoding="utf-8") as f:
                data = json.load(f)
            return MemoryEntry(
                key=data["key"],
                value=data["value"],
                metadata=data.get("metadata", {}),
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to load memory entry {key}: {e}")
            return None

    async def delete(self, key: str) -> bool:
        """Delete a value from memory.

        Args:
            key: Unique key for the entry.

        Returns:
            True if deleted, False if not found.
        """
        entry_path = self._get_entry_path(key)

        if not entry_path.exists():
            return False

        entry_path.unlink()
        logger.debug(f"Deleted memory entry: {key}")
        return True

    async def list_keys(self, prefix: str | None = None) -> list[str]:
        """List all keys in memory.

        Args:
            prefix: Optional prefix to filter keys.

        Returns:
            List of keys.
        """
        keys = []
        for entry_file in self.namespace_path.glob("*.json"):
            try:
                with open(entry_file, encoding="utf-8") as f:
                    data = json.load(f)
                key = data.get("key", entry_file.stem)
                if prefix is None or key.startswith(prefix):
                    keys.append(key)
            except (json.JSONDecodeError, KeyError):
                # Skip corrupted entries
                continue
        return keys

    async def clear(self) -> None:
        """Clear all memory entries for this namespace."""
        for entry_file in self.namespace_path.glob("*.json"):
            entry_file.unlink()
        logger.info(f"Cleared all memory entries in namespace: {self.namespace}")