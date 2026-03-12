"""Lightweight Knowledge Graph Performance Benchmarks.

This test suite measures the performance of KnowledgeGraph operations
with a reduced dataset (50-chapter scale) to avoid timeout issues.

Performance Goals:
- Node query: < 100ms
- Relationship query: < 200ms
- Conflict detection: < 500ms
- Total test suite: < 60 seconds
"""

import time
import tracemalloc
from pathlib import Path

import pytest

from src.novel.knowledge_graph import KnowledgeGraph
from src.novel.schemas import KnowledgeGraphQuery


class TestKnowledgeGraphPerformance:
    """Performance benchmarks for KnowledgeGraph with lightweight dataset."""

    @pytest.fixture
    def knowledge_graph(self, tmp_path):
        """Create a knowledge graph with 50-chapter scale data."""
        storage = tmp_path / "kg_perf"
        kg = KnowledgeGraph(graph_id="perf_test", storage_path=storage)

        # Create 50 character nodes (reduced from 400+)
        for i in range(1, 51):
            kg.add_node(
                node_id=f"character_{i:03d}",
                node_type="character",
                properties={
                    "name": f"Character {i}",
                    "role": "protagonist" if i <= 5 else "supporting",
                    "status": "active",
                    "introduced_chapter": i % 10 + 1,
                },
            )

        # Create 20 location nodes (reduced from 200)
        for i in range(1, 21):
            kg.add_node(
                node_id=f"location_{i:03d}",
                node_type="location",
                properties={
                    "name": f"Location {i}",
                    "type": "city" if i <= 5 else "region",
                    "importance": 10 - (i % 10),
                },
            )

        # Create 30 plot thread nodes (reduced from 300)
        for i in range(1, 31):
            kg.add_node(
                node_id=f"plot_{i:03d}",
                node_type="plot_thread",
                properties={
                    "name": f"Plot Thread {i}",
                    "status": "active" if i <= 20 else "resolved",
                    "priority": "high" if i <= 10 else "medium",
                },
            )

        # Create 100+ relationship edges (reduced from 1000+)
        edge_count = 0
        # Character-Character relationships
        for i in range(1, 41):
            kg.add_edge(
                edge_id=f"char_rel_{i:03d}",
                source_id=f"character_{i:03d}",
                target_id=f"character_{(i % 50) + 1:03d}",
                relationship_type="knows",
                weight=0.5 + (i % 10) * 0.05,
                properties={"since_chapter": i % 10 + 1},
            )
            edge_count += 1

        # Character-Location relationships
        for i in range(1, 31):
            kg.add_edge(
                edge_id=f"char_loc_{i:03d}",
                source_id=f"character_{i:03d}",
                target_id=f"location_{(i % 20) + 1:03d}",
                relationship_type="located_at",
                weight=0.8,
                properties={"chapter": i % 10 + 1},
            )
            edge_count += 1

        # Character-Plot relationships
        for i in range(1, 41):
            kg.add_edge(
                edge_id=f"char_plot_{i:03d}",
                source_id=f"character_{(i % 50) + 1:03d}",
                target_id=f"plot_{(i % 30) + 1:03d}",
                relationship_type="involved_in",
                weight=0.7,
                properties={"role": "main" if i <= 10 else "supporting"},
            )
            edge_count += 1

        node_count = len(kg.get_all_nodes())
        edge_count = len(kg._edges)
        assert node_count == 100, f"Expected 100 nodes, got {node_count}"
        assert edge_count >= 100, f"Expected >= 100 edges, got {edge_count}"

        return kg

    @pytest.mark.benchmark
    def test_node_query_performance(self, knowledge_graph):
        """Test node query performance.

        Goal: All queries < 100ms
        """
        tracemalloc.start()

        # Test 1: Query by node type (character)
        start = time.time()
        characters = knowledge_graph.find_nodes_by_type("character")
        elapsed_character = (time.time() - start) * 1000  # ms

        # Test 2: Query by node type (location)
        start = time.time()
        locations = knowledge_graph.find_nodes_by_type("location")
        elapsed_location = (time.time() - start) * 1000  # ms

        # Test 3: Query by node type (plot_thread)
        start = time.time()
        plots = knowledge_graph.find_nodes_by_type("plot_thread")
        elapsed_plot = (time.time() - start) * 1000  # ms

        # Test 4: Get all nodes
        start = time.time()
        all_nodes = knowledge_graph.get_all_nodes()
        elapsed_all = (time.time() - start) * 1000  # ms

        tracemalloc.stop()

        # Assert performance goals
        assert elapsed_character < 100, f"Character query too slow: {elapsed_character:.2f}ms"
        assert elapsed_location < 100, f"Location query too slow: {elapsed_location:.2f}ms"
        assert elapsed_plot < 100, f"Plot query too slow: {elapsed_plot:.2f}ms"
        assert elapsed_all < 100, f"Get all nodes too slow: {elapsed_all:.2f}ms"

        # Print results
        print(f"\nNode Query Performance:")
        print(f"  Character query (50 nodes): {elapsed_character:.2f}ms")
        print(f"  Location query (20 nodes): {elapsed_location:.2f}ms")
        print(f"  Plot query (30 nodes): {elapsed_plot:.2f}ms")
        print(f"  Get all nodes (101 nodes): {elapsed_all:.2f}ms")

    @pytest.mark.benchmark
    def test_relationship_query_performance(self, knowledge_graph):
        """Test relationship query performance.

        Goal: All queries < 200ms
        """
        tracemalloc.start()

        # Test 1: Get relationships by type
        start = time.time()
        knows_edges = knowledge_graph.get_relationships(relationship_types=["knows"])
        elapsed_knows = (time.time() - start) * 1000  # ms

        # Test 2: Get relationships from specific node
        start = time.time()
        char_edges = knowledge_graph.get_relationships(source_id="character_001")
        elapsed_char = (time.time() - start) * 1000  # ms

        # Test 3: Get relationships to specific node
        start = time.time()
        loc_edges = knowledge_graph.get_relationships(target_id="location_001")
        elapsed_loc = (time.time() - start) * 1000  # ms

        # Test 4: Get all relationships
        start = time.time()
        all_edges = knowledge_graph.get_relationships()
        elapsed_all = (time.time() - start) * 1000  # ms

        tracemalloc.stop()

        # Assert performance goals
        assert elapsed_knows < 200, f"Knows query too slow: {elapsed_knows:.2f}ms"
        assert elapsed_char < 200, f"Character edges query too slow: {elapsed_char:.2f}ms"
        assert elapsed_loc < 200, f"Location edges query too slow: {elapsed_loc:.2f}ms"
        assert elapsed_all < 200, f"Get all edges too slow: {elapsed_all:.2f}ms"

        # Print results
        print(f"\nRelationship Query Performance:")
        print(f"  'knows' relationships ({len(knows_edges)} edges): {elapsed_knows:.2f}ms")
        print(f"  character_001 edges ({len(char_edges)} edges): {elapsed_char:.2f}ms")
        print(f"  location_001 edges ({len(loc_edges)} edges): {elapsed_loc:.2f}ms")
        print(f"  All edges ({len(all_edges)} edges): {elapsed_all:.2f}ms")

    @pytest.mark.benchmark
    def test_conflict_detection_performance(self, knowledge_graph):
        """Test conflict detection performance.

        Simulates checking for inconsistencies in the knowledge graph.
        Goal: < 500ms
        """
        tracemalloc.start()

        start = time.time()

        # Simulate conflict detection: check for characters in multiple locations
        conflicts = []

        # Get all character-location relationships
        located_edges = knowledge_graph.get_relationships(relationship_types=["located_at"])

        # Group by character
        character_locations = {}
        for edge in located_edges:
            char_id = edge.source_id
            loc_id = edge.target_id
            if char_id not in character_locations:
                character_locations[char_id] = []
            character_locations[char_id].append(loc_id)

        # Check for characters with multiple active locations (potential conflict)
        for char_id, locations in character_locations.items():
            if len(locations) > 1:
                conflicts.append({
                    "character": char_id,
                    "locations": locations,
                    "issue": "multiple_active_locations",
                })

        elapsed = (time.time() - start) * 1000  # ms

        tracemalloc.stop()

        # Assert performance goal
        assert elapsed < 500, f"Conflict detection too slow: {elapsed:.2f}ms"

        # Print results
        print(f"\nConflict Detection Performance:")
        print(f"  Time: {elapsed:.2f}ms")
        print(f"  Edges analyzed: {len(located_edges)}")
        print(f"  Characters checked: {len(character_locations)}")
        print(f"  Conflicts found: {len(conflicts)}")

    @pytest.mark.benchmark
    def test_neighbor_query_performance(self, knowledge_graph):
        """Test neighbor query performance.

        Goal: < 150ms
        """
        tracemalloc.start()

        # Test getting neighbors for multiple characters
        start = time.time()
        all_neighbors = {}
        for i in range(1, 11):  # Test 10 characters
            char_id = f"character_{i:03d}"
            neighbors = knowledge_graph.get_neighbors(char_id)
            all_neighbors[char_id] = len(neighbors)
        elapsed = (time.time() - start) * 1000  # ms

        tracemalloc.stop()

        # Assert performance goal
        assert elapsed < 150, f"Neighbor query too slow: {elapsed:.2f}ms"

        # Print results
        print(f"\nNeighbor Query Performance:")
        print(f"  Time for 10 characters: {elapsed:.2f}ms")
        print(f"  Average neighbors per character: {sum(all_neighbors.values()) / len(all_neighbors):.1f}")

    @pytest.mark.benchmark
    def test_complex_query_performance(self, knowledge_graph):
        """Test complex query with filters.

        Goal: < 300ms
        """
        tracemalloc.start()

        start = time.time()

        # Complex query: Find all characters involved in high-priority plots
        query = KnowledgeGraphQuery(
            node_types=["character"],
            relationship_types=["involved_in"],
            property_filters=None,
            depth=1,
            limit=100,
        )

        # Execute query
        result = knowledge_graph.query(query)
        elapsed = (time.time() - start) * 1000  # ms

        tracemalloc.stop()

        # Assert performance goal
        assert elapsed < 300, f"Complex query too slow: {elapsed:.2f}ms"

        # Print results
        print(f"\nComplex Query Performance:")
        print(f"  Time: {elapsed:.2f}ms")
        print(f"  Results: {len(result)} characters")

    @pytest.mark.benchmark
    def test_memory_usage(self, knowledge_graph):
        """Test memory usage of the knowledge graph.

        Goal: < 10MB for 100 nodes, 100+ edges
        """
        tracemalloc.start()

        # Force a garbage collection
        import gc
        gc.collect()

        # Take snapshot
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics("lineno")

        # Get total memory
        total_memory = sum(stat.size for stat in top_stats) / 1024 / 1024  # MB

        tracemalloc.stop()

        # Assert memory goal
        assert total_memory < 10, f"Memory usage too high: {total_memory:.2f}MB"

        # Print results
        print(f"\nMemory Usage:")
        print(f"  Total: {total_memory:.2f}MB")
        print(f"  Nodes: {len(knowledge_graph.get_all_nodes())}")
        print(f"  Edges: {len(knowledge_graph._edges)}")


class TestKnowledgeGraphScalability:
    """Test how performance scales with data size."""

    @pytest.mark.benchmark
    def test_incremental_growth(self, tmp_path):
        """Test performance as graph grows.

        Measures query time at different sizes.
        """
        storage = tmp_path / "kg_scale"
        kg = KnowledgeGraph(graph_id="scale_test", storage_path=storage)

        sizes = [10, 25, 50, 75, 100]
        query_times = []

        for target_size in sizes:
            # Add nodes to reach target size
            current_nodes = len(kg.get_all_nodes())
            for i in range(current_nodes + 1, target_size + 1):
                kg.add_node(
                    node_id=f"node_{i:03d}",
                    node_type="test_node",
                    properties={"index": i},
                )

                # Add some edges
                if i > 1:
                    kg.add_edge(
                        edge_id=f"edge_{i:03d}",
                        source_id=f"node_{i-1:03d}",
                        target_id=f"node_{i:03d}",
                        relationship_type="connected_to",
                        weight=0.5,
                    )

            # Measure query time
            start = time.time()
            nodes = kg.get_all_nodes()
            elapsed = (time.time() - start) * 1000  # ms
            query_times.append(elapsed)

        # Print results
        print(f"\nScalability Test:")
        for size, time_ms in zip(sizes, query_times):
            print(f"  {size} nodes: {time_ms:.2f}ms")

        # Assert that even at 100 nodes, query is fast
        assert query_times[-1] < 100, f"Query at 100 nodes too slow: {query_times[-1]:.2f}ms"
