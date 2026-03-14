# src/memory/world_memory.py
"""World memory management with semantic search."""

import logging
from typing import Any

from src.novel_agent.memory.base import BaseMemory, MemoryEntry
from src.novel_agent.memory.memsearch_adapter import ContextLevel, MemSearchAdapter

logger = logging.getLogger(__name__)


class WorldMemory(BaseMemory):
    """Manages world settings and rules storage with semantic search.

    Provides domain-specific methods for world management:
    - Store/retrieve world rules, locations, society, and history
    - Track magic/technology systems and constraints
    - Search world elements by type, feature, or significance
    - Maintain consistency across the story world
    """

    DEFAULT_WORLD_DIR = "/memory/world"

    def __init__(
        self,
        base_path: str | None = None,
        namespace: str = "default",
        embedding_provider: str | None = None,
        milvus_uri: str | None = None,
        collection: str = "world_memory",
    ) -> None:
        super().__init__(namespace=namespace)
        self._adapter = MemSearchAdapter(
            base_path=base_path,
            namespace=namespace,
            embedding_provider=embedding_provider,
            milvus_uri=milvus_uri,
            collection=collection,
        )
        logger.info(f"WorldMemory initialized for namespace '{namespace}'")

    # BaseMemory abstract method implementations
    async def store(self, key: str, value: Any, metadata: dict[str, Any] | None = None) -> None:
        """Store a world element.

        Args:
            key: World element ID (e.g., 'rules') or path (e.g., '/memory/world/rules')
            value: World data dictionary
            metadata: Optional metadata including 'level' (L0/L1/L2)
        """
        if not key.startswith(self.DEFAULT_WORLD_DIR):
            key = f"{self.DEFAULT_WORLD_DIR}/{key}"
        await self._adapter.store(key, value, metadata)

    async def retrieve(self, key: str) -> MemoryEntry | None:
        """Retrieve a world element.

        Args:
            key: World element ID or path

        Returns:
            MemoryEntry if found, None otherwise
        """
        if not key.startswith(self.DEFAULT_WORLD_DIR):
            key = f"{self.DEFAULT_WORLD_DIR}/{key}"
        return await self._adapter.retrieve(key)

    async def search(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        """Search for world elements by semantic similarity.

        Args:
            query: Natural language query (e.g., 'magic system with limitations')
            limit: Maximum results

        Returns:
            List of matching world entries
        """
        return await self._adapter.search(query, limit)

    async def delete(self, key: str) -> bool:
        """Delete a world element.

        Args:
            key: World element ID or path

        Returns:
            True if deleted, False if not found
        """
        if not key.startswith(self.DEFAULT_WORLD_DIR):
            key = f"{self.DEFAULT_WORLD_DIR}/{key}"
        return await self._adapter.delete(key)

    async def list_keys(self, prefix: str = "") -> list[str]:
        """List all world keys.

        Args:
            prefix: Optional prefix filter

        Returns:
            List of keys
        """
        full_prefix = f"{self.DEFAULT_WORLD_DIR}/{prefix}" if prefix else self.DEFAULT_WORLD_DIR
        keys = await self._adapter.list_keys(full_prefix)
        # Strip the base path from keys
        stripped_keys = []
        for key in keys:
            if key.startswith(self.DEFAULT_WORLD_DIR):
                stripped_keys.append(key[len(self.DEFAULT_WORLD_DIR) + 1 :])
            else:
                stripped_keys.append(key)
        return stripped_keys

    # Domain-specific methods
    async def store_world_rules(
        self,
        rules_id: str,
        rules: dict[str, Any],
        level: str = ContextLevel.L0,
    ) -> None:
        """Store world rules and systems.

        Args:
            rules_id: Rules identifier (e.g., 'core_rules', 'magic_system')
            rules: Rules structure (name, time_period, core_rules, taboos, etc.)
            level: Context level (L0/L1/L2)
        """
        key = f"rules/{rules_id}"
        metadata = {"level": level, "type": "world_rules"}
        await self.store(key, rules, metadata)

    async def retrieve_world_rules(self, rules_id: str) -> dict[str, Any] | None:
        """Retrieve world rules.

        Args:
            rules_id: Rules identifier

        Returns:
            Rules structure if found, None otherwise
        """
        entry = await self.retrieve(f"rules/{rules_id}")
        return entry.value if entry else None

    async def store_location(
        self,
        location_id: str,
        location: dict[str, Any],
        level: str = ContextLevel.L1,
    ) -> None:
        """Store a location.

        Args:
            location_id: Location identifier
            location: Location data (name, type, description, significance, etc.)
            level: Context level (L0/L1/L2)
        """
        key = f"locations/{location_id}"
        metadata = {"level": level, "type": "location"}
        await self.store(key, location, metadata)

    async def retrieve_location(self, location_id: str) -> dict[str, Any] | None:
        """Retrieve a location.

        Args:
            location_id: Location identifier

        Returns:
            Location data if found, None otherwise
        """
        entry = await self.retrieve(f"locations/{location_id}")
        return entry.value if entry else None

    async def search_locations_by_type(self, location_type: str) -> list[dict[str, Any]]:
        """Search locations by type.

        Args:
            location_type: Type of location (e.g., 'city', 'forest', 'spaceship')

        Returns:
            List of matching locations
        """
        entries = await self.search(f"{location_type} location", limit=20)
        locations = []
        for entry in entries:
            if "locations/" in entry.key:
                location = entry.value
                if (
                    isinstance(location, dict)
                    and location.get("type", "").lower() == location_type.lower()
                ):
                    locations.append(location)
        return locations

    async def store_society(
        self,
        society_id: str,
        society: dict[str, Any],
        level: str = ContextLevel.L1,
    ) -> None:
        """Store society structure.

        Args:
            society_id: Society identifier (e.g., 'main_society', 'rebel_faction')
            society: Society data (government, social_classes, economy, culture, conflicts)
            level: Context level (L0/L1/L2)
        """
        key = f"society/{society_id}"
        metadata = {"level": level, "type": "society"}
        await self.store(key, society, metadata)

    async def retrieve_society(self, society_id: str) -> dict[str, Any] | None:
        """Retrieve society structure.

        Args:
            society_id: Society identifier

        Returns:
            Society data if found, None otherwise
        """
        entry = await self.retrieve(f"society/{society_id}")
        return entry.value if entry else None

    async def store_history(
        self,
        history_id: str,
        history: dict[str, Any],
        level: str = ContextLevel.L2,
    ) -> None:
        """Store world history.

        Args:
            history_id: History identifier (e.g., 'main_history', 'ancient_era')
            history: History data (ancient_history, recent_history, key_events, legends)
            level: Context level (L0/L1/L2)
        """
        key = f"history/{history_id}"
        metadata = {"level": level, "type": "history"}
        await self.store(key, history, metadata)

    async def retrieve_history(self, history_id: str) -> dict[str, Any] | None:
        """Retrieve world history.

        Args:
            history_id: History identifier

        Returns:
            History data if found, None otherwise
        """
        entry = await self.retrieve(f"history/{history_id}")
        return entry.value if entry else None

    async def get_timeline_events(self, history_id: str = "main_history") -> list[dict[str, Any]]:
        """Get timeline events from history.

        Args:
            history_id: History identifier

        Returns:
            List of key events
        """
        history = await self.retrieve_history(history_id)
        if history and isinstance(history, dict):
            return history.get("key_events", [])
        return []

    async def store_magic_system(
        self,
        system_id: str,
        magic_system: dict[str, Any],
        level: str = ContextLevel.L0,
    ) -> None:
        """Store magic/technology system.

        Args:
            system_id: System identifier (e.g., 'elemental_magic', 'ftl_drive')
            magic_system: System data (rules, limitations, costs, sources)
            level: Context level (L0/L1/L2)
        """
        key = f"systems/{system_id}"
        metadata = {"level": level, "type": "magic_system"}
        await self.store(key, magic_system, metadata)

    async def retrieve_magic_system(self, system_id: str) -> dict[str, Any] | None:
        """Retrieve magic/technology system.

        Args:
            system_id: System identifier

        Returns:
            Magic system data if found, None otherwise
        """
        entry = await self.retrieve(f"systems/{system_id}")
        return entry.value if entry else None

    async def get_all_constraints(self) -> list[str]:
        """Get all world constraints (rules, taboos, limitations).

        Returns:
            List of constraint descriptions
        """
        constraints = []
        # Get rules
        rules_entry = await self.retrieve_world_rules("core_rules")
        if rules_entry and isinstance(rules_entry, dict):
            # Add taboos
            taboos = rules_entry.get("taboos", [])
            if isinstance(taboos, list):
                constraints.extend(taboos)
            # Add constraints field
            world_constraints = rules_entry.get("constraints", [])
            if isinstance(world_constraints, list):
                constraints.extend(world_constraints)
            # Add limitations from core rules
            core_rules = rules_entry.get("core_rules", [])
            if isinstance(core_rules, list):
                for rule in core_rules:
                    if isinstance(rule, dict):
                        limitation = rule.get("limitations")
                        if limitation:
                            constraints.append(limitation)
        return constraints

    async def search_by_feature(
        self,
        feature: str,
        element_type: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search world elements by feature.

        Args:
            feature: Feature to search for (e.g., 'magic', 'technology', 'trade')
            element_type: Optional element type filter ('rules', 'locations', 'society', 'history')
            limit: Maximum results

        Returns:
            List of matching world elements
        """
        query = f"world {feature}"
        if element_type:
            query = f"{element_type} {feature}"
        entries = await self.search(query, limit=limit)
        results = []
        for entry in entries:
            value = entry.value
            if isinstance(value, dict):
                # Check various fields for feature mention
                text_to_check = []
                # Add all string values
                for v in value.values():
                    if isinstance(v, str):
                        text_to_check.append(v)
                    elif isinstance(v, list):
                        text_to_check.extend([str(item) for item in v if isinstance(item, str)])
                # Check if feature appears in any text
                combined_text = " ".join(text_to_check).lower()
                if feature.lower() in combined_text:
                    results.append(value)
            else:
                # If value is string, check directly
                if isinstance(value, str) and feature.lower() in value.lower():
                    results.append(value)
        return results

    async def get_world_overview(self) -> dict[str, Any]:
        """Get comprehensive world overview.

        Returns:
            Dictionary with all major world components
        """
        overview = {}
        # Get core rules
        rules = await self.retrieve_world_rules("core_rules")
        if rules:
            overview["rules"] = rules
        # Get society
        society = await self.retrieve_society("main_society")
        if society:
            overview["society"] = society
        # Get history
        history = await self.retrieve_history("main_history")
        if history:
            overview["history"] = history
        # Get key locations (first 5)
        location_keys = await self.list_keys("locations/")
        locations = []
        for key in location_keys[:5]:  # Limit to 5
            loc = await self.retrieve(f"locations/{key}")
            if loc:
                locations.append(loc.value)
        if locations:
            overview["key_locations"] = locations
        # Get magic/technology systems
        system_keys = await self.list_keys("systems/")
        systems = []
        for key in system_keys:
            system = await self.retrieve(f"systems/{key}")
            if system:
                systems.append(system.value)
        if systems:
            overview["systems"] = systems
        return overview

    # Context management
    async def get_context(
        self,
        level: str = ContextLevel.L0,
        element_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get context for worldbuilding.

        Args:
            level: Context level (L0/L1/L2)
            element_types: Optional list of element types to include ('rules', 'locations', 'society', 'history', 'systems')

        Returns:
            Context dictionary
        """
        if element_types:
            context = {}
            for elem_type in element_types:
                if elem_type == "rules":
                    rules = await self.retrieve_world_rules("core_rules")
                    if rules:
                        context["rules"] = rules
                elif elem_type == "locations":
                    # Get first 3 locations
                    location_keys = await self.list_keys("locations/")
                    locations = []
                    for key in location_keys[:3]:
                        loc = await self.retrieve(f"locations/{key}")
                        if loc:
                            locations.append(loc.value)
                    if locations:
                        context["locations"] = locations
                elif elem_type == "society":
                    society = await self.retrieve_society("main_society")
                    if society:
                        context["society"] = society
                elif elem_type == "history":
                    history = await self.retrieve_history("main_history")
                    if history:
                        context["history"] = history
                elif elem_type == "systems":
                    system_keys = await self.list_keys("systems/")
                    systems = []
                    for key in system_keys[:2]:  # First 2 systems
                        system = await self.retrieve(f"systems/{key}")
                        if system:
                            systems.append(system.value)
                    if systems:
                        context["systems"] = systems
            return context
        else:
            # Use adapter's tiered context
            return await self._adapter.get_context(level=level)

    # Synchronous wrappers
    def store_world_rules_sync(
        self,
        rules_id: str,
        rules: dict[str, Any],
        level: str = ContextLevel.L0,
    ) -> None:
        """Synchronous wrapper for store_world_rules."""
        import asyncio

        asyncio.run(self.store_world_rules(rules_id, rules, level))

    def retrieve_world_rules_sync(self, rules_id: str) -> dict[str, Any] | None:
        """Synchronous wrapper for retrieve_world_rules."""
        import asyncio

        return asyncio.run(self.retrieve_world_rules(rules_id))

    def store_location_sync(
        self,
        location_id: str,
        location: dict[str, Any],
        level: str = ContextLevel.L1,
    ) -> None:
        """Synchronous wrapper for store_location."""
        import asyncio

        asyncio.run(self.store_location(location_id, location, level))

    def retrieve_location_sync(self, location_id: str) -> dict[str, Any] | None:
        """Synchronous wrapper for retrieve_location."""
        import asyncio

        return asyncio.run(self.retrieve_location(location_id))

    def close(self) -> None:
        """Close underlying adapter."""
        self._adapter.close()
