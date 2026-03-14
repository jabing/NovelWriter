"""Tests for CognitiveGraph class."""

import pytest

from src.novel_agent.novel.cognitive_graph import CognitiveGraph


class TestCognitiveGraphInit:
    """Test CognitiveGraph initialization."""

    def test_default_initialization(self):
        """Test initialization with default parameters."""
        graph = CognitiveGraph()

        assert graph.graph_id == "default"
        assert graph.node_count == 0
        assert graph.edge_count == 0

    def test_custom_graph_id(self):
        """Test initialization with custom graph ID."""
        graph = CognitiveGraph(graph_id="test")

        assert graph.graph_id == "test"


class TestCognitiveGraphNodes:
    """Test node operations."""

    @pytest.fixture
    def graph(self):
        """Create a fresh graph for each test."""
        return CognitiveGraph()

    def test_add_character_node(self, graph):
        """Test adding character nodes."""
        graph.add_character_node("char1", "Alice", tier=0)

        assert graph.node_count == 1
        node = graph.get_node("char1")
        assert node["node_type"] == "character"
        assert node["name"] == "Alice"
        assert node["tier"] == 0

    def test_add_character_node_with_properties(self, graph):
        """Test adding character nodes with additional properties."""
        graph.add_character_node("char1", "Alice", tier=0, properties={"age": 25, "role": "protagonist"})

        node = graph.get_node("char1")
        assert node["age"] == 25
        assert node["role"] == "protagonist"

    def test_add_location_node(self, graph):
        """Test adding location nodes."""
        graph.add_location_node("loc1", "Beijing")

        assert graph.node_count == 1
        node = graph.get_node("loc1")
        assert node["node_type"] == "location"
        assert node["name"] == "Beijing"

    def test_add_location_node_with_properties(self, graph):
        """Test adding location nodes with additional properties."""
        graph.add_location_node("loc1", "Beijing", properties={"country": "China", "population": 21000000})

        node = graph.get_node("loc1")
        assert node["country"] == "China"
        assert node["population"] == 21000000

    def test_add_plot_thread_node(self, graph):
        """Test adding plot thread nodes."""
        graph.add_plot_thread_node("thread1", "Main Plot")

        assert graph.node_count == 1
        node = graph.get_node("thread1")
        assert node["node_type"] == "plot_thread"
        assert node["name"] == "Main Plot"

    def test_add_plot_thread_node_with_properties(self, graph):
        """Test adding plot thread nodes with additional properties."""
        graph.add_plot_thread_node("thread1", "Main Plot", properties={"status": "active", "priority": 1})

        node = graph.get_node("thread1")
        assert node["status"] == "active"
        assert node["priority"] == 1

    def test_get_node_nonexistent(self, graph):
        """Test getting a nonexistent node."""
        result = graph.get_node("nonexistent")

        assert result is None

    def test_get_nodes_by_type(self, graph):
        """Test filtering nodes by type."""
        graph.add_character_node("char1", "Alice", tier=0)
        graph.add_character_node("char2", "Bob", tier=1)
        graph.add_location_node("loc1", "Beijing")

        characters = graph.get_nodes_by_type("character")
        assert len(characters) == 2
        assert "char1" in characters
        assert "char2" in characters

        locations = graph.get_nodes_by_type("location")
        assert locations == ["loc1"]

        plot_threads = graph.get_nodes_by_type("plot_thread")
        assert plot_threads == []

    def test_remove_node(self, graph):
        """Test removing nodes."""
        graph.add_character_node("char1", "Alice", tier=0)

        assert graph.node_count == 1

        result = graph.remove_node("char1")
        assert result is True
        assert graph.node_count == 0

    def test_remove_nonexistent_node(self, graph):
        """Test removing a nonexistent node."""
        result = graph.remove_node("nonexistent")

        assert result is False

    def test_remove_node_with_edges(self, graph):
        """Test removing a node that has edges."""
        graph.add_character_node("char1", "Alice", tier=0)
        graph.add_location_node("loc1", "Beijing")
        graph.add_relationship("char1", "loc1", "located_at")

        assert graph.node_count == 2
        assert graph.edge_count == 1

        graph.remove_node("char1")

        assert graph.node_count == 1
        assert graph.edge_count == 0  # Edge should be removed too


class TestCognitiveGraphEdges:
    """Test edge/relationship operations."""

    @pytest.fixture
    def graph(self):
        """Create a graph with some nodes for edge tests."""
        g = CognitiveGraph()
        g.add_character_node("char1", "Alice", tier=0)
        g.add_character_node("char2", "Bob", tier=1)
        g.add_location_node("loc1", "Beijing")
        return g

    def test_add_relationship(self, graph):
        """Test adding relationships."""
        graph.add_relationship("char1", "loc1", "located_at")

        assert graph.edge_count == 1

    def test_add_relationship_with_properties(self, graph):
        """Test adding relationships with properties."""
        graph.add_relationship("char1", "char2", "knows", {"confidence": 0.9})

        edge_data = graph.graph.get_edge_data("char1", "char2")
        assert edge_data["relation_type"] == "knows"
        assert edge_data["confidence"] == 0.9

    def test_get_neighbors(self, graph):
        """Test getting neighbors."""
        graph.add_relationship("char1", "loc1", "located_at")

        neighbors = graph.get_neighbors("char1")
        assert neighbors == ["loc1"]

    def test_get_neighbors_nonexistent_node(self, graph):
        """Test getting neighbors for a nonexistent node."""
        neighbors = graph.get_neighbors("nonexistent")

        assert neighbors == []

    def test_get_neighbors_filtered(self, graph):
        """Test filtering neighbors by relation type."""
        graph.add_relationship("char1", "char2", "knows")
        graph.add_relationship("char1", "loc1", "located_at")

        knows_neighbors = graph.get_neighbors("char1", relation_type="knows")
        assert knows_neighbors == ["char2"]

        located_neighbors = graph.get_neighbors("char1", relation_type="located_at")
        assert located_neighbors == ["loc1"]

    def test_get_neighbors_no_match(self, graph):
        """Test filtering neighbors with no matches."""
        graph.add_relationship("char1", "char2", "knows")

        located_neighbors = graph.get_neighbors("char1", relation_type="located_at")
        assert located_neighbors == []

    def test_get_relationships(self, graph):
        """Test getting all relationships for a node."""
        graph.add_relationship("char1", "char2", "knows")
        graph.add_relationship("char1", "loc1", "located_at")

        relationships = graph.get_relationships("char1")

        assert len(relationships) == 2
        relation_types = [r[2]["relation_type"] for r in relationships]
        assert "knows" in relation_types
        assert "located_at" in relation_types

    def test_get_relationships_incoming(self, graph):
        """Test getting incoming relationships."""
        graph.add_relationship("char1", "char2", "knows")

        # char2 should see incoming relationship from char1
        relationships = graph.get_relationships("char2")

        assert len(relationships) == 1
        assert relationships[0][0] == "char1"  # from_id
        assert relationships[0][1] == "char2"  # to_id

    def test_get_relationships_filtered(self, graph):
        """Test filtering relationships by type."""
        graph.add_relationship("char1", "char2", "knows")
        graph.add_relationship("char1", "loc1", "located_at")

        knows_rels = graph.get_relationships("char1", relation_type="knows")

        assert len(knows_rels) == 1
        assert knows_rels[0][2]["relation_type"] == "knows"

    def test_get_relationships_nonexistent_node(self, graph):
        """Test getting relationships for a nonexistent node."""
        relationships = graph.get_relationships("nonexistent")

        assert relationships == []


class TestCognitiveGraphSerialization:
    """Test serialization and deserialization."""

    def test_to_dict_empty(self):
        """Test serializing an empty graph."""
        graph = CognitiveGraph(graph_id="test")
        data = graph.to_dict()

        assert data["graph_id"] == "test"
        assert data["nodes"] == []
        assert data["edges"] == []

    def test_to_dict_with_data(self):
        """Test serializing a graph with data."""
        graph = CognitiveGraph(graph_id="test")
        graph.add_character_node("char1", "Alice", tier=0, properties={"age": 25})
        graph.add_location_node("loc1", "Beijing")
        graph.add_relationship("char1", "loc1", "located_at", {"confidence": 0.9})

        data = graph.to_dict()

        assert data["graph_id"] == "test"
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1

        # Check nodes
        node_ids = [n["id"] for n in data["nodes"]]
        assert "char1" in node_ids
        assert "loc1" in node_ids

        # Check edge
        edge = data["edges"][0]
        assert edge["from"] == "char1"
        assert edge["to"] == "loc1"
        assert edge["relation_type"] == "located_at"
        assert edge["confidence"] == 0.9

    def test_from_dict_empty(self):
        """Test deserializing an empty graph."""
        data = {
            "graph_id": "test",
            "nodes": [],
            "edges": [],
        }

        graph = CognitiveGraph.from_dict(data)

        assert graph.graph_id == "test"
        assert graph.node_count == 0
        assert graph.edge_count == 0

    def test_from_dict_with_data(self):
        """Test deserializing a graph with data."""
        data = {
            "graph_id": "test",
            "nodes": [
                {"id": "char1", "node_type": "character", "name": "Alice", "tier": 0, "age": 25},
                {"id": "loc1", "node_type": "location", "name": "Beijing"},
            ],
            "edges": [
                {"from": "char1", "to": "loc1", "relation_type": "located_at", "confidence": 0.9},
            ],
        }

        graph = CognitiveGraph.from_dict(data)

        assert graph.graph_id == "test"
        assert graph.node_count == 2
        assert graph.edge_count == 1

        # Verify data integrity
        node = graph.get_node("char1")
        assert node["name"] == "Alice"
        assert node["age"] == 25

        neighbors = graph.get_neighbors("char1")
        assert neighbors == ["loc1"]

    def test_roundtrip(self):
        """Test serialization roundtrip."""
        original = CognitiveGraph(graph_id="test")
        original.add_character_node("char1", "Alice", tier=0, properties={"age": 25})
        original.add_location_node("loc1", "Beijing")
        original.add_relationship("char1", "loc1", "located_at", {"confidence": 0.9})

        # Serialize and deserialize
        data = original.to_dict()
        restored = CognitiveGraph.from_dict(data)

        # Compare
        assert restored.graph_id == original.graph_id
        assert restored.node_count == original.node_count
        assert restored.edge_count == original.edge_count

        # Verify node data
        original_node = original.get_node("char1")
        restored_node = restored.get_node("char1")
        assert restored_node["name"] == original_node["name"]
        assert restored_node["age"] == original_node["age"]


class TestCognitiveGraphClear:
    """Test graph clearing."""

    def test_clear(self):
        """Test clearing the graph."""
        graph = CognitiveGraph()
        graph.add_character_node("char1", "Alice", tier=0)
        graph.add_location_node("loc1", "Beijing")
        graph.add_relationship("char1", "loc1", "located_at")

        assert graph.node_count == 2
        assert graph.edge_count == 1

        graph.clear()

        assert graph.node_count == 0
        assert graph.edge_count == 0

    def test_clear_empty_graph(self):
        """Test clearing an already empty graph."""
        graph = CognitiveGraph()

        graph.clear()  # Should not raise

        assert graph.node_count == 0
        assert graph.edge_count == 0


class TestCognitiveGraphFacts:
    """Test fact node operations."""

    @pytest.fixture
    def graph(self):
        """Create a fresh graph for each test."""
        return CognitiveGraph()

    def test_add_fact_node(self, graph):
        """Test adding a fact node."""
        graph.add_fact_node(
            "fact1",
            fact_type="event",
            content="林晚在第三章遇见了丞相",
            source_character="char1",
            chapter=3,
        )

        assert graph.node_count == 1
        node = graph.get_node("fact1")
        assert node["node_type"] == "fact"
        assert node["fact_type"] == "event"
        assert node["content"] == "林晚在第三章遇见了丞相"
        assert node["source_character"] == "char1"
        assert node["chapter"] == 3

    def test_add_fact_node_with_properties(self, graph):
        """Test adding a fact node with additional properties."""
        graph.add_fact_node(
            "fact1",
            fact_type="secret",
            content="丞相其实是林晚的亲生父亲",
            source_character="char2",
            chapter=5,
            properties={"importance": "high", "verified": True},
        )

        node = graph.get_node("fact1")
        assert node["importance"] == "high"
        assert node["verified"] is True

    def test_get_facts_for_character_source(self, graph):
        """Test getting facts where character is the source."""
        graph.add_character_node("char1", "林晚", tier=0)
        graph.add_fact_node(
            "fact1",
            fact_type="event",
            content="林晚参加了宴会",
            source_character="char1",
            chapter=1,
        )
        graph.add_fact_node(
            "fact2",
            fact_type="event",
            content="丞相出席了宴会",
            source_character="char2",
            chapter=1,
        )

        facts = graph.get_facts_for_character("char1")

        assert len(facts) == 1
        assert facts[0]["id"] == "fact1"

    def test_get_facts_for_character_with_knowledge(self, graph):
        """Test getting facts known by a character via knows relation."""
        graph.add_character_node("char1", "林晚", tier=0)
        graph.add_character_node("char2", "丞相", tier=1)
        graph.add_fact_node(
            "fact1",
            fact_type="secret",
            content="丞相计划叛变",
            source_character="char2",
            chapter=3,
        )
        graph.add_character_knowledge("char1", "fact1", confidence=0.8, source="hearsay")

        facts = graph.get_facts_for_character("char1")

        assert len(facts) == 1
        assert facts[0]["id"] == "fact1"

    def test_get_facts_by_type(self, graph):
        """Test filtering facts by type."""
        graph.add_fact_node(
            "fact1",
            fact_type="event",
            content="发生了一场战斗",
            source_character="char1",
            chapter=1,
        )
        graph.add_fact_node(
            "fact2",
            fact_type="secret",
            content="主角隐藏了身份",
            source_character="char1",
            chapter=2,
        )
        graph.add_fact_node(
            "fact3",
            fact_type="event",
            content="签订了和平条约",
            source_character="char2",
            chapter=3,
        )

        events = graph.get_facts_by_type("event")
        secrets = graph.get_facts_by_type("secret")

        assert len(events) == 2
        assert len(secrets) == 1
        event_ids = [f["id"] for f in events]
        assert "fact1" in event_ids
        assert "fact3" in event_ids
        assert secrets[0]["id"] == "fact2"

    def test_get_facts_by_type_empty(self, graph):
        """Test getting facts when none exist for type."""
        graph.add_fact_node(
            "fact1",
            fact_type="event",
            content="某个事件",
            source_character="char1",
            chapter=1,
        )

        secrets = graph.get_facts_by_type("secret")

        assert secrets == []


class TestCognitiveGraphKnowledge:
    """Test character knowledge operations."""

    @pytest.fixture
    def graph(self):
        """Create a graph with characters and facts for knowledge tests."""
        g = CognitiveGraph()
        g.add_character_node("char1", "林晚", tier=0)
        g.add_character_node("char2", "丞相", tier=1)
        g.add_fact_node(
            "fact1",
            fact_type="event",
            content="林晚在边境发现敌军",
            source_character="char1",
            chapter=1,
        )
        g.add_fact_node(
            "fact2",
            fact_type="secret",
            content="丞相私通敌国",
            source_character="char2",
            chapter=2,
        )
        return g

    def test_add_character_knowledge(self, graph):
        """Test adding knowledge relationship."""
        graph.add_character_knowledge("char2", "fact1", confidence=0.9, source="direct")

        assert graph.edge_count == 1
        edge_data = graph.graph.get_edge_data("char2", "fact1")
        assert edge_data["relation_type"] == "knows"
        assert edge_data["confidence"] == 0.9
        assert edge_data["source"] == "direct"

    def test_add_character_knowledge_defaults(self, graph):
        """Test adding knowledge with default values."""
        graph.add_character_knowledge("char1", "fact2")

        edge_data = graph.graph.get_edge_data("char1", "fact2")
        assert edge_data["confidence"] == 1.0
        assert edge_data["source"] == "direct"

    def test_get_character_knowledge(self, graph):
        """Test getting all knowledge for a character."""
        graph.add_character_knowledge("char1", "fact2", confidence=0.7, source="inference")
        graph.add_character_knowledge("char2", "fact1", confidence=0.9, source="direct")

        knowledge = graph.get_character_knowledge("char1")

        assert len(knowledge) == 1
        fact_data, confidence, source = knowledge[0]
        assert fact_data["id"] == "fact2"
        assert confidence == 0.7
        assert source == "inference"

    def test_get_character_knowledge_multiple(self, graph):
        """Test getting multiple facts known by a character."""
        graph.add_character_knowledge("char1", "fact1", confidence=1.0, source="direct")
        graph.add_character_knowledge("char1", "fact2", confidence=0.5, source="hearsay")

        knowledge = graph.get_character_knowledge("char1")

        assert len(knowledge) == 2
        fact_ids = [k[0]["id"] for k in knowledge]
        assert "fact1" in fact_ids
        assert "fact2" in fact_ids

    def test_get_character_knowledge_empty(self, graph):
        """Test getting knowledge for character with no facts."""
        knowledge = graph.get_character_knowledge("char2")

        assert knowledge == []

    def test_get_character_knowledge_nonexistent_character(self, graph):
        """Test getting knowledge for nonexistent character."""
        knowledge = graph.get_character_knowledge("nonexistent")

        assert knowledge == []


class TestCognitiveGraphConsistency:
    """Test consistency check operations."""

    @pytest.fixture
    def graph(self):
        """Create a fresh graph for consistency tests."""
        return CognitiveGraph()

    def test_check_consistency_no_conflicts(self, graph):
        """Test checking consistency with no conflicts."""
        graph.add_fact_node(
            "fact1",
            fact_type="event",
            content="林晚参加了宴会",
            source_character="char1",
            chapter=1,
        )
        graph.add_fact_node(
            "fact2",
            fact_type="event",
            content="丞相出席了会议",
            source_character="char2",
            chapter=1,
        )

        conflicts = graph.check_consistency("fact1")

        assert conflicts == []

    def test_check_consistency_with_negation_conflict(self, graph):
        """Test detecting conflict with negation pattern."""
        graph.add_fact_node(
            "fact1",
            fact_type="event",
            content="林晚去京城",
            source_character="char1",
            chapter=1,
        )
        graph.add_fact_node(
            "fact2",
            fact_type="event",
            content="林晚没去京城",
            source_character="char2",
            chapter=1,
        )

        conflicts = graph.check_consistency("fact1")

        assert len(conflicts) == 1
        assert conflicts[0]["id"] == "fact2"

    def test_check_consistency_different_types_no_conflict(self, graph):
        """Test that different fact types don't conflict."""
        graph.add_fact_node(
            "fact1",
            fact_type="event",
            content="林晚去了京城",
            source_character="char1",
            chapter=1,
        )
        graph.add_fact_node(
            "fact2",
            fact_type="secret",
            content="林晚去了京城",
            source_character="char2",
            chapter=1,
        )

        conflicts = graph.check_consistency("fact1")

        assert conflicts == []

    def test_check_consistency_nonexistent_fact(self, graph):
        """Test checking consistency for nonexistent fact."""
        conflicts = graph.check_consistency("nonexistent")

        assert conflicts == []

    def test_check_consistency_non_fact_node(self, graph):
        """Test checking consistency for non-fact node."""
        graph.add_character_node("char1", "林晚", tier=0)

        conflicts = graph.check_consistency("char1")

        assert conflicts == []

    def test_find_conflicts_none(self, graph):
        """Test finding conflicts when there are none."""
        graph.add_fact_node(
            "fact1",
            fact_type="event",
            content="林晚去了京城",
            source_character="char1",
            chapter=1,
        )
        graph.add_fact_node(
            "fact2",
            fact_type="event",
            content="丞相去了江南",
            source_character="char2",
            chapter=1,
        )

        conflicts = graph.find_conflicts()

        assert conflicts == []

    def test_find_conflicts_with_negation(self, graph):
        """Test finding conflicts with negation patterns."""
        graph.add_fact_node(
            "fact1",
            fact_type="event",
            content="林晚知道这个秘密",
            source_character="char1",
            chapter=1,
        )
        graph.add_fact_node(
            "fact2",
            fact_type="event",
            content="林晚不知道这个秘密",
            source_character="char2",
            chapter=2,
        )

        conflicts = graph.find_conflicts()

        assert len(conflicts) == 1
        fact_ids = {conflicts[0][0]["id"], conflicts[0][1]["id"]}
        assert fact_ids == {"fact1", "fact2"}

    def test_find_conflicts_multiple_pairs(self, graph):
        """Test finding multiple conflict pairs."""
        graph.add_fact_node(
            "fact1",
            fact_type="event",
            content="城门打开",
            source_character="char1",
            chapter=1,
        )
        graph.add_fact_node(
            "fact2",
            fact_type="event",
            content="城门没打开",
            source_character="char2",
            chapter=1,
        )
        graph.add_fact_node(
            "fact3",
            fact_type="secret",
            content="他是刺客",
            source_character="char1",
            chapter=2,
        )
        graph.add_fact_node(
            "fact4",
            fact_type="secret",
            content="他不是刺客",
            source_character="char2",
            chapter=2,
        )

        conflicts = graph.find_conflicts()

        assert len(conflicts) == 2

    def test_find_conflicts_english_negation(self, graph):
        """Test finding conflicts with English negation patterns."""
        graph.add_fact_node(
            "fact1",
            fact_type="event",
            content="john is an assassin",
            source_character="char1",
            chapter=1,
        )
        graph.add_fact_node(
            "fact2",
            fact_type="event",
            content="john is not an assassin",
            source_character="char2",
            chapter=1,
        )

        conflicts = graph.find_conflicts()

        assert len(conflicts) == 1
