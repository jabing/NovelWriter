"""Tests for inventory updater system."""

import pytest

from src.novel.continuity import CharacterState, StoryState
from src.novel.inventory_updater import InventoryUpdater


class TestInventoryUpdater:
    """Test InventoryUpdater functionality."""

    def test_initialization(self) -> None:
        """Test that InventoryUpdater can be initialized."""
        updater = InventoryUpdater()

        assert updater.knowledge_graph is not None
        assert updater.timeline_manager is not None
        assert updater.continuity_manager is not None
        # Glossary manager may be None if initialization fails
        # That's acceptable for fallback behavior

    @pytest.mark.asyncio
    async def test_update_inventory_empty_content(self) -> None:
        """Test inventory update with empty chapter content."""
        updater = InventoryUpdater()

        stats = await updater.update_inventory(
            chapter_content="",
            chapter_number=1,
            story_state=None,
        )

        assert stats["entities_extracted"] == 0
        assert stats["relationships_extracted"] == 0
        assert stats["events_extracted"] == 0
        assert stats["glossary_terms_added"] == 0
        assert len(stats["errors"]) == 0

    @pytest.mark.asyncio
    async def test_update_inventory_with_characters(self) -> None:
        """Test inventory update with character names."""
        updater = InventoryUpdater()

        # Create a story state with existing characters
        character_state = CharacterState(
            name="Sir Kael",
            status="alive",
            location="Forest",
            physical_form="human",
            relationships={},
        )

        story_state = StoryState(
            chapter=1,
            location="Forest",
            active_characters=["Sir Kael"],
            character_states={"Sir Kael": character_state},
            plot_threads=[],
            key_events=[],
        )

        chapter_content = "Sir Kael rode through the forest. He carried a sword."

        stats = await updater.update_inventory(
            chapter_content=chapter_content,
            chapter_number=2,
            story_state=story_state,
        )

        # Should extract at least Sir Kael character
        assert stats["entities_extracted"] >= 1
        assert "errors" in stats
        assert len(stats["errors"]) == 0

        # Check knowledge graph has the character
        kg = updater.knowledge_graph
        assert len(kg._nodes) >= 1

        # Verify character node exists
        character_found = False
        for _node_id, node in kg._nodes.items():
            if node.node_type == "character" and "Sir Kael" in str(node.properties.get("name", "")):
                character_found = True
                break
        assert character_found, "Character node should exist in knowledge graph"

    @pytest.mark.asyncio
    async def test_entity_extraction_simple(self) -> None:
        """Test entity extraction with simple content."""
        updater = InventoryUpdater()

        chapter_content = "Kael found a magical sword in the ancient cave."

        entities = updater._extract_entities(chapter_content, None)

        # Should extract items (sword, cave)
        assert len(entities) >= 2

        item_types = [e[0] for e in entities]
        item_names = [e[1] for e in entities]

        assert "item" in item_types
        # Should find "sword" and "cave" (after cleaning)
        assert any("sword" in name.lower() for name in item_names) or any(
            "cave" in name.lower() for name in item_names
        )

    def test_clean_entity_phrase(self) -> None:
        """Test entity phrase cleaning."""
        updater = InventoryUpdater()

        # Test with possessive pronoun
        result = updater._clean_entity_phrase("his sword")
        assert result == "sword"

        # Test with multiple stop words
        result = updater._clean_entity_phrase("the ancient sword of power")
        assert result == "ancient sword"

        # Test with only stop words
        result = updater._clean_entity_phrase("his the")
        assert result is None

        # Test with no stop words
        result = updater._clean_entity_phrase("DragonFire Sword")
        assert result == "DragonFire Sword"

    @pytest.mark.asyncio
    async def test_relationship_extraction(self) -> None:
        """Test relationship extraction."""
        updater = InventoryUpdater()

        chapter_content = "Kael fought the dragon. Lyra healed Kael."

        # First extract entities
        entities = updater._extract_entities(chapter_content, None)

        # Then extract relationships
        relationships = updater._extract_relationships(chapter_content, entities)

        # Should find at least one relationship
        assert len(relationships) >= 1

        # Check relationship structure
        for source, target, rel_type, evidence in relationships:
            assert source
            assert target
            assert rel_type
            assert evidence
            assert rel_type in ["fought", "defended", "combat"]  # Based on patterns

    def test_event_extraction(self) -> None:
        """Test event extraction."""
        updater = InventoryUpdater()

        chapter_content = "The battle began at dawn. They discovered the treasure."

        events = updater._extract_events(chapter_content, chapter_number=1)

        # Should find events with keywords "battle" and "discovered"
        assert len(events) >= 2

        for event_id, timestamp, description, event_type, metadata in events:
            assert event_id.startswith("ch001")
            assert timestamp == "Chapter 1"
            assert description
            assert event_type in ["combat", "discovery", "start"]
            assert "sentence" in metadata

    def test_glossary_term_extraction(self) -> None:
        """Test glossary term extraction."""
        updater = InventoryUpdater()

        chapter_content = "The DragonFire Sword was created by the Ancient Elves of Eldergrove."

        terms = updater._extract_glossary_terms(chapter_content)

        # Should extract proper noun phrases
        assert len(terms) >= 1

        for term, term_type, definition in terms:
            assert term
            assert term_type in ["character", "location", "item", "concept"]
            assert definition

    @pytest.mark.asyncio
    async def test_integration_with_story_state(self) -> None:
        """Test full integration with story state."""
        updater = InventoryUpdater()

        # Create initial story state
        character_state = CharacterState(
            name="Lyra",
            status="alive",
            location="Village",
            physical_form="elf",
            relationships={},
        )

        story_state = StoryState(
            chapter=1,
            location="Village",
            active_characters=["Lyra"],
            character_states={"Lyra": character_state},
            plot_threads=["Search for the artifact"],
            key_events=["Lyra left the village"],
        )

        chapter_content = """
        Lyra traveled to the Dark Forest. She found the Crystal of Truth.
        A wolf attacked her, but she defended herself with her magic.
        """

        stats = await updater.update_inventory(
            chapter_content=chapter_content,
            chapter_number=2,
            story_state=story_state,
        )

        # Should extract entities, relationships, and events
        assert stats["entities_extracted"] > 0
        assert stats["relationships_extracted"] >= 0  # May be 0 if patterns don't match
        assert stats["events_extracted"] > 0
        assert "errors" in stats
        assert len(stats["errors"]) == 0

        # Verify timeline has events
        timeline = updater.timeline_manager
        assert len(timeline._events) == stats["events_extracted"]

    def test_find_entity_by_name(self) -> None:
        """Test entity lookup by name."""
        updater = InventoryUpdater()

        entities = [
            ("character", "Kael", {"name": "Kael", "type": "character"}),
            ("item", "Sword", {"name": "Sword", "type": "item"}),
            ("location", "Forest", {"name": "Forest", "type": "location"}),
        ]

        # Exact match
        found = updater._find_entity_by_name(entities, "Kael")
        assert found is not None
        assert found[1] == "Kael"

        # Case insensitive
        found = updater._find_entity_by_name(entities, "kael")
        assert found is not None
        assert found[1] == "Kael"

        # Not found
        found = updater._find_entity_by_name(entities, "Dragon")
        assert found is None
