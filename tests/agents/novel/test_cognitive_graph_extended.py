"""Tests for ExtendedCognitiveGraph class."""

import pytest

from src.novel_agent.novel.cognitive_graph_extended import (
    ConflictResolution,
    ExtendedCognitiveGraph,
    RESOLUTION_SUGGESTIONS,
)


class TestExtendedCognitiveGraphInit:
    """Test ExtendedCognitiveGraph initialization."""

    def test_default_initialization(self):
        """Test initialization with default parameters."""
        graph = ExtendedCognitiveGraph()

        assert graph.graph_id == "default"
        assert graph.node_count == 0
        assert graph.edge_count == 0
        assert len(graph._inferred_edges) == 0

    def test_custom_graph_id(self):
        """Test initialization with custom graph ID."""
        graph = ExtendedCognitiveGraph(graph_id="extended_test")

        assert graph.graph_id == "extended_test"


class TestRelationshipInference:
    """Test relationship inference functionality."""

    @pytest.fixture
    def graph(self):
        """Create a graph for inference tests."""
        g = ExtendedCognitiveGraph()
        g.add_character_node("char1", "林晚", tier=0)
        g.add_character_node("char2", "丞相", tier=1)
        g.add_character_node("char3", "将军", tier=1)
        return g

    def test_infer_relationships_empty_graph(self):
        """Test inference with no relationships."""
        graph = ExtendedCognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)

        inferred = graph.infer_relationships("char1")

        assert inferred == []

    def test_infer_relationships_nonexistent_character(self):
        """Test inference for nonexistent character."""
        graph = ExtendedCognitiveGraph()

        inferred = graph.infer_relationships("nonexistent")

        assert inferred == []

    def test_infer_transitive_relationships(self, graph):
        """Test transitivity inference: A knows B, B knows C => A knows C."""
        graph.add_relationship("char1", "char2", "knows")
        graph.add_relationship("char2", "char3", "knows")

        inferred = graph.infer_relationships("char1")

        assert len(inferred) == 1
        rel = inferred[0]
        assert rel["target_id"] == "char3"
        assert rel["relation_type"] == "knows_of"
        assert rel["inference_method"] == "transitivity"
        assert rel["confidence"] == 0.6

    def test_infer_colocation_relationships(self):
        """Test co-location inference: same location implies met."""
        graph = ExtendedCognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)
        graph.add_character_node("char2", "丞相", tier=1)
        graph.add_location_node("loc1", "京城")
        graph.add_relationship("char1", "loc1", "located_at")
        graph.add_relationship("char2", "loc1", "located_at")

        inferred = graph.infer_relationships("char1")

        assert len(inferred) == 1
        rel = inferred[0]
        assert rel["target_id"] == "char2"
        assert rel["relation_type"] == "met"
        assert rel["inference_method"] == "co-location"
        assert rel["confidence"] == 0.7

    def test_infer_shared_knowledge_relationships(self):
        """Test shared knowledge inference: same facts implies discussion."""
        graph = ExtendedCognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)
        graph.add_character_node("char2", "丞相", tier=1)
        graph.add_fact_node("fact1", "secret", "丞相私通敌国", "char2", 3)
        graph.add_character_knowledge("char1", "fact1", confidence=0.8)
        graph.add_character_knowledge("char2", "fact1", confidence=1.0)

        inferred = graph.infer_relationships("char1")

        assert len(inferred) == 1
        rel = inferred[0]
        assert rel["target_id"] == "char2"
        assert rel["relation_type"] == "discussed_with"
        assert rel["inference_method"] == "shared_knowledge"

    def test_infer_multiple_relationships(self, graph):
        """Test inference with multiple potential relationships."""
        graph.add_location_node("loc1", "京城")
        graph.add_fact_node("fact1", "event", "宴会", "char1", 1)
        graph.add_relationship("char1", "char2", "knows")
        graph.add_relationship("char2", "char3", "knows")
        graph.add_relationship("char1", "loc1", "located_at")
        graph.add_relationship("char2", "loc1", "located_at")
        graph.add_character_knowledge("char1", "fact1")
        graph.add_character_knowledge("char2", "fact1")

        inferred = graph.infer_relationships("char1")

        assert len(inferred) >= 2

        relation_types = [r["relation_type"] for r in inferred]
        assert "knows_of" in relation_types
        assert "met" in relation_types or "discussed_with" in relation_types

    def test_inferred_edges_tracking(self, graph):
        """Test that inferred edges are tracked."""
        graph.add_relationship("char1", "char2", "knows")
        graph.add_relationship("char2", "char3", "knows")

        graph.infer_relationships("char1")

        assert len(graph._inferred_edges) == 1

    def test_clear_inferred_edges(self, graph):
        """Test clearing inferred edges."""
        graph.add_relationship("char1", "char2", "knows")
        graph.add_relationship("char2", "char3", "knows")
        graph.infer_relationships("char1")

        assert len(graph._inferred_edges) == 1

        graph.clear_inferred_edges()

        assert len(graph._inferred_edges) == 0

    def test_get_inferred_edges(self, graph):
        """Test getting all inferred edges."""
        graph.add_relationship("char1", "char2", "knows")
        graph.add_relationship("char2", "char3", "knows")
        graph.infer_relationships("char1")

        inferred = graph.get_inferred_edges()

        assert len(inferred) == 1
        assert inferred[0]["source"] == "char1"
        assert inferred[0]["target"] == "char3"


class TestConflictResolutionSuggestions:
    """Test conflict resolution suggestion functionality."""

    @pytest.fixture
    def graph(self):
        """Create a graph with potential conflicts."""
        g = ExtendedCognitiveGraph()
        g.add_fact_node(
            "fact1",
            fact_type="event",
            content="城门打开",
            source_character="char1",
            chapter=1,
        )
        g.add_fact_node(
            "fact2",
            fact_type="event",
            content="城门没打开",
            source_character="char2",
            chapter=1,
        )
        return g

    def test_suggest_resolutions_with_conflict(self, graph):
        """Test suggesting resolutions for a conflict."""
        resolutions = graph.suggest_conflict_resolutions("fact1")

        assert len(resolutions) >= 1
        negation_res = [r for r in resolutions if r.conflict_type == "negation_conflict"]
        assert len(negation_res) >= 1
        assert len(negation_res[0].affected_nodes) == 2

    def test_suggest_resolutions_no_conflict(self):
        """Test suggesting resolutions when no conflict exists."""
        graph = ExtendedCognitiveGraph()
        graph.add_fact_node(
            "fact1",
            fact_type="event",
            content="林晚去了京城",
            source_character="char1",
            chapter=1,
        )

        resolutions = graph.suggest_conflict_resolutions("fact1")

        assert len(resolutions) == 1
        assert resolutions[0].conflict_type == "timeline_order"

    def test_suggest_resolutions_nonexistent_fact(self):
        """Test suggesting resolutions for nonexistent fact."""
        graph = ExtendedCognitiveGraph()

        resolutions = graph.suggest_conflict_resolutions("nonexistent")

        assert resolutions == []

    def test_suggest_resolutions_timeline_conflict(self):
        """Test resolution for timeline conflicts."""
        graph = ExtendedCognitiveGraph()
        graph.add_fact_node(
            "fact1",
            fact_type="event",
            content="林晚到达",
            source_character="char1",
            chapter=1,
        )
        graph.add_fact_node(
            "fact2",
            fact_type="event",
            content="林晚到达",
            source_character="char2",
            chapter=3,
        )

        resolutions = graph.suggest_conflict_resolutions("fact1")

        timeline_res = [r for r in resolutions if r.conflict_type == "timeline_order"]
        assert len(timeline_res) >= 1

    def test_conflict_resolution_to_dict(self):
        """Test ConflictResolution serialization."""
        resolution = ConflictResolution(
            conflict_id="test_conflict",
            conflict_type="content_conflict",
            suggestion="Verify facts",
            affected_nodes=["fact1", "fact2"],
            priority=1,
            auto_fixable=False,
        )

        data = resolution.to_dict()

        assert data["conflict_id"] == "test_conflict"
        assert data["conflict_type"] == "content_conflict"
        assert data["suggestion"] == "Verify facts"
        assert data["affected_nodes"] == ["fact1", "fact2"]
        assert data["priority"] == 1
        assert data["auto_fixable"] is False


class TestVisualizationExport:
    """Test graph visualization export functionality."""

    @pytest.fixture
    def graph(self):
        """Create a graph for visualization tests."""
        g = ExtendedCognitiveGraph(graph_id="viz_test")
        g.add_character_node("char1", "林晚", tier=0)
        g.add_character_node("char2", "丞相", tier=1)
        g.add_location_node("loc1", "京城")
        g.add_fact_node("fact1", "secret", "丞相私通敌国", "char2", 3)
        g.add_relationship("char1", "char2", "knows", {"confidence": 0.8})
        g.add_character_knowledge("char1", "fact1", confidence=0.7)
        return g

    def test_export_for_visualization_structure(self, graph):
        """Test basic structure of visualization export."""
        viz_data = graph.export_for_visualization()

        assert "nodes" in viz_data
        assert "edges" in viz_data
        assert "statistics" in viz_data
        assert viz_data["graph_id"] == "viz_test"

    def test_export_nodes(self, graph):
        """Test node export for visualization."""
        viz_data = graph.export_for_visualization()

        nodes = viz_data["nodes"]
        assert len(nodes) == 4

        node_ids = [n["id"] for n in nodes]
        assert "char1" in node_ids
        assert "char2" in node_ids
        assert "loc1" in node_ids
        assert "fact1" in node_ids

    def test_export_character_node(self, graph):
        """Test character node properties in export."""
        viz_data = graph.export_for_visualization()

        char_node = next(n for n in viz_data["nodes"] if n["id"] == "char1")
        assert char_node["type"] == "character"
        assert char_node["name"] == "林晚"
        assert char_node["tier"] == 0

    def test_export_fact_node(self, graph):
        """Test fact node properties in export."""
        viz_data = graph.export_for_visualization()

        fact_node = next(n for n in viz_data["nodes"] if n["id"] == "fact1")
        assert fact_node["type"] == "fact"
        assert fact_node["fact_type"] == "secret"
        assert fact_node["chapter"] == 3

    def test_export_edges(self, graph):
        """Test edge export for visualization."""
        viz_data = graph.export_for_visualization()

        edges = viz_data["edges"]
        assert len(edges) == 2

        knows_edge = next(e for e in edges if e["label"] == "knows")
        assert knows_edge["source"] == "char1"
        assert knows_edge["target"] in ["char2", "fact1"]
        assert "confidence" in knows_edge

    def test_export_statistics(self, graph):
        """Test statistics in visualization export."""
        viz_data = graph.export_for_visualization()

        stats = viz_data["statistics"]
        assert stats["node_count"] == 4
        assert stats["edge_count"] == 2
        assert "density" in stats
        assert "node_types" in stats
        assert "relation_types" in stats

    def test_export_inferred_edges_marked(self, graph):
        """Test that inferred edges are marked in export."""
        graph.add_character_node("char3", "将军", tier=1)
        graph.add_relationship("char1", "char2", "knows")
        graph.add_relationship("char2", "char3", "knows")
        graph.infer_relationships("char1")

        viz_data = graph.export_for_visualization()

        inferred_edges = [e for e in viz_data["edges"] if e.get("inferred")]
        assert len(inferred_edges) >= 1


class TestCharacterSubgraph:
    """Test character subgraph extraction."""

    @pytest.fixture
    def graph(self):
        """Create a graph for subgraph tests."""
        g = ExtendedCognitiveGraph()
        g.add_character_node("char1", "林晚", tier=0)
        g.add_character_node("char2", "丞相", tier=1)
        g.add_character_node("char3", "将军", tier=1)
        g.add_location_node("loc1", "京城")
        g.add_location_node("loc2", "边关")
        g.add_fact_node("fact1", "secret", "丞相私通敌国", "char2", 3)
        g.add_fact_node("fact2", "event", "边境战事", "char3", 2)
        g.add_relationship("char1", "char2", "knows")
        g.add_relationship("char1", "loc1", "located_at")
        g.add_character_knowledge("char1", "fact1", confidence=0.8)
        return g

    def test_get_character_subgraph(self, graph):
        """Test basic subgraph extraction."""
        subgraph = graph.get_character_subgraph("char1")

        assert subgraph["character_id"] == "char1"
        assert subgraph["node_count"] >= 3
        assert subgraph["edge_count"] >= 2

    def test_subgraph_includes_character(self, graph):
        """Test that subgraph includes the character."""
        subgraph = graph.get_character_subgraph("char1")

        node_ids = [n["id"] for n in subgraph["nodes"]]
        assert "char1" in node_ids

    def test_subgraph_includes_known_facts(self, graph):
        """Test that subgraph includes facts known by character."""
        subgraph = graph.get_character_subgraph("char1")

        node_ids = [n["id"] for n in subgraph["nodes"]]
        assert "fact1" in node_ids

    def test_subgraph_includes_related_characters(self, graph):
        """Test that subgraph includes related characters."""
        subgraph = graph.get_character_subgraph("char1")

        node_ids = [n["id"] for n in subgraph["nodes"]]
        assert "char2" in node_ids

    def test_subgraph_excludes_unrelated(self, graph):
        """Test that subgraph excludes unrelated nodes."""
        subgraph = graph.get_character_subgraph("char1")

        node_ids = [n["id"] for n in subgraph["nodes"]]
        assert "char3" not in node_ids
        assert "fact2" not in node_ids

    def test_subgraph_nonexistent_character(self, graph):
        """Test subgraph for nonexistent character."""
        subgraph = graph.get_character_subgraph("nonexistent")

        assert subgraph["nodes"] == []
        assert subgraph["edges"] == []

    def test_subgraph_edges(self, graph):
        """Test edges in subgraph."""
        subgraph = graph.get_character_subgraph("char1")

        edges = subgraph["edges"]
        assert len(edges) >= 2

        edge_pairs = [(e["from"], e["to"]) for e in edges]
        assert ("char1", "char2") in edge_pairs or ("char1", "fact1") in edge_pairs


class TestIndirectRelationships:
    """Test finding indirect relationships between characters."""

    @pytest.fixture
    def graph(self):
        """Create a graph for path finding tests."""
        g = ExtendedCognitiveGraph()
        g.add_character_node("char1", "林晚", tier=0)
        g.add_character_node("char2", "丞相", tier=1)
        g.add_character_node("char3", "将军", tier=1)
        g.add_character_node("char4", "谋士", tier=2)
        g.add_relationship("char1", "char2", "knows", {"confidence": 0.8})
        g.add_relationship("char2", "char3", "knows", {"confidence": 0.9})
        g.add_relationship("char3", "char4", "knows", {"confidence": 0.7})
        return g

    def test_find_direct_relationship(self, graph):
        """Test finding direct relationship."""
        paths = graph.find_indirect_relationships("char1", "char2")

        assert len(paths) == 1
        assert paths[0]["length"] == 1
        assert paths[0]["path"] == ["char1", "char2"]

    def test_find_indirect_relationship(self, graph):
        """Test finding indirect relationship through intermediate."""
        paths = graph.find_indirect_relationships("char1", "char3")

        assert len(paths) >= 1
        assert paths[0]["length"] == 2
        assert paths[0]["path"] == ["char1", "char2", "char3"]

    def test_find_longer_path(self, graph):
        """Test finding longer path."""
        paths = graph.find_indirect_relationships("char1", "char4")

        assert len(paths) >= 1
        assert paths[0]["length"] == 3
        assert paths[0]["path"] == ["char1", "char2", "char3", "char4"]

    def test_max_depth_limit(self, graph):
        """Test that max_depth limits path length."""
        paths = graph.find_indirect_relationships("char1", "char4", max_depth=2)

        assert len(paths) == 0

    def test_no_relationship_exists(self, graph):
        """Test when no relationship path exists."""
        graph.add_character_node("char5", "陌生人", tier=3)

        paths = graph.find_indirect_relationships("char1", "char5")

        assert len(paths) == 0

    def test_nonexistent_source(self, graph):
        """Test with nonexistent source character."""
        paths = graph.find_indirect_relationships("nonexistent", "char1")

        assert paths == []

    def test_nonexistent_target(self, graph):
        """Test with nonexistent target character."""
        paths = graph.find_indirect_relationships("char1", "nonexistent")

        assert paths == []

    def test_path_confidence(self, graph):
        """Test that path confidence is calculated."""
        paths = graph.find_indirect_relationships("char1", "char3")

        assert paths[0]["confidence"] == pytest.approx(0.8 * 0.9, rel=0.01)

    def test_path_edges_included(self, graph):
        """Test that edges are included in path."""
        paths = graph.find_indirect_relationships("char1", "char2")

        assert len(paths[0]["edges"]) == 1
        assert paths[0]["edges"][0]["from"] == "char1"
        assert paths[0]["edges"][0]["to"] == "char2"


class TestGraphStatistics:
    """Test graph statistics functionality."""

    @pytest.fixture
    def graph(self):
        """Create a graph for statistics tests."""
        g = ExtendedCognitiveGraph()
        g.add_character_node("char1", "林晚", tier=0)
        g.add_character_node("char2", "丞相", tier=1)
        g.add_location_node("loc1", "京城")
        g.add_fact_node("fact1", "secret", "丞相私通敌国", "char2", 3)
        g.add_relationship("char1", "char2", "knows")
        g.add_relationship("char1", "loc1", "located_at")
        g.add_character_knowledge("char1", "fact1")
        return g

    def test_basic_statistics(self, graph):
        """Test basic statistics."""
        stats = graph.get_graph_statistics()

        assert stats["node_count"] == 4
        assert stats["edge_count"] == 3

    def test_node_type_statistics(self, graph):
        """Test node type counting."""
        stats = graph.get_graph_statistics()

        assert stats["node_types"]["character"] == 2
        assert stats["node_types"]["location"] == 1
        assert stats["node_types"]["fact"] == 1

    def test_relation_type_statistics(self, graph):
        """Test relation type counting."""
        stats = graph.get_graph_statistics()

        assert stats["relation_types"]["knows"] == 2
        assert stats["relation_types"]["located_at"] == 1

    def test_density_calculation(self, graph):
        """Test density calculation."""
        stats = graph.get_graph_statistics()

        assert "density" in stats
        assert 0.0 <= stats["density"] <= 1.0

    def test_empty_graph_statistics(self):
        """Test statistics for empty graph."""
        graph = ExtendedCognitiveGraph()
        stats = graph.get_graph_statistics()

        assert stats["node_count"] == 0
        assert stats["edge_count"] == 0
        assert stats["density"] == 0.0
        assert stats["node_types"] == {}
        assert stats["relation_types"] == {}

    def test_average_connections(self, graph):
        """Test average connections calculation."""
        stats = graph.get_graph_statistics()

        assert "avg_connections" in stats
        assert stats["avg_connections"] >= 0.0

    def test_inferred_edge_count(self, graph):
        """Test inferred edge count in statistics."""
        graph.add_relationship("char2", "loc1", "knows")
        graph.infer_relationships("char1")

        stats = graph.get_graph_statistics()

        assert stats["inferred_edge_count"] >= 1


class TestSerialization:
    """Test serialization and deserialization."""

    def test_to_dict_includes_inferred(self):
        """Test that to_dict includes inferred edges."""
        graph = ExtendedCognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)
        graph.add_character_node("char2", "丞相", tier=1)
        graph.add_character_node("char3", "将军", tier=1)
        graph.add_relationship("char1", "char2", "knows")
        graph.add_relationship("char2", "char3", "knows")
        graph.infer_relationships("char1")

        data = graph.to_dict()

        assert "inferred_edges" in data
        assert len(data["inferred_edges"]) == 1

    def test_from_dict_restores_inferred(self):
        """Test that from_dict restores inferred edges."""
        original = ExtendedCognitiveGraph()
        original.add_character_node("char1", "林晚", tier=0)
        original.add_character_node("char2", "丞相", tier=1)
        original.add_character_node("char3", "将军", tier=1)
        original.add_relationship("char1", "char2", "knows")
        original.add_relationship("char2", "char3", "knows")
        original.infer_relationships("char1")

        data = original.to_dict()
        restored = ExtendedCognitiveGraph.from_dict(data)

        assert len(restored._inferred_edges) == 1
        assert len(restored._inference_metadata) == 1

    def test_roundtrip_extended(self):
        """Test full roundtrip serialization."""
        original = ExtendedCognitiveGraph(graph_id="test")
        original.add_character_node("char1", "林晚", tier=0)
        original.add_character_node("char2", "丞相", tier=1)
        original.add_location_node("loc1", "京城")
        original.add_fact_node("fact1", "secret", "丞相私通敌国", "char2", 3)
        original.add_relationship("char1", "char2", "knows", {"confidence": 0.8})
        original.add_character_knowledge("char1", "fact1", confidence=0.7)
        original.add_relationship("char2", "loc1", "knows")
        original.infer_relationships("char1")

        data = original.to_dict()
        restored = ExtendedCognitiveGraph.from_dict(data)

        assert restored.graph_id == original.graph_id
        assert restored.node_count == original.node_count
        assert restored.edge_count == original.edge_count
        assert len(restored._inferred_edges) == len(original._inferred_edges)


class TestInheritance:
    """Test that ExtendedCognitiveGraph properly inherits from CognitiveGraph."""

    def test_inherits_add_character_node(self):
        """Test inherited method add_character_node."""
        graph = ExtendedCognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)

        assert graph.node_count == 1
        node = graph.get_node("char1")
        assert node is not None
        assert node["name"] == "林晚"

    def test_inherits_add_fact_node(self):
        """Test inherited method add_fact_node."""
        graph = ExtendedCognitiveGraph()
        graph.add_fact_node("fact1", "secret", "内容", "char1", 1)

        assert graph.node_count == 1
        node = graph.get_node("fact1")
        assert node is not None
        assert node["fact_type"] == "secret"

    def test_inherits_check_consistency(self):
        """Test inherited method check_consistency."""
        graph = ExtendedCognitiveGraph()
        graph.add_fact_node(
            "fact1", "event", "城门打开", "char1", 1
        )
        graph.add_fact_node(
            "fact2", "event", "城门没打开", "char2", 1
        )

        conflicts = graph.check_consistency("fact1")

        assert len(conflicts) == 1

    def test_inherits_find_conflicts(self):
        """Test inherited method find_conflicts."""
        graph = ExtendedCognitiveGraph()
        graph.add_fact_node(
            "fact1", "event", "城门打开", "char1", 1
        )
        graph.add_fact_node(
            "fact2", "event", "城门没打开", "char2", 1
        )

        conflicts = graph.find_conflicts()

        assert len(conflicts) == 1

    def test_inherits_get_character_knowledge(self):
        """Test inherited method get_character_knowledge."""
        graph = ExtendedCognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)
        graph.add_fact_node("fact1", "event", "事件", "char1", 1)
        graph.add_character_knowledge("char1", "fact1")

        knowledge = graph.get_character_knowledge("char1")

        assert len(knowledge) == 1
