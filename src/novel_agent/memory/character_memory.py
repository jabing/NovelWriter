# src/memory/character_memory.py
"""Character memory management with semantic search."""

import logging
from typing import Any

from src.novel_agent.memory.base import BaseMemory, MemoryEntry
from src.novel_agent.memory.memsearch_adapter import ContextLevel, MemSearchAdapter

logger = logging.getLogger(__name__)


class CharacterMemory(BaseMemory):
    """Manages character profile storage and retrieval with semantic search.

    Provides domain-specific methods for character management:
    - Store/retrieve character profiles with rich attributes
    - Track relationships and development arcs
    - Search characters by traits, role, appearance, etc.
    - Maintain consistency across the story
    """

    DEFAULT_CHARACTERS_DIR = "/memory/characters"

    def __init__(
        self,
        base_path: str | None = None,
        namespace: str = "default",
        embedding_provider: str | None = None,
        milvus_uri: str | None = None,
        collection: str = "character_memory",
    ) -> None:
        super().__init__(namespace=namespace)
        self._adapter = MemSearchAdapter(
            base_path=base_path,
            namespace=namespace,
            embedding_provider=embedding_provider,
            milvus_uri=milvus_uri,
            collection=collection,
        )
        logger.info(f"CharacterMemory initialized for namespace '{namespace}'")

    # BaseMemory abstract method implementations
    async def store(self, key: str, value: Any, metadata: dict[str, Any] | None = None) -> None:
        """Store a character profile.

        Args:
            key: Character ID (e.g., 'alice') or path (e.g., '/memory/characters/main/alice')
            value: Character profile dictionary
            metadata: Optional metadata including 'level' (L0/L1/L2)
        """
        # Ensure key is in character directory
        if not key.startswith(self.DEFAULT_CHARACTERS_DIR):
            key = f"{self.DEFAULT_CHARACTERS_DIR}/{key}"
        await self._adapter.store(key, value, metadata)

    async def retrieve(self, key: str) -> MemoryEntry | None:
        """Retrieve a character profile.

        Args:
            key: Character ID or path

        Returns:
            MemoryEntry if found, None otherwise
        """
        if not key.startswith(self.DEFAULT_CHARACTERS_DIR):
            key = f"{self.DEFAULT_CHARACTERS_DIR}/{key}"
        return await self._adapter.retrieve(key)

    async def search(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        """Search for characters by semantic similarity.

        Args:
            query: Natural language query (e.g., 'brave protagonist with scar')
            limit: Maximum results

        Returns:
            List of matching character entries
        """
        return await self._adapter.search(query, limit)

    async def delete(self, key: str) -> bool:
        """Delete a character profile.

        Args:
            key: Character ID or path

        Returns:
            True if deleted, False if not found
        """
        if not key.startswith(self.DEFAULT_CHARACTERS_DIR):
            key = f"{self.DEFAULT_CHARACTERS_DIR}/{key}"
        return await self._adapter.delete(key)

    async def list_keys(self, prefix: str = "") -> list[str]:
        """List all character keys.

        Args:
            prefix: Optional prefix filter

        Returns:
            List of keys
        """
        full_prefix = (
            f"{self.DEFAULT_CHARACTERS_DIR}/{prefix}" if prefix else self.DEFAULT_CHARACTERS_DIR
        )
        keys = await self._adapter.list_keys(full_prefix)
        # Strip the base path from keys
        stripped_keys = []
        for key in keys:
            if key.startswith(self.DEFAULT_CHARACTERS_DIR):
                stripped_keys.append(key[len(self.DEFAULT_CHARACTERS_DIR) + 1 :])
            else:
                stripped_keys.append(key)
        return stripped_keys

    # Domain-specific methods
    async def store_character(
        self,
        character_id: str,
        profile: dict[str, Any],
        is_main: bool = True,
        level: str = ContextLevel.L0,
    ) -> None:
        """Store a character profile with proper categorization.

        Args:
            character_id: Unique character identifier
            profile: Character profile dictionary
            is_main: Whether this is a main character
            level: Context level (L0/L1/L2)
        """
        category = "main" if is_main else "supporting"
        key = f"{category}/{character_id}"
        metadata = {"level": level, "category": category, "is_main": is_main}
        await self.store(key, profile, metadata)

    async def retrieve_character(self, character_id: str) -> dict[str, Any] | None:
        """Retrieve a character profile by ID.

        Args:
            character_id: Character identifier

        Returns:
            Character profile if found, None otherwise
        """
        # Try main then supporting
        for category in ["main", "supporting"]:
            entry = await self.retrieve(f"{category}/{character_id}")
            if entry and isinstance(entry.value, dict):
                return entry.value
        return None

    async def search_by_trait(
        self,
        trait: str,
        value: Any = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search characters by personality trait or appearance attribute.

        Args:
            trait: Trait name (e.g., 'brave', 'scar', 'green eyes')
            value: Optional specific value to match
            limit: Maximum results

        Returns:
            List of matching character profiles
        """
        # Use semantic search for flexible matching
        entries = await self.search(f"character with {trait}", limit=limit)
        results = []
        for entry in entries:
            if value is not None:
                # Check if value matches in personality traits or appearance
                char = entry.value
                matched = False
                # Check personality traits
                if isinstance(char.get("personality"), dict):
                    traits = char["personality"].get("traits", [])
                    if any(value.lower() in t.lower() for t in traits):
                        matched = True
                # Check appearance
                if isinstance(char.get("appearance"), dict):
                    for _attr, attr_value in char["appearance"].items():
                        if isinstance(attr_value, str) and value.lower() in attr_value.lower():
                            matched = True
                if matched:
                    results.append(char)
            else:
                results.append(entry.value)
        return results

    async def get_all_main_characters(self) -> list[dict[str, Any]]:
        """Get all main characters.

        Returns:
            List of main character profiles
        """
        keys = await self.list_keys("main/")
        characters = []
        for key in keys:
            entry = await self.retrieve(key)
            if entry:
                characters.append(entry.value)
        return characters

    async def get_all_supporting_characters(self) -> list[dict[str, Any]]:
        """Get all supporting characters.

        Returns:
            List of supporting character profiles
        """
        keys = await self.list_keys("supporting/")
        characters = []
        for key in keys:
            entry = await self.retrieve(key)
            if entry:
                characters.append(entry.value)
        return characters

    async def store_relationship(
        self,
        character1_id: str,
        character2_id: str,
        relationship: dict[str, Any],
    ) -> None:
        """Store relationship between two characters.

        Args:
            character1_id: First character ID
            character2_id: Second character ID
            relationship: Relationship data
        """
        key = f"relationships/{character1_id}/{character2_id}"
        metadata = {"type": "relationship"}
        await self.store(key, relationship, metadata)

    async def get_relationships(self, character_id: str) -> list[dict[str, Any]]:
        """Get all relationships for a character.

        Args:
            character_id: Character ID

        Returns:
            List of relationships
        """
        # Search for relationships involving this character
        entries = await self._adapter.search(f"relationship with {character_id}", limit=20)
        relationships = []
        for entry in entries:
            if "relationships/" in entry.key:
                relationships.append(entry.value)
        return relationships

    async def store_development_arc(
        self,
        character_id: str,
        arc: dict[str, Any],
    ) -> None:
        """Store character development arc.

        Args:
            character_id: Character ID
            arc: Development arc data
        """
        key = f"arcs/{character_id}"
        metadata = {"type": "development_arc"}
        await self.store(key, arc, metadata)

    async def get_development_arc(self, character_id: str) -> dict[str, Any] | None:
        """Get development arc for a character.

        Args:
            character_id: Character ID

        Returns:
            Development arc if found, None otherwise
        """
        entry = await self.retrieve(f"arcs/{character_id}")
        return entry.value if entry else None

    # Context management
    async def get_context(
        self,
        level: str = ContextLevel.L0,
        character_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get context for character generation.

        Args:
            level: Context level (L0/L1/L2)
            character_ids: Optional specific character IDs

        Returns:
            Context dictionary
        """
        if character_ids:
            context = {}
            for char_id in character_ids:
                profile = await self.retrieve_character(char_id)
                if profile:
                    context[char_id] = profile
            return context
        else:
            # Use adapter's tiered context
            return await self._adapter.get_context(level=level)

    # Synchronous wrappers
    def store_character_sync(
        self,
        character_id: str,
        profile: dict[str, Any],
        is_main: bool = True,
        level: str = ContextLevel.L0,
    ) -> None:
        """Synchronous wrapper for store_character."""
        import asyncio

        asyncio.run(self.store_character(character_id, profile, is_main, level))

    def retrieve_character_sync(self, character_id: str) -> dict[str, Any] | None:
        """Synchronous wrapper for retrieve_character."""
        import asyncio

        return asyncio.run(self.retrieve_character(character_id))

    def close(self) -> None:
        """Close underlying adapter."""
        self._adapter.close()
