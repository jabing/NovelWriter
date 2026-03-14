"""Tests for KnowledgeGraph class."""

from datetime import datetime

import pytest

from src.novel.knowledge_graph import KnowledgeGraph, create_knowledge_graph
from src.novel.schemas import KnowledgeGraphEdge, KnowledgeGraphNode, KnowledgeGraphQuery


class TestKnowledgeGraphInit:
    """Test KnowledgeGraph initialization."""

    def test_default_initialization(self):
        """Test initialization with default parameters."""
        kg = KnowledgeGraph()

        assert kg.graph_id == "default"
        assert kg.storage_path is None
        assert len(kg._nodes) == 0
        assert len(kg._edges) == 0

    def test_custom_graph_id(self):
        """Test initialization with custom graph ID."""
        kg = KnowledgeGraph(graph_id="test_graph")

        assert kg.graph_id == "test_graph"

    def test_with_storage_path(self, tmp_path):
        """Test initialization with storage path."""
        storage_path = tmp_path / "test_graph"
        kg = KnowledgeGraph(graph_id="test", storage_path=storage_path)

        assert kg.storage_path == storage_path

    def test_load_from_nonexistent_storage(self, tmp_path):
        """Test initialization with non-existent storage path."""
        storage_path = tmp_path / "nonexistent"
        kg = KnowledgeGraph(storage_path=storage_path)

        # Should not raise error
        assert len(kg._nodes) == 0
        assert len(kg._edges) == 0


class TestKnowledgeGraphAddNode:
    """Test node operations."""

    @pytest.fixture
    def kg(self):
        """Create a fresh knowledge graph."""
        return KnowledgeGraph()

    def test_add_node_basic(self, kg):
        """Test adding a basic node."""
        node = kg.add_node(
            node_id="char_001",
            node_type="character",
            properties={"name": "Alice", "age": 25},
        )

        assert isinstance(node, KnowledgeGraphNode)
        assert node.node_id == "char_001"
        assert node.node_type == "character"
        assert node.properties == {"name": "Alice", "age": 25}
        assert node.created_at <= datetime.now()
        assert node.updated_at <= datetime.now()

        # Verify stored
        assert "char_001" in kg._nodes
        assert kg.get_node("char_001") == node

    def test_add_node_with_embeddings(self, kg):
        """Test adding a node with embeddings."""
        embeddings = [0.1, 0.2, 0.3]
        node = kg.add_node(
            node_id="plot_001",
            node_type="plot",
            properties={"title": "Opening scene"},
            embeddings=embeddings,
        )

        assert node.embeddings == embeddings

    def test_add_node_duplicate_id(self, kg):
        """Test adding node with duplicate ID raises error."""
        kg.add_node(
            node_id="test",
            node_type="character",
            properties={},
        )

        with pytest.raises(ValueError, match="already exists"):
            kg.add_node(
                node_id="test",
                node_type="plot",
                properties={},
            )

    def test_add_node_timestamps(self, kg):
        """Test custom timestamps."""
        created = datetime(2025, 1, 1, 12, 0, 0)
        updated = datetime(2025, 1, 2, 12, 0, 0)

        node = kg.add_node(
            node_id="test",
            node_type="character",
            properties={},
            created_at=created,
            updated_at=updated,
        )

        assert node.created_at == created
        assert node.updated_at == updated


class TestKnowledgeGraphUpdateNode:
    """Test node updates."""

    @pytest.fixture
    def kg_with_node(self):
        """Create a knowledge graph with a node."""
        kg = KnowledgeGraph()
        node = kg.add_node(
            node_id="char_001",
            node_type="character",
            properties={"name": "Alice", "age": 25},
        )
        return kg, node

    def test_update_node_properties(self, kg_with_node):
        """Test updating node properties."""
        kg, original_node = kg_with_node

        updated = kg.update_node(
            node_id="char_001",
            properties={"age": 26, "occupation": "Scientist"},
            merge_properties=True,
        )

        assert updated is not None
        assert updated.properties == {
            "name": "Alice",  # Original preserved
            "age": 26,  # Updated
            "occupation": "Scientist",  # Added
        }
        assert updated.updated_at >= original_node.updated_at

    def test_update_node_replace_properties(self, kg_with_node):
        """Test replacing node properties."""
        kg, original_node = kg_with_node

        updated = kg.update_node(
            node_id="char_001",
            properties={"new": "data"},
            merge_properties=False,
        )

        assert updated.properties == {"new": "data"}

    def test_update_node_embeddings(self, kg_with_node):
        """Test updating node embeddings."""
        kg, _ = kg_with_node

        new_embeddings = [0.5, 0.6, 0.7]
        updated = kg.update_node(
            node_id="char_001",
            embeddings=new_embeddings,
        )

        assert updated.embeddings == new_embeddings

    def test_update_nonexistent_node(self, kg_with_node):
        """Test updating non-existent node returns None."""
        kg, _ = kg_with_node

        updated = kg.update_node(
            node_id="nonexistent",
            properties={},
        )

        assert updated is None

    def test_update_node_weight_validation(self, kg_with_node):
        """Test weight validation on edge updates."""
        kg, _ = kg_with_node
        kg.add_node(node_id="char_002", node_type="character", properties={})
        kg.add_edge(
            edge_id="edge_001",
            source_id="char_001",
            target_id="char_002",
            relationship_type="knows",
            weight=0.5,
        )

        # Valid weight
        updated = kg.update_edge("edge_001", weight=0.8)
        assert updated is not None
        assert updated.weight == 0.8

        # Invalid weight
        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            kg.update_edge("edge_001", weight=1.5)


class TestKnowledgeGraphDeleteNode:
    """Test node deletion."""

    @pytest.fixture
    def kg_with_nodes_and_edges(self):
        """Create a knowledge graph with nodes and edges."""
        kg = KnowledgeGraph()
        kg.add_node(node_id="char_001", node_type="character", properties={})
        kg.add_node(node_id="char_002", node_type="character", properties={})
        kg.add_node(node_id="loc_001", node_type="location", properties={})

        kg.add_edge(
            edge_id="edge_001",
            source_id="char_001",
            target_id="char_002",
            relationship_type="knows",
        )
        kg.add_edge(
            edge_id="edge_002",
            source_id="char_001",
            target_id="loc_001",
            relationship_type="located_at",
        )

        return kg

    def test_delete_node_without_cascade(self, kg_with_nodes_and_edges):
        """Test deleting node without cascading."""
        kg = kg_with_nodes_and_edges

        result = kg.delete_node("char_001", cascade=False)

        assert result is True
        assert "char_001" not in kg._nodes
        # Edges should remain (orphaned)
        assert "edge_001" in kg._edges
        assert "edge_002" in kg._edges

    def test_delete_node_with_cascade(self, kg_with_nodes_and_edges):
        """Test deleting node with cascading edge deletion."""
        kg = kg_with_nodes_and_edges

        result = kg.delete_node("char_001", cascade=True)

        assert result is True
        assert "char_001" not in kg._nodes
        # Edges connected to char_001 should be deleted
        assert "edge_001" not in kg._edges
        assert "edge_002" not in kg._edges
        # Other nodes remain
        assert "char_002" in kg._nodes
        assert "loc_001" in kg._nodes

    def test_delete_nonexistent_node(self, kg_with_nodes_and_edges):
        """Test deleting non-existent node returns False."""
        kg = kg_with_nodes_and_edges

        result = kg.delete_node("nonexistent")

        assert result is False


class TestKnowledgeGraphAddEdge:
    """Test edge operations."""

    @pytest.fixture
    def kg_with_nodes(self):
        """Create a knowledge graph with nodes."""
        kg = KnowledgeGraph()
        kg.add_node(node_id="char_001", node_type="character", properties={})
        kg.add_node(node_id="char_002", node_type="character", properties={})
        kg.add_node(node_id="loc_001", node_type="location", properties={})
        return kg

    def test_add_edge_basic(self, kg_with_nodes):
        """Test adding a basic edge."""
        kg = kg_with_nodes

        edge = kg.add_edge(
            edge_id="edge_001",
            source_id="char_001",
            target_id="char_002",
            relationship_type="knows",
        )

        assert isinstance(edge, KnowledgeGraphEdge)
        assert edge.edge_id == "edge_001"
        assert edge.source_id == "char_001"
        assert edge.target_id == "char_002"
        assert edge.relationship_type == "knows"
        assert edge.weight == 1.0
        assert edge.created_at <= datetime.now()

        # Verify stored
        assert "edge_001" in kg._edges
        assert kg.get_edge("edge_001") == edge

    def test_add_edge_with_properties(self, kg_with_nodes):
        """Test adding an edge with properties."""
        kg = kg_with_nodes

        edge = kg.add_edge(
            edge_id="edge_001",
            source_id="char_001",
            target_id="loc_001",
            relationship_type="located_at",
            properties={"since": "2025-01-01", "duration": "2 years"},
        )

        assert edge.properties == {"since": "2025-01-01", "duration": "2 years"}

    def test_add_edge_with_weight(self, kg_with_nodes):
        """Test adding an edge with custom weight."""
        kg = kg_with_nodes

        edge = kg.add_edge(
            edge_id="edge_001",
            source_id="char_001",
            target_id="char_002",
            relationship_type="trusts",
            weight=0.7,
        )

        assert edge.weight == 0.7

    def test_add_edge_duplicate_id(self, kg_with_nodes):
        """Test adding edge with duplicate ID raises error."""
        kg = kg_with_nodes

        kg.add_edge(
            edge_id="edge_001",
            source_id="char_001",
            target_id="char_002",
            relationship_type="knows",
        )

        with pytest.raises(ValueError, match="already exists"):
            kg.add_edge(
                edge_id="edge_001",
                source_id="char_001",
                target_id="loc_001",
                relationship_type="located_at",
            )

    def test_add_edge_missing_source(self, kg_with_nodes):
        """Test adding edge with missing source node raises error."""
        kg = kg_with_nodes

        with pytest.raises(ValueError, match="Source node"):
            kg.add_edge(
                edge_id="edge_001",
                source_id="nonexistent",
                target_id="char_001",
                relationship_type="knows",
            )

    def test_add_edge_missing_target(self, kg_with_nodes):
        """Test adding edge with missing target node raises error."""
        kg = kg_with_nodes

        with pytest.raises(ValueError, match="Target node"):
            kg.add_edge(
                edge_id="edge_001",
                source_id="char_001",
                target_id="nonexistent",
                relationship_type="knows",
            )

    def test_add_edge_invalid_weight(self, kg_with_nodes):
        """Test adding edge with invalid weight raises error."""
        kg = kg_with_nodes

        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            kg.add_edge(
                edge_id="edge_001",
                source_id="char_001",
                target_id="char_002",
                relationship_type="knows",
                weight=2.0,
            )


class TestKnowledgeGraphQuery:
    """Test graph queries."""

    @pytest.fixture
    def kg_with_complex_graph(self):
        """Create a complex graph for testing queries."""
        kg = KnowledgeGraph()

        # Add characters
        kg.add_node(
            node_id="alice",
            node_type="character",
            properties={"name": "Alice", "role": "protagonist"},
        )
        kg.add_node(
            node_id="bob", node_type="character", properties={"name": "Bob", "role": "ally"}
        )
        kg.add_node(
            node_id="charlie",
            node_type="character",
            properties={"name": "Charlie", "role": "antagonist"},
        )
        kg.add_node(
            node_id="diana", node_type="character", properties={"name": "Diana", "role": "ally"}
        )

        # Add locations
        kg.add_node(
            node_id="forest",
            node_type="location",
            properties={"name": "Enchanted Forest", "type": "wilderness"},
        )
        kg.add_node(
            node_id="castle",
            node_type="location",
            properties={"name": "Dark Castle", "type": "fortress"},
        )

        # Add edges (relationships)
        kg.add_edge(
            edge_id="e1", source_id="alice", target_id="bob", relationship_type="friend", weight=0.9
        )
        kg.add_edge(
            edge_id="e2",
            source_id="alice",
            target_id="charlie",
            relationship_type="enemy",
            weight=0.3,
        )
        kg.add_edge(
            edge_id="e3", source_id="bob", target_id="diana", relationship_type="friend", weight=0.8
        )
        kg.add_edge(
            edge_id="e4",
            source_id="charlie",
            target_id="castle",
            relationship_type="owns",
            weight=1.0,
        )
        kg.add_edge(
            edge_id="e5",
            source_id="alice",
            target_id="forest",
            relationship_type="visits",
            weight=0.5,
        )
        kg.add_edge(
            edge_id="e6",
            source_id="bob",
            target_id="forest",
            relationship_type="visits",
            weight=0.4,
        )

        return kg

    def test_query_by_node_type(self, kg_with_complex_graph):
        """Test query filtering by node type."""
        kg = kg_with_complex_graph

        query = KnowledgeGraphQuery(
            node_types=["character"],
            limit=10,
        )

        results = kg.query(query)

        assert len(results) == 4
        assert all(node.node_type == "character" for node in results)
        assert {node.node_id for node in results} == {"alice", "bob", "charlie", "diana"}

    def test_query_by_property(self, kg_with_complex_graph):
        """Test query filtering by property."""
        kg = kg_with_complex_graph

        query = KnowledgeGraphQuery(
            property_filters={"role": "ally"},
            limit=10,
        )

        results = kg.query(query)

        assert len(results) == 2
        assert {node.node_id for node in results} == {"bob", "diana"}

    def test_query_by_node_type_and_property(self, kg_with_complex_graph):
        """Test query filtering by both node type and property."""
        kg = kg_with_complex_graph

        query = KnowledgeGraphQuery(
            node_types=["location"],
            property_filters={"type": "fortress"},
            limit=10,
        )

        results = kg.query(query)

        assert len(results) == 1
        assert results[0].node_id == "castle"

    def test_query_with_relationship_traversal(self, kg_with_complex_graph):
        """Test query with relationship traversal."""
        kg = kg_with_complex_graph

        query = KnowledgeGraphQuery(
            node_types=["character"],
            relationship_types=["friend"],
            depth=2,
            limit=10,
        )

        results = kg.query(query)

        # Should include alice (has friend edge), bob (friend of alice), diana (friend of bob)
        assert len(results) == 3
        assert {node.node_id for node in results} == {"alice", "bob", "diana"}
        # Charlie is not reachable via friend relationships
        assert "charlie" not in {node.node_id for node in results}

    def test_query_limit(self, kg_with_complex_graph):
        """Test query result limiting."""
        kg = kg_with_complex_graph

        query = KnowledgeGraphQuery(
            node_types=["character"],
            limit=2,
        )

        results = kg.query(query)

        assert len(results) == 2

    def test_find_nodes_by_type_method(self, kg_with_complex_graph):
        """Test find_nodes_by_type convenience method."""
        kg = kg_with_complex_graph

        characters = kg.find_nodes_by_type("character")
        locations = kg.find_nodes_by_type("location")

        assert len(characters) == 4
        assert len(locations) == 2

    def test_find_edges_by_relationship_method(self, kg_with_complex_graph):
        """Test find_edges_by_relationship convenience method."""
        kg = kg_with_complex_graph

        friend_edges = kg.find_edges_by_relationship("friend")
        visits_edges = kg.find_edges_by_relationship("visits")

        assert len(friend_edges) == 2
        assert len(visits_edges) == 2


class TestKnowledgeGraphNeighbors:
    """Test neighbor queries."""

    @pytest.fixture
    def kg_with_star_graph(self):
        """Create a star-shaped graph."""
        kg = KnowledgeGraph()

        # Central node
        kg.add_node(node_id="center", node_type="character", properties={})

        # Surrounding nodes
        for i in range(5):
            kg.add_node(node_id=f"node_{i}", node_type="character", properties={})
            kg.add_edge(
                edge_id=f"edge_to_{i}",
                source_id="center",
                target_id=f"node_{i}",
                relationship_type="connected",
            )
            # Add some reverse edges
            if i % 2 == 0:
                kg.add_edge(
                    edge_id=f"edge_from_{i}",
                    source_id=f"node_{i}",
                    target_id="center",
                    relationship_type="connected_reverse",
                )

        return kg

    def test_get_neighbors_outgoing(self, kg_with_star_graph):
        """Test getting outgoing neighbors."""
        kg = kg_with_star_graph

        neighbors = kg.get_neighbors("center", direction="outgoing")

        assert len(neighbors) == 5
        assert {node.node_id for node in neighbors} == {f"node_{i}" for i in range(5)}

    def test_get_neighbors_incoming(self, kg_with_star_graph):
        """Test getting incoming neighbors."""
        kg = kg_with_star_graph

        neighbors = kg.get_neighbors("center", direction="incoming")

        # Only nodes with reverse edges (0, 2, 4)
        assert len(neighbors) == 3
        assert {node.node_id for node in neighbors} == {"node_0", "node_2", "node_4"}

    def test_get_neighbors_both(self, kg_with_star_graph):
        """Test getting neighbors in both directions."""
        kg = kg_with_star_graph

        neighbors = kg.get_neighbors("center", direction="both")

        # All 5 nodes (some appear in both directions but deduplicated)
        assert len(neighbors) == 5

    def test_get_neighbors_filtered_by_relationship(self, kg_with_star_graph):
        """Test getting neighbors filtered by relationship type."""
        kg = kg_with_star_graph

        neighbors = kg.get_neighbors(
            "center", relationship_types=["connected"], direction="outgoing"
        )

        assert len(neighbors) == 5

        neighbors = kg.get_neighbors(
            "center", relationship_types=["connected_reverse"], direction="incoming"
        )

        assert len(neighbors) == 3

    def test_get_neighbors_nonexistent_node(self, kg_with_star_graph):
        """Test getting neighbors of non-existent node returns empty list."""
        kg = kg_with_star_graph

        neighbors = kg.get_neighbors("nonexistent", direction="both")

        assert neighbors == []


class TestKnowledgeGraphShortestPath:
    """Test shortest path finding."""

    @pytest.fixture
    def kg_with_linear_path(self):
        """Create a linear path graph."""
        kg = KnowledgeGraph()

        for i in range(5):
            kg.add_node(node_id=f"node_{i}", node_type="character", properties={})
            if i > 0:
                kg.add_edge(
                    edge_id=f"edge_{i - 1}_{i}",
                    source_id=f"node_{i - 1}",
                    target_id=f"node_{i}",
                    relationship_type="next",
                )

        return kg

    def test_find_shortest_path_linear(self, kg_with_linear_path):
        """Test finding shortest path in linear graph."""
        kg = kg_with_linear_path

        path = kg.find_shortest_path("node_0", "node_4")

        assert path == ["node_0", "node_1", "node_2", "node_3", "node_4"]

    def test_find_shortest_path_same_node(self, kg_with_linear_path):
        """Test finding path from node to itself."""
        kg = kg_with_linear_path

        path = kg.find_shortest_path("node_2", "node_2")

        assert path == ["node_2"]

    def test_find_shortest_path_no_path(self, kg_with_linear_path):
        """Test finding path when none exists."""
        kg = kg_with_linear_path

        # Add disconnected node
        kg.add_node(node_id="isolated", node_type="character", properties={})

        path = kg.find_shortest_path("node_0", "isolated")

        assert path is None

    def test_find_shortest_path_with_relationship_filter(self, kg_with_linear_path):
        """Test finding path with relationship type filter."""
        kg = kg_with_linear_path

        # Add alternative path with different relationship
        kg.add_edge(
            edge_id="alt_edge",
            source_id="node_0",
            target_id="node_4",
            relationship_type="teleport",
        )

        # Filter for "next" relationship only
        path = kg.find_shortest_path("node_0", "node_4", relationship_types=["next"])

        assert path == ["node_0", "node_1", "node_2", "node_3", "node_4"]

        # Filter for "teleport" relationship only
        path = kg.find_shortest_path("node_0", "node_4", relationship_types=["teleport"])

        assert path == ["node_0", "node_4"]

    def test_find_shortest_path_max_depth(self, kg_with_linear_path):
        """Test path finding with max depth limit."""
        kg = kg_with_linear_path

        path = kg.find_shortest_path("node_0", "node_4", max_depth=3)

        # Should find path within depth 3
        assert path is None  # Actually path length 5 > max_depth 3, so no path found

    def test_find_shortest_path_missing_node(self, kg_with_linear_path):
        """Test path finding with missing node."""
        kg = kg_with_linear_path

        path = kg.find_shortest_path("node_0", "nonexistent")

        assert path is None


class TestKnowledgeGraphStorage:
    """Test persistence functionality."""

    def test_save_and_load(self, tmp_path):
        """Test saving graph to storage and loading it back."""
        storage_path = tmp_path / "test_graph"

        # Create and populate graph
        kg1 = KnowledgeGraph(graph_id="test", storage_path=storage_path)
        kg1.add_node(node_id="char_001", node_type="character", properties={"name": "Alice"})
        kg1.add_node(node_id="char_002", node_type="character", properties={"name": "Bob"})
        kg1.add_edge(
            edge_id="edge_001",
            source_id="char_001",
            target_id="char_002",
            relationship_type="knows",
        )

        # Create new graph instance loading from same storage
        kg2 = KnowledgeGraph(graph_id="test", storage_path=storage_path)

        # Verify data loaded
        assert len(kg2._nodes) == 2
        assert len(kg2._edges) == 1

        node = kg2.get_node("char_001")
        assert node is not None
        assert node.properties["name"] == "Alice"

        edge = kg2.get_edge("edge_001")
        assert edge is not None
        assert edge.relationship_type == "knows"

    def test_auto_save_on_mutations(self, tmp_path):
        """Test that mutations trigger auto-save when storage is configured."""
        storage_path = tmp_path / "test_graph"
        kg = KnowledgeGraph(storage_path=storage_path)

        # Add node (should auto-save)
        kg.add_node(node_id="test", node_type="character", properties={})

        # Verify file created
        nodes_file = storage_path / "nodes.json"
        assert nodes_file.exists()

        # Add edge (should auto-save)
        kg.add_node(node_id="test2", node_type="character", properties={})
        kg.add_edge(
            edge_id="edge_001",
            source_id="test",
            target_id="test2",
            relationship_type="knows",
        )

        edges_file = storage_path / "edges.json"
        assert edges_file.exists()

    def test_no_auto_save_without_storage(self):
        """Test that mutations don't crash without storage path."""
        kg = KnowledgeGraph(storage_path=None)

        # Should not raise errors
        kg.add_node(node_id="test", node_type="character", properties={})
        kg.add_node(node_id="test2", node_type="character", properties={})
        kg.add_edge(
            edge_id="edge_001",
            source_id="test",
            target_id="test2",
            relationship_type="knows",
        )


class TestKnowledgeGraphStatistics:
    """Test graph statistics."""

    @pytest.fixture
    def kg_with_data(self):
        """Create a graph with data for statistics."""
        kg = KnowledgeGraph()

        kg.add_node(node_id="char_001", node_type="character", properties={})
        kg.add_node(node_id="char_002", node_type="character", properties={})
        kg.add_node(node_id="loc_001", node_type="location", properties={})

        kg.add_edge(
            edge_id="edge_001",
            source_id="char_001",
            target_id="char_002",
            relationship_type="knows",
        )
        kg.add_edge(
            edge_id="edge_002",
            source_id="char_001",
            target_id="loc_001",
            relationship_type="located_at",
        )

        return kg

    def test_stats(self, kg_with_data):
        """Test stats method."""
        stats = kg_with_data.stats()

        assert stats["total_nodes"] == 3
        assert stats["total_edges"] == 2
        assert "node_types" in stats
        assert "character" in stats["node_types"]
        assert stats["node_types"]["character"] == 2
        assert stats["node_types"]["location"] == 1
        assert "relationship_types" in stats
        assert "knows" in stats["relationship_types"]
        assert stats["relationship_types"]["knows"] == 1
        assert stats["relationship_types"]["located_at"] == 1

    def test_export_to_dict(self, kg_with_data):
        """Test export_to_dict method."""
        export = kg_with_data.export_to_dict()

        assert export["graph_id"] == "default"
        assert "nodes" in export
        assert "edges" in export
        assert "statistics" in export
        assert len(export["nodes"]) == 3
        assert len(export["edges"]) == 2


class TestFactoryFunction:
    """Test create_knowledge_graph factory function."""

    def test_create_with_defaults(self):
        """Test factory with default parameters."""
        kg = create_knowledge_graph()

        assert isinstance(kg, KnowledgeGraph)
        assert kg.graph_id == "default"
        assert kg.storage_path is not None
        assert str(kg.storage_path).replace('\\', '/').endswith('data/knowledge_graphs/default')

    def test_create_with_custom_id(self):
        """Test factory with custom graph ID."""
        kg = create_knowledge_graph(graph_id="my_graph")

        assert kg.graph_id == "my_graph"
        assert str(kg.storage_path).replace('\\', '/').endswith('data/knowledge_graphs/my_graph')

    def test_create_with_custom_path(self, tmp_path):
        """Test factory with custom storage path."""
        custom_path = tmp_path / "custom"
        kg = create_knowledge_graph(graph_id="test", storage_path=custom_path)

        assert kg.storage_path == custom_path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
