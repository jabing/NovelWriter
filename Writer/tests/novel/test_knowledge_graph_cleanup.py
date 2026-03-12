"""Tests for KnowledgeGraph cleanup functionality."""

import pytest

from src.novel.knowledge_graph import (
    CLEANUP_FREQUENCY,
    LOOKBACK_CHAPTERS,
    KnowledgeGraph,
)


class TestKnowledgeGraphCleanupConstants:
    """Test cleanup configuration constants."""

    def test_cleanup_frequency_default(self):
        """Test CLEANUP_FREQUENCY has expected value."""
        assert CLEANUP_FREQUENCY == 5  # Changed from 10 for 50-chapter support

    def test_lookback_chapters_default(self):
        """Test LOOKBACK_CHAPTERS has expected value."""
        assert LOOKBACK_CHAPTERS == 10  # Changed from 5 for 50-chapter support


class TestKnowledgeGraphCleanup:
    """Test cleanup_unreferenced method."""

    @pytest.fixture
    def kg_with_mixed_entities(self):
        """Create a knowledge graph with various entity types."""
        kg = KnowledgeGraph()

        # Primary characters
        kg.add_node(
            node_id="alice",
            node_type="character",
            properties={"name": "Alice", "role": "protagonist"},
        )
        kg.add_node(
            node_id="bob",
            node_type="character",
            properties={"name": "Bob", "role": "ally"},
        )

        # Minor character (should be removed)
        kg.add_node(
            node_id="tavern_keeper",
            node_type="character",
            properties={"name": "Tavern Keeper"},
        )

        # Minor character with active status (should be kept)
        kg.add_node(
            node_id="active_guard",
            node_type="character",
            properties={"name": "Guard", "status": "active"},
        )

        # Main location
        kg.add_node(
            node_id="crystal_palace",
            node_type="location",
            properties={"name": "Crystal Palace", "is_main": True},
        )

        # Minor location (should be removed)
        kg.add_node(
            node_id="old_forest_path",
            node_type="location",
            properties={"name": "Old Forest Path"},
        )

        # Recently mentioned character (should be kept)
        kg.add_node(
            node_id="recent_npc",
            node_type="character",
            properties={"name": "Recent NPC"},
        )

        # Add edges
        kg.add_edge(
            edge_id="e1",
            source_id="alice",
            target_id="bob",
            relationship_type="friend",
        )
        kg.add_edge(
            edge_id="e2",
            source_id="alice",
            target_id="tavern_keeper",
            relationship_type="knows",
        )

        return kg

    def test_cleanup_removes_unreferenced_entities(self, kg_with_mixed_entities):
        """Test that unreferenced entities are removed."""
        kg = kg_with_mixed_entities

        initial_count = len(kg._nodes)
        assert initial_count == 7

        # Run cleanup with empty recent chapters and plot threads
        removed = kg.cleanup_unreferenced(
            recent_chapters=[],
            primary_characters={"alice", "bob"},
            active_plot_threads=[],
        )

        # Tavern keeper, old forest path, and recent_npc should be removed
        # (recent_npc is not protected - not in recent_chapters content)
        assert len(removed) == 3
        assert "tavern_keeper" in removed
        assert "old_forest_path" in removed
        assert "recent_npc" in removed

        # Verify remaining entities
        assert len(kg._nodes) == 4
        assert "alice" in kg._nodes
        assert "bob" in kg._nodes
        assert "active_guard" in kg._nodes  # Has active status
        assert "crystal_palace" in kg._nodes  # Is main location
        assert "recent_npc" not in kg._nodes  # Not mentioned in recent chapters

    def test_primary_characters_never_removed(self, kg_with_mixed_entities):
        """Test that primary characters are never removed."""
        kg = kg_with_mixed_entities

        # Run cleanup with Alice not mentioned in recent chapters
        removed = kg.cleanup_unreferenced(
            recent_chapters=["Bob went to the market."],  # Alice not mentioned
            primary_characters={"alice", "bob"},
            active_plot_threads=[],
        )

        # Alice should NOT be removed even though not mentioned
        assert "alice" not in removed
        assert "alice" in kg._nodes

    def test_recently_mentioned_entities_kept(self, kg_with_mixed_entities):
        """Test that entities mentioned in recent chapters are kept."""
        kg = kg_with_mixed_entities

        # Run cleanup with Recent NPC mentioned
        removed = kg.cleanup_unreferenced(
            recent_chapters=["Recent NPC appeared in the story."],
            primary_characters={"alice", "bob"},
            active_plot_threads=[],
        )

        # Recent NPC should NOT be removed
        assert "recent_npc" not in removed
        assert "recent_npc" in kg._nodes

    def test_active_plot_thread_entities_kept(self, kg_with_mixed_entities):
        """Test that entities in active plot threads are kept."""
        kg = kg_with_mixed_entities

        # Run cleanup with Tavern Keeper in plot thread
        removed = kg.cleanup_unreferenced(
            recent_chapters=[],
            primary_characters={"alice", "bob"},
            active_plot_threads=["The Tavern Keeper knows a secret."],
        )

        # Tavern Keeper should NOT be removed (in active plot thread)
        assert "tavern_keeper" not in removed
        assert "tavern_keeper" in kg._nodes

    def test_main_locations_kept(self, kg_with_mixed_entities):
        """Test that main locations are kept."""
        kg = kg_with_mixed_entities

        # Run cleanup with Crystal Palace not mentioned
        removed = kg.cleanup_unreferenced(
            recent_chapters=[],
            primary_characters={"alice", "bob"},
            active_plot_threads=[],
        )

        # Crystal Palace should NOT be removed (is_main=True)
        assert "crystal_palace" not in removed
        assert "crystal_palace" in kg._nodes

    def test_active_status_entities_kept(self, kg_with_mixed_entities):
        """Test that entities with status='active' are kept."""
        kg = kg_with_mixed_entities

        # Run cleanup with active guard not mentioned
        removed = kg.cleanup_unreferenced(
            recent_chapters=[],
            primary_characters={"alice", "bob"},
            active_plot_threads=[],
        )

        # Active guard should NOT be removed (status=active)
        assert "active_guard" not in removed
        assert "active_guard" in kg._nodes

    def test_cleanup_removes_connected_edges(self, kg_with_mixed_entities):
        """Test that removing a node also removes connected edges."""
        kg = kg_with_mixed_entities

        # Verify edge exists before cleanup
        assert kg.get_edge("e2") is not None  # alice -> tavern_keeper

        # Run cleanup
        removed = kg.cleanup_unreferenced(
            recent_chapters=[],
            primary_characters={"alice", "bob"},
            active_plot_threads=[],
        )

        # Tavern keeper should be removed
        assert "tavern_keeper" in removed

        # Edge to tavern keeper should also be removed
        assert kg.get_edge("e2") is None

        # Edge between alice and bob should remain
        assert kg.get_edge("e1") is not None

    def test_cleanup_returns_removed_ids(self, kg_with_mixed_entities):
        """Test that cleanup returns list of removed entity IDs."""
        kg = kg_with_mixed_entities

        removed = kg.cleanup_unreferenced(
            recent_chapters=[],
            primary_characters={"alice", "bob"},
            active_plot_threads=[],
        )

        # Verify return value
        assert isinstance(removed, list)
        assert all(isinstance(id, str) for id in removed)

    def test_cleanup_with_chapter_num_logging(self, kg_with_mixed_entities, caplog):
        """Test that cleanup logs chapter number when provided."""
        kg = kg_with_mixed_entities

        with caplog.at_level("INFO"):
            kg.cleanup_unreferenced(
                recent_chapters=[],
                primary_characters={"alice", "bob"},
                active_plot_threads=[],
                chapter_num=10,
            )

        # Check log contains chapter number
        assert any("chapter 10" in record.message.lower() for record in caplog.records)

    def test_cleanup_preserves_graph_structure(self, kg_with_mixed_entities):
        """Test that cleanup preserves graph structure for remaining entities."""
        kg = kg_with_mixed_entities

        # Run cleanup
        kg.cleanup_unreferenced(
            recent_chapters=["Bob helped Alice."],
            primary_characters={"alice", "bob"},
            active_plot_threads=[],
        )

        # Verify remaining entities have correct structure
        alice = kg.get_node("alice")
        assert alice is not None
        assert alice.properties["name"] == "Alice"

        # Verify edges
        neighbors = kg.get_neighbors("alice", relationship_types=["friend"])
        assert any(n.node_id == "bob" for n in neighbors)


class TestIsUnreferenced:
    """Test the _is_unreferenced helper method."""

    @pytest.fixture
    def kg(self):
        """Create a fresh knowledge graph."""
        return KnowledgeGraph()

    def test_primary_character_protected(self, kg):
        """Test primary characters return False (protected)."""
        kg.add_node(
            node_id="hero",
            node_type="character",
            properties={"name": "Hero"},
        )

        node = kg.get_node("hero")
        is_unreferenced = kg._is_unreferenced(
            entity=node,
            recent_chapters=[],
            primary_characters={"hero"},
            active_plot_threads=[],
        )

        assert is_unreferenced is False

    def test_active_status_protected(self, kg):
        """Test entities with status='active' return False (protected)."""
        kg.add_node(
            node_id="active_char",
            node_type="character",
            properties={"name": "Active", "status": "active"},
        )

        node = kg.get_node("active_char")
        is_unreferenced = kg._is_unreferenced(
            entity=node,
            recent_chapters=[],
            primary_characters=set(),
            active_plot_threads=[],
        )

        assert is_unreferenced is False

    def test_recently_mentioned_protected(self, kg):
        """Test entities mentioned in recent chapters return False."""
        kg.add_node(
            node_id="recent",
            node_type="character",
            properties={"name": "Recent Character"},
        )

        node = kg.get_node("recent")
        is_unreferenced = kg._is_unreferenced(
            entity=node,
            recent_chapters=["Recent Character appeared here."],
            primary_characters=set(),
            active_plot_threads=[],
        )

        assert is_unreferenced is False

    def test_in_plot_thread_protected(self, kg):
        """Test entities in active plot threads return False."""
        kg.add_node(
            node_id="plot_entity",
            node_type="character",
            properties={"name": "Plot Character"},
        )

        node = kg.get_node("plot_entity")
        is_unreferenced = kg._is_unreferenced(
            entity=node,
            recent_chapters=[],
            primary_characters=set(),
            active_plot_threads=["Plot Character knows the secret."],
        )

        assert is_unreferenced is False

    def test_main_location_protected(self, kg):
        """Test main locations return False (protected)."""
        kg.add_node(
            node_id="main_loc",
            node_type="location",
            properties={"name": "Main Castle", "is_main": True},
        )

        node = kg.get_node("main_loc")
        is_unreferenced = kg._is_unreferenced(
            entity=node,
            recent_chapters=[],
            primary_characters=set(),
            active_plot_threads=[],
        )

        assert is_unreferenced is False

    def test_unreferenced_entity_returns_true(self, kg):
        """Test unreferenced entities return True (can be removed)."""
        kg.add_node(
            node_id="minor_char",
            node_type="character",
            properties={"name": "Minor Character"},
        )

        node = kg.get_node("minor_char")
        is_unreferenced = kg._is_unreferenced(
            entity=node,
            recent_chapters=["Some other content."],
            primary_characters=set(),
            active_plot_threads=["Unrelated plot thread."],
        )

        assert is_unreferenced is True

    def test_uses_node_id_when_no_name(self, kg):
        """Test that node_id is used when name property is missing."""
        kg.add_node(
            node_id="unnamed_entity",
            node_type="character",
            properties={},  # No name
        )

        node = kg.get_node("unnamed_entity")

        # Should use node_id for reference checking
        is_unreferenced = kg._is_unreferenced(
            entity=node,
            recent_chapters=["unnamed_entity was mentioned"],
            primary_characters=set(),
            active_plot_threads=[],
        )

        # Should be protected because node_id was in recent chapters
        assert is_unreferenced is False


class TestCleanupEdgeCases:
    """Test edge cases in cleanup functionality."""

    def test_cleanup_empty_graph(self):
        """Test cleanup on empty graph."""
        kg = KnowledgeGraph()

        removed = kg.cleanup_unreferenced(
            recent_chapters=[],
            primary_characters=set(),
            active_plot_threads=[],
        )

        assert removed == []
        assert len(kg._nodes) == 0

    def test_cleanup_all_protected(self):
        """Test cleanup when all entities are protected."""
        kg = KnowledgeGraph()

        # Add only protected entities
        kg.add_node(
            node_id="hero",
            node_type="character",
            properties={"name": "Hero"},
        )
        kg.add_node(
            node_id="castle",
            node_type="location",
            properties={"name": "Castle", "is_main": True},
        )

        removed = kg.cleanup_unreferenced(
            recent_chapters=["Hero was here."],
            primary_characters={"hero"},
            active_plot_threads=["The Castle holds secrets."],
        )

        assert removed == []
        assert len(kg._nodes) == 2

    def test_cleanup_all_removable(self):
        """Test cleanup when all entities can be removed."""
        kg = KnowledgeGraph()

        # Add only removable entities
        kg.add_node(
            node_id="minor1",
            node_type="character",
            properties={"name": "Minor One"},
        )
        kg.add_node(
            node_id="minor2",
            node_type="character",
            properties={"name": "Minor Two"},
        )

        removed = kg.cleanup_unreferenced(
            recent_chapters=["Completely unrelated content."],
            primary_characters=set(),
            active_plot_threads=["Also unrelated."],
        )

        assert len(removed) == 2
        assert len(kg._nodes) == 0

    def test_cleanup_substring_name_match(self):
        """Test that substring name matches DO protect entities.

        The implementation uses substring matching, so 'Bob' in 'Bobby' will match.
        This is intentional - partial matches likely refer to the same character.
        """
        kg = KnowledgeGraph()

        kg.add_node(
            node_id="bob",
            node_type="character",
            properties={"name": "Bob"},
        )

        # "Bob" is a substring of "Bobby", so Bob should be protected
        removed = kg.cleanup_unreferenced(
            recent_chapters=["Bobby went to the store."],  # Contains "Bob"
            primary_characters=set(),
            active_plot_threads=[],
        )

        # Bob should be protected because "Bob" is a substring in recent chapters
        assert "bob" not in removed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
