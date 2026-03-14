"""KnowledgeGraph performance benchmark for 200+ chapter scenarios.

This module tests KnowledgeGraph query performance with large-scale data:
- 200+ chapters worth of facts and relationships
- Multiple character arcs and plot threads
- Query performance targets: < 1s for complex queries
"""

import time
from pathlib import Path
from typing import Any

import pytest

from src.novel.knowledge_graph import KnowledgeGraph
from src.novel.schemas import KnowledgeGraphQuery


class TestKnowledgeGraphPerformance:
    """Performance tests for KnowledgeGraph at 200+ chapter scale."""

    @pytest.fixture
    def large_knowledge_graph(self, tmp_path: Path) -> KnowledgeGraph:
        """Create a knowledge graph with 200 chapters of data.
        
        Creates:
        - 400+ character nodes (main, supporting, minor characters)
        - 200 location nodes
        - 300 plot thread nodes
        - 100+ concept nodes
        - 1000+ relationship edges
        """
        storage = tmp_path / "perf_test_kg"
        kg = KnowledgeGraph(graph_id="perf_200chapters", storage_path=storage)
        
        # Create characters with varying importance
        character_types = [
            ("main", 10, 0.9),      # 10 main characters, high weight
            ("supporting", 40, 0.7),  # 40 supporting characters
            ("minor", 350, 0.5),     # 350 minor characters
        ]
        
        char_id = 0
        for char_type, count, base_weight in character_types:
            for i in range(count):
                node_id = f"char_{char_type}_{i}"
                first_appearance = (char_id % 200) + 1
                appearances = [
                    first_appearance,
                    min(first_appearance + 5, 200),
                    min(first_appearance + 20, 200),
                ]
                
                kg.add_node(
                    node_id=node_id,
                    node_type="character",
                    properties={
                        "name": f"Character {char_type.title()} {i}",
                        "type": char_type,
                        "first_appearance": first_appearance,
                        "appearances": appearances,
                        "status": "active" if char_type != "minor" else "inactive",
                        "chapter_introduced": first_appearance,
                    },
                )
                char_id += 1
        
        # Create locations
        location_types = [
            ("main", 20, True),    # 20 main locations
            ("secondary", 80, False),  # 80 secondary locations
            ("minor", 100, False),     # 100 minor locations
        ]
        
        loc_id = 0
        for loc_type, count, is_main in location_types:
            for i in range(count):
                node_id = f"loc_{loc_type}_{i}"
                first_appearance = (loc_id % 200) + 1
                
                kg.add_node(
                    node_id=node_id,
                    node_type="location",
                    properties={
                        "name": f"Location {loc_type.title()} {i}",
                        "type": loc_type,
                        "is_main": is_main,
                        "first_appearance": first_appearance,
                        "appearances": [first_appearance, min(first_appearance + 10, 200)],
                    },
                )
                loc_id += 1
        
        # Create plot threads
        for i in range(300):
            node_id = f"plot_{i}"
            start_chapter = (i % 200) + 1
            
            kg.add_node(
                node_id=node_id,
                node_type="plot",
                properties={
                    "name": f"Plot Thread {i}",
                    "status": "active" if i < 100 else "resolved",
                    "start_chapter": start_chapter,
                    "end_chapter": min(start_chapter + 50, 200),
                    "priority": "high" if i < 50 else "medium",
                },
            )
        
        # Create concepts/abilities/items
        for i in range(100):
            node_id = f"concept_{i}"
            
            kg.add_node(
                node_id=node_id,
                node_type="concept",
                properties={
                    "name": f"Concept {i}",
                    "category": "ability" if i % 3 == 0 else "item" if i % 3 == 1 else "lore",
                    "importance": "critical" if i < 20 else "normal",
                },
            )
        
        # Create relationships between entities
        edge_id = 0
        
        # Character relationships (family, friends, rivals, etc.)
        for i in range(10):  # Main characters
            source_id = f"char_main_{i}"
            
            # Family relationships
            for j in range(3):
                target_id = f"char_supporting_{i * 4 + j}"
                kg.add_edge(
                    edge_id=f"edge_{edge_id}",
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type="family",
                    weight=0.9,
                    properties={
                        "relation": "sibling" if j == 0 else "cousin",
                        "chapter_introduced": (i * 5 + j) % 200 + 1,
                    },
                )
                edge_id += 1
            
            # Friend/ally relationships
            for j in range(5):
                target_id = f"char_supporting_{(i + j) % 40}"
                kg.add_edge(
                    edge_id=f"edge_{edge_id}",
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type="ally",
                    weight=0.7 + (j * 0.05),
                    properties={
                        "relation": "friend",
                        "chapter_introduced": (i * 10 + j) % 200 + 1,
                    },
                )
                edge_id += 1
            
            # Rival relationships
            for j in range(2):
                target_id = f"char_main_{(i + j + 1) % 10}"
                kg.add_edge(
                    edge_id=f"edge_{edge_id}",
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type="rival",
                    weight=0.8,
                    properties={
                        "relation": "competitor",
                        "chapter_introduced": (i * 15 + j) % 200 + 1,
                    },
                )
                edge_id += 1
        
        # Character-Location relationships (visited, lives_at, etc.)
        for i in range(400):
            char_type_idx = i % 3
            char_types = ["main", "supporting", "minor"]
            char_counts = [10, 40, 350]
            char_type = char_types[char_type_idx]
            char_idx = i % char_counts[char_type_idx]
            
            loc_type_idx = i % 3
            loc_types = ["main", "secondary", "minor"]
            loc_counts = [20, 80, 100]
            loc_type = loc_types[loc_type_idx]
            loc_idx = i % loc_counts[loc_type_idx]
            
            char_id_str = f"char_{char_type}_{char_idx}"
            loc_id_str = f"loc_{loc_type}_{loc_idx}"
            
            kg.add_edge(
                edge_id=f"edge_{edge_id}",
                source_id=char_id_str,
                target_id=loc_id_str,
                relationship_type="visited",
                weight=0.5 + ((i % 50) / 100),
                properties={
                    "chapter": (i % 200) + 1,
                    "duration": "brief" if i % 3 == 0 else "extended",
                },
            )
            edge_id += 1
        
        # Character-Plot relationships (involved_in, leads, etc.)
        for i in range(300):
            if i < 100:
                char_type = "main"
                char_idx = i % 10
            elif i < 250:
                char_type = "supporting"
                char_idx = i % 40
            else:
                char_type = "minor"
                char_idx = i % 350
            
            char_id_str = f"char_{char_type}_{char_idx}"
            plot_id_str = f"plot_{i % 300}"
            
            kg.add_edge(
                edge_id=f"edge_{edge_id}",
                source_id=char_id_str,
                target_id=plot_id_str,
                relationship_type="involved_in",
                weight=0.6 + ((i % 40) / 100),
                properties={
                    "role": "protagonist" if i < 50 else "supporting" if i < 150 else "minor",
                    "chapter_introduced": (i % 200) + 1,
                },
            )
            edge_id += 1
        
        # Concept relationships (related_to, enables, etc.)
        for i in range(100):
            source_id = f"concept_{i}"
            target_id = f"concept_{(i + 1) % 100}"
            
            kg.add_edge(
                edge_id=f"edge_{edge_id}",
                source_id=source_id,
                target_id=target_id,
                relationship_type="related_to",
                weight=0.5,
                properties={
                    "relation": "prerequisite" if i % 2 == 0 else "complementary",
                },
            )
            edge_id += 1
        
        # Character-Concept relationships (has_ability, owns_item, knows_lore)
        for i in range(200):
            if i < 50:
                char_type = "main"
                char_idx = i % 10
            elif i < 150:
                char_type = "supporting"
                char_idx = i % 40
            else:
                char_type = "minor"
                char_idx = i % 350
            
            char_id_str = f"char_{char_type}_{char_idx}"
            concept_id_str = f"concept_{i % 100}"
            
            rel_type = "has_ability" if i % 3 == 0 else "owns_item" if i % 3 == 1 else "knows_lore"
            
            kg.add_edge(
                edge_id=f"edge_{edge_id}",
                source_id=char_id_str,
                target_id=concept_id_str,
                relationship_type=rel_type,
                weight=0.7,
                properties={
                    "chapter_acquired": (i % 200) + 1,
                },
            )
            edge_id += 1
        
        return kg

    def test_graph_initialization_stats(self, large_knowledge_graph: KnowledgeGraph) -> None:
        """Verify the test graph has expected scale."""
        stats = large_knowledge_graph.stats()
        
        print(f"\n=== Knowledge Graph Statistics ===")
        print(f"Total Nodes: {stats['total_nodes']}")
        print(f"Total Edges: {stats['total_edges']}")
        print(f"Node Types: {stats['node_types']}")
        print(f"Relationship Types: {stats['relationship_types']}")
        print(f"Average Degree: {stats['avg_degree']:.2f}")
        
        # Verify scale
        assert stats["total_nodes"] >= 1000, "Graph should have 1000+ nodes"
        assert stats["total_edges"] >= 1000, "Graph should have 1000+ edges"
        assert "character" in stats["node_types"], "Should have character nodes"
        assert "location" in stats["node_types"], "Should have location nodes"
        assert "plot" in stats["node_types"], "Should have plot nodes"

    def test_query_performance_all_nodes(self, large_knowledge_graph: KnowledgeGraph) -> None:
        """Test performance of getting all nodes."""
        start = time.time()
        nodes = large_knowledge_graph.get_all_nodes()
        duration_ms = (time.time() - start) * 1000
        
        print(f"\n=== Get All Nodes Performance ===")
        print(f"Retrieved {len(nodes)} nodes in {duration_ms:.2f}ms")
        
        assert duration_ms < 100, f"get_all_nodes() should be < 100ms, got {duration_ms:.2f}ms"
        assert len(nodes) >= 1000

    def test_query_performance_find_nodes_by_type(self, large_knowledge_graph: KnowledgeGraph) -> None:
        """Test performance of finding nodes by type."""
        start = time.time()
        characters = large_knowledge_graph.find_nodes_by_type("character")
        duration_ms = (time.time() - start) * 1000
        
        print(f"\n=== Find Nodes By Type Performance ===")
        print(f"Found {len(characters)} characters in {duration_ms:.2f}ms")
        
        assert duration_ms < 50, f"find_nodes_by_type() should be < 50ms, got {duration_ms:.2f}ms"
        assert len(characters) == 400  # 10 + 40 + 350

    def test_query_performance_get_relationships(self, large_knowledge_graph: KnowledgeGraph) -> None:
        """Test performance of getting relationships for a character."""
        start = time.time()
        relations = large_knowledge_graph.get_relationships(source_id="char_main_0")
        duration_ms = (time.time() - start) * 1000
        
        print(f"\n=== Get Relationships Performance ===")
        print(f"Found {len(relations)} relationships in {duration_ms:.2f}ms")
        
        assert duration_ms < 50, f"get_relationships() should be < 50ms, got {duration_ms:.2f}ms"
        assert len(relations) > 0

    def test_query_performance_get_neighbors(self, large_knowledge_graph: KnowledgeGraph) -> None:
        """Test performance of getting neighbors for a node."""
        start = time.time()
        neighbors = large_knowledge_graph.get_neighbors("char_main_0")
        duration_ms = (time.time() - start) * 1000
        
        print(f"\n=== Get Neighbors Performance ===")
        print(f"Found {len(neighbors)} neighbors in {duration_ms:.2f}ms")
        
        assert duration_ms < 50, f"get_neighbors() should be < 50ms, got {duration_ms:.2f}ms"
        assert len(neighbors) > 0

    def test_query_performance_complex_query(self, large_knowledge_graph: KnowledgeGraph) -> None:
        """Test performance of complex graph query with traversal."""
        query = KnowledgeGraphQuery(
            node_types=["character"],
            relationship_types=["ally", "family"],
            property_filters={"type": "main"},
            depth=2,
            limit=100,
        )
        
        start = time.time()
        results = large_knowledge_graph.query(query)
        duration_ms = (time.time() - start) * 1000
        
        print(f"\n=== Complex Query Performance ===")
        print(f"Query returned {len(results)} results in {duration_ms:.2f}ms")
        
        assert duration_ms < 100, f"Complex query should be < 100ms, got {duration_ms:.2f}ms"

    def test_query_performance_shortest_path(self, large_knowledge_graph: KnowledgeGraph) -> None:
        """Test performance of shortest path finding."""
        start = time.time()
        path = large_knowledge_graph.find_shortest_path(
            source_id="char_main_0",
            target_id="char_main_5",
            max_depth=5,
        )
        duration_ms = (time.time() - start) * 1000
        
        print(f"\n=== Shortest Path Performance ===")
        print(f"Found path of length {len(path) if path else 0} in {duration_ms:.2f}ms")
        
        assert duration_ms < 100, f"find_shortest_path() should be < 100ms, got {duration_ms:.2f}ms"

    def test_query_performance_related_entities(self, large_knowledge_graph: KnowledgeGraph) -> None:
        """Test performance of related entities query (BFS traversal)."""
        start = time.time()
        related = large_knowledge_graph.query_related_entities(
            node_id="char_main_0",
            max_depth=3,
        )
        duration_ms = (time.time() - start) * 1000
        
        print(f"\n=== Related Entities Performance ===")
        print(f"Found {len(related)} related entities in {duration_ms:.2f}ms")
        
        assert duration_ms < 100, f"query_related_entities() should be < 100ms, got {duration_ms:.2f}ms"
        assert len(related) > 0

    def test_query_performance_by_time_range(self, large_knowledge_graph: KnowledgeGraph) -> None:
        """Test performance of chapter range queries."""
        start = time.time()
        entities = large_knowledge_graph.query_by_time_range(
            start_chapter=50,
            end_chapter=100,
            node_type="character",
        )
        duration_ms = (time.time() - start) * 1000
        
        print(f"\n=== Time Range Query Performance ===")
        print(f"Found {len(entities)} entities in chapters 50-100 in {duration_ms:.2f}ms")
        
        assert duration_ms < 100, f"query_by_time_range() should be < 100ms, got {duration_ms:.2f}ms"

    def test_query_performance_entity_timeline(self, large_knowledge_graph: KnowledgeGraph) -> None:
        """Test performance of entity timeline generation."""
        start = time.time()
        timeline = large_knowledge_graph.get_entity_timeline("char_main_0")
        duration_ms = (time.time() - start) * 1000
        
        print(f"\n=== Entity Timeline Performance ===")
        print(f"Generated timeline with {len(timeline)} events in {duration_ms:.2f}ms")
        
        assert duration_ms < 100, f"get_entity_timeline() should be < 100ms, got {duration_ms:.2f}ms"

    def test_query_performance_get_entity_by_name(self, large_knowledge_graph: KnowledgeGraph) -> None:
        """Test performance of name-based entity lookup."""
        start = time.time()
        entity = large_knowledge_graph.get_entity_by_name(
            name="Character Main 5",
            node_type="character",
        )
        duration_ms = (time.time() - start) * 1000
        
        print(f"\n=== Get Entity By Name Performance ===")
        print(f"Found entity in {duration_ms:.2f}ms")
        
        assert duration_ms < 50, f"get_entity_by_name() should be < 50ms, got {duration_ms:.2f}ms"
        assert entity is not None

    def test_query_performance_get_subgraph(self, large_knowledge_graph: KnowledgeGraph) -> None:
        """Test performance of subgraph extraction."""
        # Get 50 related node IDs
        node_ids = [f"char_main_{i}" for i in range(10)]
        node_ids += [f"char_supporting_{i}" for i in range(40)]
        
        start = time.time()
        nodes, edges = large_knowledge_graph.get_subgraph(node_ids)
        duration_ms = (time.time() - start) * 1000
        
        print(f"\n=== Get Subgraph Performance ===")
        print(f"Extracted subgraph with {len(nodes)} nodes, {len(edges)} edges in {duration_ms:.2f}ms")
        
        assert duration_ms < 100, f"get_subgraph() should be < 100ms, got {duration_ms:.2f}ms"

    def test_query_performance_export(self, large_knowledge_graph: KnowledgeGraph) -> None:
        """Test performance of graph export to dict."""
        start = time.time()
        data = large_knowledge_graph.export_to_dict()
        duration_ms = (time.time() - start) * 1000
        
        print(f"\n=== Export To Dict Performance ===")
        print(f"Exported graph in {duration_ms:.2f}ms")
        
        assert duration_ms < 500, f"export_to_dict() should be < 500ms, got {duration_ms:.2f}ms"
        assert "nodes" in data
        assert "edges" in data
        assert "statistics" in data

    def test_comprehensive_query_suite(self, large_knowledge_graph: KnowledgeGraph) -> None:
        """Test comprehensive query suite - all queries must complete < 1s total."""
        start = time.time()
        
        # Execute typical query suite
        all_nodes = large_knowledge_graph.get_all_nodes()
        characters = large_knowledge_graph.find_nodes_by_type("character")
        relations = large_knowledge_graph.get_relationships(source_id="char_main_0")
        neighbors = large_knowledge_graph.get_neighbors("char_main_0")
        related = large_knowledge_graph.query_related_entities("char_main_0", max_depth=2)
        timeline = large_knowledge_graph.get_entity_timeline("char_main_0")
        entities_range = large_knowledge_graph.query_by_time_range(50, 100, "character")
        entity = large_knowledge_graph.get_entity_by_name("Character Main 3", "character")
        
        total_duration_ms = (time.time() - start) * 1000
        
        print(f"\n=== Comprehensive Query Suite ===")
        print(f"Executed 8 queries in {total_duration_ms:.2f}ms total")
        print(f"Average query time: {total_duration_ms / 8:.2f}ms")
        
        # CRITICAL: Total time must be < 1 second
        assert total_duration_ms < 1000, (
            f"Comprehensive query suite should be < 1000ms, got {total_duration_ms:.2f}ms"
        )
        
        # Verify results are non-empty
        assert len(all_nodes) > 0
        assert len(characters) > 0
        assert len(relations) > 0
        assert len(neighbors) > 0
        assert len(related) > 0
        assert len(timeline) > 0
        assert len(entities_range) > 0
        assert entity is not None


class TestKnowledgeGraphScalability:
    """Test KnowledgeGraph scalability as data grows."""

    def test_linear_growth_verification(self, tmp_path: Path) -> None:
        """Verify query performance grows linearly, not exponentially."""
        kg = KnowledgeGraph(graph_id="scalability_test", storage_path=tmp_path / "scale_test")
        
        results = []
        sizes = [50, 100, 200, 400]
        
        for size in sizes:
            # Add nodes
            for i in range(size):
                kg.add_node(
                    node_id=f"node_{size}_{i}",
                    node_type="character",
                    properties={"name": f"Node {i}", "batch": size},
                )
            
            # Add edges (sparse graph, O(n) edges)
            for i in range(min(size, 100)):
                kg.add_edge(
                    edge_id=f"edge_{size}_{i}",
                    source_id=f"node_{size}_{i}",
                    target_id=f"node_{size}_{(i + 1) % size}",
                    relationship_type="connected",
                    weight=0.5,
                )
            
            # Measure query time
            start = time.time()
            nodes = kg.get_all_nodes()
            duration_ms = (time.time() - start) * 1000
            
            results.append({
                "size": size,
                "nodes": len(nodes),
                "time_ms": duration_ms,
            })
        
        print("\n=== Scalability Test Results ===")
        for result in results:
            print(f"Size {result['size']:3d}: {result['nodes']:3d} nodes, {result['time_ms']:6.2f}ms")
        
        # Verify linear growth (roughly)
        # Time should not grow faster than O(n)
        if len(results) >= 2:
            time_ratio = results[-1]["time_ms"] / max(results[0]["time_ms"], 0.001)
            size_ratio = results[-1]["size"] / results[0]["size"]
            
            # Allow some overhead, but should be roughly linear
            assert time_ratio < size_ratio * 2, (
                f"Query time growth ({time_ratio:.2f}x) exceeds linear growth ({size_ratio:.2f}x)"
            )
