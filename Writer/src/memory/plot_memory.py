# src/memory/plot_memory.py
"""Plot memory management with semantic search."""

import logging
from typing import Any

from src.memory.base import BaseMemory, MemoryEntry
from src.memory.memsearch_adapter import ContextLevel, MemSearchAdapter

logger = logging.getLogger(__name__)


class PlotMemory(BaseMemory):
    """Manages plot outline and foreshadowing storage with semantic search.

    Provides domain-specific methods for plot management:
    - Store/retrieve main story arcs and chapter outlines
    - Track foreshadowing and pacing
    - Search plot elements by theme, event, character involvement
    - Maintain narrative consistency across the story
    """

    DEFAULT_PLOT_DIR = "/memory/plot"

    def __init__(
        self,
        base_path: str | None = None,
        namespace: str = "default",
        embedding_provider: str | None = None,
        milvus_uri: str | None = None,
        collection: str = "plot_memory",
    ) -> None:
        super().__init__(namespace=namespace)
        self._adapter = MemSearchAdapter(
            base_path=base_path,
            namespace=namespace,
            embedding_provider=embedding_provider,
            milvus_uri=milvus_uri,
            collection=collection,
        )
        logger.info(f"PlotMemory initialized for namespace '{namespace}'")

    # BaseMemory abstract method implementations
    async def store(self, key: str, value: Any, metadata: dict[str, Any] | None = None) -> None:
        """Store a plot element.

        Args:
            key: Plot element ID (e.g., 'main_arc') or path (e.g., '/memory/plot/main_arc')
            value: Plot data dictionary
            metadata: Optional metadata including 'level' (L0/L1/L2)
        """
        if not key.startswith(self.DEFAULT_PLOT_DIR):
            key = f"{self.DEFAULT_PLOT_DIR}/{key}"
        await self._adapter.store(key, value, metadata)

    async def retrieve(self, key: str) -> MemoryEntry | None:
        """Retrieve a plot element.

        Args:
            key: Plot element ID or path

        Returns:
            MemoryEntry if found, None otherwise
        """
        if not key.startswith(self.DEFAULT_PLOT_DIR):
            key = f"{self.DEFAULT_PLOT_DIR}/{key}"
        return await self._adapter.retrieve(key)

    async def search(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        """Search for plot elements by semantic similarity.

        Args:
            query: Natural language query (e.g., 'climactic battle scene')
            limit: Maximum results

        Returns:
            List of matching plot entries
        """
        return await self._adapter.search(query, limit)

    async def delete(self, key: str) -> bool:
        """Delete a plot element.

        Args:
            key: Plot element ID or path

        Returns:
            True if deleted, False if not found
        """
        if not key.startswith(self.DEFAULT_PLOT_DIR):
            key = f"{self.DEFAULT_PLOT_DIR}/{key}"
        return await self._adapter.delete(key)

    async def list_keys(self, prefix: str = "") -> list[str]:
        """List all plot keys.

        Args:
            prefix: Optional prefix filter

        Returns:
            List of keys
        """
        full_prefix = f"{self.DEFAULT_PLOT_DIR}/{prefix}" if prefix else self.DEFAULT_PLOT_DIR
        keys = await self._adapter.list_keys(full_prefix)
        # Strip the base path from keys
        stripped_keys = []
        for key in keys:
            if key.startswith(self.DEFAULT_PLOT_DIR):
                stripped_keys.append(key[len(self.DEFAULT_PLOT_DIR) + 1 :])
            else:
                stripped_keys.append(key)
        return stripped_keys

    # Domain-specific methods
    async def store_main_arc(
        self,
        arc_id: str,
        main_arc: dict[str, Any],
        level: str = ContextLevel.L0,
    ) -> None:
        """Store main story arc.

        Args:
            arc_id: Arc identifier (e.g., 'main_arc', 'subplot_romance')
            main_arc: Main arc structure (title, logline, acts, climax, resolution)
            level: Context level (L0/L1/L2)
        """
        key = f"arcs/{arc_id}"
        metadata = {"level": level, "type": "main_arc"}
        await self.store(key, main_arc, metadata)

    async def retrieve_main_arc(self, arc_id: str) -> dict[str, Any] | None:
        """Retrieve main story arc.

        Args:
            arc_id: Arc identifier

        Returns:
            Main arc structure if found, None otherwise
        """
        entry = await self.retrieve(f"arcs/{arc_id}")
        return entry.value if entry else None

    async def store_chapter_outline(
        self,
        chapter_number: int,
        outline: dict[str, Any],
        level: str = ContextLevel.L0,
    ) -> None:
        """Store chapter outline.

        Args:
            chapter_number: Chapter number (1-indexed)
            outline: Chapter outline (title, summary, key_events, characters, emotional_beat)
            level: Context level (L0/L1/L2)
        """
        key = f"chapters/{chapter_number:03d}"
        metadata = {"level": level, "type": "chapter_outline", "chapter": chapter_number}
        await self.store(key, outline, metadata)

    async def retrieve_chapter_outline(self, chapter_number: int) -> dict[str, Any] | None:
        """Retrieve chapter outline.

        Args:
            chapter_number: Chapter number

        Returns:
            Chapter outline if found, None otherwise
        """
        entry = await self.retrieve(f"chapters/{chapter_number:03d}")
        return entry.value if entry else None

    async def get_chapter_range(self, start: int, end: int) -> list[dict[str, Any]]:
        """Get outlines for a range of chapters.

        Args:
            start: Start chapter (inclusive)
            end: End chapter (inclusive)

        Returns:
            List of chapter outlines in order
        """
        outlines = []
        for chapter_num in range(start, end + 1):
            outline = await self.retrieve_chapter_outline(chapter_num)
            if outline:
                outlines.append(outline)
        return outlines

    async def store_foreshadowing(
        self,
        foreshadowing_id: str,
        element: dict[str, Any],
    ) -> None:
        """Store foreshadowing element.

        Args:
            foreshadowing_id: Unique identifier
            element: Foreshadowing data (planted_chapter, payoff_chapter, method, etc.)
        """
        key = f"foreshadowing/{foreshadowing_id}"
        metadata = {"type": "foreshadowing"}
        await self.store(key, element, metadata)

    async def get_foreshadowing_for_chapter(self, chapter_number: int) -> list[dict[str, Any]]:
        """Get all foreshadowing elements planted or paying off in a chapter.

        Args:
            chapter_number: Chapter number

        Returns:
            List of foreshadowing elements
        """
        # Search for foreshadowing elements
        entries = await self._adapter.search(f"foreshadowing chapter {chapter_number}", limit=20)
        elements = []
        for entry in entries:
            if "foreshadowing/" in entry.key:
                element = entry.value
                planted = element.get("planted_chapter")
                payoff = element.get("payoff_chapter")
                if planted == chapter_number or payoff == chapter_number:
                    elements.append(element)
        return elements

    async def store_pacing_guide(
        self,
        guide_id: str,
        pacing: dict[str, Any],
    ) -> None:
        """Store pacing guide.

        Args:
            guide_id: Guide identifier
            pacing: Pacing data (chapters_per_act, word_count_targets, emotional_arc)
        """
        key = f"pacing/{guide_id}"
        metadata = {"type": "pacing_guide"}
        await self.store(key, pacing, metadata)

    async def get_pacing_guide(self, guide_id: str) -> dict[str, Any] | None:
        """Retrieve pacing guide.

        Args:
            guide_id: Guide identifier

        Returns:
            Pacing guide if found, None otherwise
        """
        entry = await self.retrieve(f"pacing/{guide_id}")
        return entry.value if entry else None

    async def search_by_theme(self, theme: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search plot elements by theme.

        Args:
            theme: Theme (e.g., 'redemption', 'love', 'war')
            limit: Maximum results

        Returns:
            List of matching plot elements
        """
        entries = await self.search(f"theme {theme}", limit=limit)
        results = []
        for entry in entries:
            # Check if theme appears in the content
            value = entry.value
            if isinstance(value, dict):
                # Check theme field directly
                if value.get("theme", "").lower().find(theme.lower()) >= 0:
                    results.append(value)
                # Check in other text fields
                text_fields = ["logline", "summary", "main_conflict", "emotional_beat"]
                for field in text_fields:
                    if isinstance(value.get(field), str) and theme.lower() in value[field].lower():
                        results.append(value)
                        break
            else:
                # Skip non-dict values
                continue

    async def search_by_character_involvement(
        self,
        character_name: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search plot elements involving a specific character.

        Args:
            character_name: Character name
            limit: Maximum results

        Returns:
            List of matching plot elements
        """
        entries = await self.search(f"character {character_name}", limit=limit)
        results = []
        for entry in entries:
            value = entry.value
            if isinstance(value, dict):
                # Check characters field
                characters = value.get("characters", [])
                if isinstance(characters, list):
                    if any(character_name.lower() in str(c).lower() for c in characters):
                        results.append(value)
                # Check key_events text
                key_events = value.get("key_events", [])
                if isinstance(key_events, list):
                    if any(character_name.lower() in str(e).lower() for e in key_events):
                        results.append(value)
        return results

    async def get_act_structure(self, arc_id: str = "main_arc") -> list[dict[str, Any]] | None:
        """Get act structure for a story arc.

        Args:
            arc_id: Arc identifier

        Returns:
            List of acts if found, None otherwise
        """
        arc = await self.retrieve_main_arc(arc_id)
        if arc and isinstance(arc, dict):
            acts = arc.get("acts", [])
            if isinstance(acts, list):
                return acts
        return None

    async def get_climax(self, arc_id: str = "main_arc") -> str | None:
        """Get climax description for a story arc.

        Args:
            arc_id: Arc identifier

        Returns:
            Climax description if found, None otherwise
        """
        arc = await self.retrieve_main_arc(arc_id)
        if arc and isinstance(arc, dict):
            return arc.get("climax")
        return None

    async def get_resolution(self, arc_id: str = "main_arc") -> str | None:
        """Get resolution description for a story arc.

        Args:
            arc_id: Arc identifier

        Returns:
            Resolution description if found, None otherwise
        """
        arc = await self.retrieve_main_arc(arc_id)
        if arc and isinstance(arc, dict):
            return arc.get("resolution")
        return None

    # Context management
    async def get_context(
        self,
        level: str = ContextLevel.L0,
        chapter_range: tuple[int, int] | None = None,
    ) -> dict[str, Any]:
        """Get context for plot generation.

        Args:
            level: Context level (L0/L1/L2)
            chapter_range: Optional tuple (start_chapter, end_chapter) for chapter-specific context

        Returns:
            Context dictionary
        """
        if chapter_range:
            start, end = chapter_range
            context: dict[str, Any] = {}
            # Get main arc
            main_arc = await self.retrieve_main_arc("main_arc")
            if main_arc:
                context["main_arc"] = main_arc
            # Get chapters in range
            chapters = await self.get_chapter_range(start, end)
            context["chapters"] = chapters
            # Get foreshadowing relevant to these chapters
            foreshadowing = []
            for chapter_num in range(start, end + 1):
                elements = await self.get_foreshadowing_for_chapter(chapter_num)
                foreshadowing.extend(elements)
            context["foreshadowing"] = foreshadowing
            return context
        else:
            # Use adapter's tiered context
            return await self._adapter.get_context(level=level)

    # Synchronous wrappers
    def store_main_arc_sync(
        self,
        arc_id: str,
        main_arc: dict[str, Any],
        level: str = ContextLevel.L0,
    ) -> None:
        """Synchronous wrapper for store_main_arc."""
        import asyncio

        asyncio.run(self.store_main_arc(arc_id, main_arc, level))

    def retrieve_main_arc_sync(self, arc_id: str) -> dict[str, Any] | None:
        """Synchronous wrapper for retrieve_main_arc."""
        import asyncio

        return asyncio.run(self.retrieve_main_arc(arc_id))

    def store_chapter_outline_sync(
        self,
        chapter_number: int,
        outline: dict[str, Any],
        level: str = ContextLevel.L0,
    ) -> None:
        """Synchronous wrapper for store_chapter_outline."""
        import asyncio

        asyncio.run(self.store_chapter_outline(chapter_number, outline, level))

    def retrieve_chapter_outline_sync(self, chapter_number: int) -> dict[str, Any] | None:
        """Synchronous wrapper for retrieve_chapter_outline."""
        import asyncio

        return asyncio.run(self.retrieve_chapter_outline(chapter_number))

    def close(self) -> None:
        """Close underlying adapter."""
        self._adapter.close()
