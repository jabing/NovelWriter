"""Integration tests for Knowledge Graph and SummaryManager integration.

Tests T2-4 and T2-5 functionality:
- T2-4: Knowledge graph query methods (query_related_entities, query_by_time_range, get_entity_timeline)
- T2-5: SummaryManager integration with knowledge graph
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.novel.entity_extractor import (
    CharacterEntity,
)
from src.novel.knowledge_graph import KnowledgeGraph
from src.novel.summary_manager import SummaryManager


@pytest.fixture
def temp_storage(tmp_path):
    """Create temporary storage path."""
    return tmp_path / "test_data"


@pytest.fixture
def mock_llm():
    """Create mock LLM."""
    llm = MagicMock()
    llm.generate_with_system = AsyncMock(return_value=MagicMock(content="{}"))
    return llm


class TestKnowledgeGraphQueries:
    """Test T2-4: Knowledge graph query methods."""

    def test_query_related_entities_basic(self, temp_storage):
        """Test basic BFS traversal for related entities."""
        kg = KnowledgeGraph("test_graph", temp_storage)

        # Create test entities
        kg.add_node("char_1", "character", {"name": "Alice", "appearances": [1, 2, 3]})
        kg.add_node("char_2", "character", {"name": "Bob", "appearances": [1, 2]})
        kg.add_node("char_3", "character", {"name": "Charlie", "appearances": [2, 3]})
        kg.add_node("loc_1", "location", {"name": "City A", "appearances": [1]})

        # Create relationships
        kg.add_edge("rel_1", "char_1", "char_2", "friend", 1.0, {"chapter": 1})
        kg.add_edge("rel_2", "char_2", "char_3", "friend", 1.0, {"chapter": 2})
        kg.add_edge("rel_3", "char_1", "loc_1", "located_at", 1.0, {"chapter": 1})

        # Query related entities
        related = kg.query_related_entities("char_1", max_depth=1)

        assert len(related) == 2  # Bob and City A (depth 1)
        names = {e.properties["name"] for e in related}
        assert "Bob" in names
        assert "City A" in names

    def test_query_related_entities_depth_2(self, temp_storage):
        """Test BFS traversal with depth 2."""
        kg = KnowledgeGraph("test_graph", temp_storage)

        # Create test entities
        kg.add_node("char_1", "character", {"name": "Alice", "appearances": [1]})
        kg.add_node("char_2", "character", {"name": "Bob", "appearances": [1]})
        kg.add_node("char_3", "character", {"name": "Charlie", "appearances": [1]})

        # Create chain: Alice -> Bob -> Charlie
        kg.add_edge("rel_1", "char_1", "char_2", "friend", 1.0, {"chapter": 1})
        kg.add_edge("rel_2", "char_2", "char_3", "friend", 1.0, {"chapter": 1})

        # Query depth 1
        related_depth1 = kg.query_related_entities("char_1", max_depth=1)
        assert len(related_depth1) == 1
        assert related_depth1[0].properties["name"] == "Bob"

        # Query depth 2
        related_depth2 = kg.query_related_entities("char_1", max_depth=2)
        assert len(related_depth2) == 2
        names = {e.properties["name"] for e in related_depth2}
        assert "Bob" in names
        assert "Charlie" in names

    def test_query_related_entities_with_type_filter(self, temp_storage):
        """Test querying with relation type filter."""
        kg = KnowledgeGraph("test_graph", temp_storage)

        kg.add_node("char_1", "character", {"name": "Alice", "appearances": [1]})
        kg.add_node("char_2", "character", {"name": "Bob", "appearances": [1]})
        kg.add_node("loc_1", "location", {"name": "City A", "appearances": [1]})

        kg.add_edge("rel_1", "char_1", "char_2", "friend", 1.0, {"chapter": 1})
        kg.add_edge("rel_2", "char_1", "loc_1", "located_at", 1.0, {"chapter": 1})

        # Query with friend relation only
        related = kg.query_related_entities("char_1", relation_types=["friend"], max_depth=1)

        assert len(related) == 1
        assert related[0].properties["name"] == "Bob"

    def test_query_by_time_range(self, temp_storage):
        """Test querying entities by chapter range."""
        kg = KnowledgeGraph("test_graph", temp_storage)

        # Create entities with different appearances
        kg.add_node("char_1", "character", {"name": "Alice", "appearances": [1, 5, 10]})
        kg.add_node("char_2", "character", {"name": "Bob", "appearances": [3, 4, 5]})
        kg.add_node("char_3", "character", {"name": "Charlie", "appearances": [20, 30]})
        kg.add_node("loc_1", "location", {"name": "City A", "appearances": [1, 50]})

        # Query chapters 1-10
        entities = kg.query_by_time_range(1, 10)

        assert len(entities) == 3  # Alice, Bob, City A
        names = {e.properties["name"] for e in entities}
        assert "Alice" in names
        assert "Bob" in names
        assert "City A" in names
        assert "Charlie" not in names

    def test_query_by_time_range_with_type(self, temp_storage):
        """Test querying by chapter range with entity type filter."""
        kg = KnowledgeGraph("test_graph", temp_storage)

        kg.add_node("char_1", "character", {"name": "Alice", "appearances": [1, 5]})
        kg.add_node("char_2", "character", {"name": "Bob", "appearances": [3]})
        kg.add_node("loc_1", "location", {"name": "City A", "appearances": [1]})

        # Query only characters in range 1-5
        entities = kg.query_by_time_range(1, 5, node_type="character")

        assert len(entities) == 2
        names = {e.properties["name"] for e in entities}
        assert "Alice" in names
        assert "Bob" in names
        assert "City A" not in names

    def test_get_entity_timeline(self, temp_storage):
        """Test getting entity timeline."""
        kg = KnowledgeGraph("test_graph", temp_storage)

        kg.add_node(
            "char_1",
            "character",
            {
                "name": "Alice",
                "appearances": [1, 5, 10],
                "status_history": [{"chapter": 5, "description": "Became queen"}],
            },
        )
        kg.add_node("char_2", "character", {"name": "Bob", "appearances": [1]})

        # Create relationship edge
        kg.add_edge(
            "rel_1",
            "char_1",
            "char_2",
            "friend",
            1.0,
            {"chapter": 1, "description": "Met Bob", "evidence": "They shook hands"},
        )

        timeline = kg.get_entity_timeline("char_1")

        assert len(timeline) > 0

        # Check appearance events
        appearance_events = [e for e in timeline if e["event_type"] == "appearance"]
        assert len(appearance_events) == 3

        # Check status change event
        status_events = [e for e in timeline if e["event_type"] == "status_change"]
        assert len(status_events) == 1
        assert status_events[0]["chapter"] == 5

        # Check relation event
        relation_events = [e for e in timeline if e["event_type"] == "relation"]
        assert len(relation_events) == 1
        assert relation_events[0]["chapter"] == 1

        # Check sorted by chapter
        chapters = [e["chapter"] for e in timeline]
        assert chapters == sorted(chapters)

    def test_get_entity_by_name(self, temp_storage):
        """Test finding entity by name."""
        kg = KnowledgeGraph("test_graph", temp_storage)

        kg.add_node(
            "char_1",
            "character",
            {"name": "Alice", "aliases": ["Princess Alice", "The Queen"], "appearances": [1]},
        )

        # Find by main name
        entity = kg.get_entity_by_name("Alice")
        assert entity is not None
        assert entity.properties["name"] == "Alice"

        # Find by alias
        entity = kg.get_entity_by_name("Princess Alice")
        assert entity is not None
        assert entity.properties["name"] == "Alice"

        # Case insensitive
        entity = kg.get_entity_by_name("alice")
        assert entity is not None

        # Not found
        entity = kg.get_entity_by_name("Bob")
        assert entity is None


class TestSummaryManagerKGIntegration:
    """Test T2-5: SummaryManager knowledge graph integration."""

    @pytest.mark.asyncio
    async def test_summary_manager_kg_initialization(self, temp_storage, mock_llm):
        """Test SummaryManager initializes KG components."""
        manager = SummaryManager(
            storage_path=temp_storage,
            novel_id="test_novel",
            llm=mock_llm,
            use_knowledge_graph=True,
        )

        assert manager.use_knowledge_graph is True
        assert manager.knowledge_graph is not None
        assert manager.entity_extractor is not None
        assert manager.relation_inference is not None

    @pytest.mark.asyncio
    async def test_summary_manager_kg_disabled(self, temp_storage, mock_llm):
        """Test SummaryManager without KG."""
        manager = SummaryManager(
            storage_path=temp_storage,
            novel_id="test_novel",
            llm=mock_llm,
            use_knowledge_graph=False,
        )

        assert manager.use_knowledge_graph is False
        assert manager.knowledge_graph is None
        assert manager.relation_inference is None

    def test_get_related_characters(self, temp_storage, mock_llm):
        """Test get_related_characters method."""
        manager = SummaryManager(
            storage_path=temp_storage,
            novel_id="test_novel",
            llm=mock_llm,
            use_knowledge_graph=True,
        )

        # Add test data to KG
        kg = manager.knowledge_graph
        kg.add_node("char_1", "character", {"name": "Alice", "appearances": [1]})
        kg.add_node("char_2", "character", {"name": "Bob", "appearances": [1]})
        kg.add_node("char_3", "character", {"name": "Charlie", "appearances": [1]})
        kg.add_node("loc_1", "location", {"name": "City A", "appearances": [1]})

        kg.add_edge("rel_1", "char_1", "char_2", "friend", 1.0, {"chapter": 1})
        kg.add_edge("rel_2", "char_1", "char_3", "friend", 1.0, {"chapter": 1})
        kg.add_edge("rel_3", "char_1", "loc_1", "located_at", 1.0, {"chapter": 1})

        # Get related characters
        related = manager.get_related_characters("Alice", max_depth=1)

        assert len(related) == 2
        assert "Bob" in related
        assert "Charlie" in related
        assert "City A" not in related  # Not a character

    def test_get_related_characters_kg_disabled(self, temp_storage, mock_llm):
        """Test get_related_characters returns empty when KG disabled."""
        manager = SummaryManager(
            storage_path=temp_storage,
            novel_id="test_novel",
            llm=mock_llm,
            use_knowledge_graph=False,
        )

        related = manager.get_related_characters("Alice")
        assert related == []

    def test_get_character_timeline(self, temp_storage, mock_llm):
        """Test get_character_timeline method."""
        manager = SummaryManager(
            storage_path=temp_storage,
            novel_id="test_novel",
            llm=mock_llm,
            use_knowledge_graph=True,
        )

        # Add test data to KG
        kg = manager.knowledge_graph
        kg.add_node(
            "char_1",
            "character",
            {
                "name": "Alice",
                "appearances": [1, 5, 10],
                "status_history": [{"chapter": 5, "description": "Became queen"}],
            },
        )

        timeline = manager.get_character_timeline("Alice")

        assert len(timeline) > 0
        # Should have at least appearance events
        appearance_events = [e for e in timeline if e["event_type"] == "appearance"]
        assert len(appearance_events) == 3

    def test_get_character_timeline_not_found(self, temp_storage, mock_llm):
        """Test get_character_timeline for non-existent character."""
        manager = SummaryManager(
            storage_path=temp_storage,
            novel_id="test_novel",
            llm=mock_llm,
            use_knowledge_graph=True,
        )

        timeline = manager.get_character_timeline("NonExistent")
        assert timeline == []

    def test_get_character_timeline_kg_disabled(self, temp_storage, mock_llm):
        """Test get_character_timeline returns empty when KG disabled."""
        manager = SummaryManager(
            storage_path=temp_storage,
            novel_id="test_novel",
            llm=mock_llm,
            use_knowledge_graph=False,
        )

        timeline = manager.get_character_timeline("Alice")
        assert timeline == []


class TestEndToEndKGWorkflow:
    """End-to-end tests for KG integration workflow."""

    @pytest.mark.asyncio
    async def test_chapter_processing_with_kg(self, temp_storage, mock_llm):
        """Test full chapter processing with KG extraction."""
        manager = SummaryManager(
            storage_path=temp_storage,
            novel_id="test_novel",
            llm=mock_llm,
            use_knowledge_graph=True,
            use_auto_fix=False,  # Disable for simpler test
        )

        # Process a chapter
        content = """
        Alice met Bob in the City Square. They discussed their plans.
        Charlie watched from a distance. The meeting was important.
        """

        # Mock entity extractor to return test data
        test_entity = CharacterEntity(
            id="char_alice", name="Alice", first_appearance=1, appearances=[1]
        )

        mock_extraction = MagicMock()
        mock_extraction.entities = [test_entity]
        mock_extraction.relation_count = 0
        mock_extraction.event_count = 0

        manager.entity_extractor.extract_from_chapter = AsyncMock(return_value=mock_extraction)

        # Process chapter (uses process_chapter_with_autofix)
        # Mock auto_fixer to avoid needing full setup
        manager.auto_fixer = MagicMock()
        manager.auto_fixer.verify.return_value = MagicMock(is_consistent=True)

        summary, verification, auto_fix_result = await manager.process_chapter_with_autofix(
            chapter_number=1,
            title="Test Chapter",
            content=content,
        )

        assert summary is not None
        # Verify extraction was called
        manager.entity_extractor.extract_from_chapter.assert_called_once()
