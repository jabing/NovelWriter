"""Knowledge graph for tracking story entities and relationships.

Provides a graph-based representation of characters, locations, plot points,
and concepts with their relationships, enabling semantic queries and
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from src.novel.schemas import KnowledgeGraphEdge, KnowledgeGraphNode, KnowledgeGraphQuery

logger = logging.getLogger(__name__)

# Configuration constants for cleanup (optimized for 50-chapter generation)
CLEANUP_FREQUENCY = 5  # Run cleanup every N chapters (was 10)
LOOKBACK_CHAPTERS = 10  # How many chapters to check for references (was 5)



class KnowledgeGraph:
    """Knowledge graph for story entities and relationships.

    Maintains nodes (entities) and edges (relationships) with properties,
    supporting semantic queries and graph algorithms.
    """

    graph_id: str
    storage_path: Path | None


    def __init__(self, graph_id: str = "default", storage_path: Path | None = None) -> None:
        """Initialize the knowledge graph.

        Args:
            graph_id: Unique identifier for this graph
            storage_path: Optional path for persistent storage
        """
        self.graph_id = graph_id
        self.storage_path = storage_path

        # In-memory storage
        self._nodes: dict[str, KnowledgeGraphNode] = {}
        self._edges: dict[str, KnowledgeGraphEdge] = {}

        # Indexes for fast lookups
        self._node_type_index: dict[str, set[str]] = {}  # node_type -> set of node_ids
        self._edge_type_index: dict[str, set[str]] = {}  # relationship_type -> set of edge_ids
        self._source_index: dict[str, set[str]] = {}  # source_id -> set of edge_ids
        self._target_index: dict[str, set[str]] = {}  # target_id -> set of edge_ids

        # Load from storage if path exists
        if storage_path and storage_path.exists():
            self._load_from_storage()

        logger.info(
            f"KnowledgeGraph '{graph_id}' initialized with {len(self._nodes)} nodes, {len(self._edges)} edges"
        )

    def _load_from_storage(self) -> None:
        """Load graph from storage path."""
        try:
            assert self.storage_path is not None
            nodes_file = self.storage_path / "nodes.json"
            edges_file = self.storage_path / "edges.json"

            if nodes_file.exists():
                with open(nodes_file, encoding="utf-8") as f:
                    nodes_data = json.load(f)

                for node_data in nodes_data:
                    # Handle datetime fields
                    for time_field in ["created_at", "updated_at"]:
                        if time_field in node_data and isinstance(node_data[time_field], str):
                            node_data[time_field] = datetime.fromisoformat(node_data[time_field])

                    node = KnowledgeGraphNode(**node_data)
                    self._add_node_to_indexes(node)

            if edges_file.exists():
                with open(edges_file, encoding="utf-8") as f:
                    edges_data = json.load(f)

                for edge_data in edges_data:
                    # Handle datetime field
                    if "created_at" in edge_data and isinstance(edge_data["created_at"], str):
                        edge_data["created_at"] = datetime.fromisoformat(edge_data["created_at"])

                    edge = KnowledgeGraphEdge(**edge_data)
                    self._add_edge_to_indexes(edge)

            logger.info(f"Loaded knowledge graph from {self.storage_path}")

        except Exception as e:
            logger.error(f"Failed to load knowledge graph from {self.storage_path}: {e}")

    def _save_to_storage(self) -> None:
        """Save graph to storage path."""
        if not self.storage_path:
            return
            assert self.storage_path is not None

        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)

            # Convert nodes to JSON-serializable format
            nodes_data = []
            for node in self._nodes.values():
                node_dict = node.model_dump()
                # Convert datetime to ISO string
                for time_field in ["created_at", "updated_at"]:
                    if time_field in node_dict and isinstance(node_dict[time_field], datetime):
                        node_dict[time_field] = node_dict[time_field].isoformat()
                nodes_data.append(node_dict)

            # Convert edges to JSON-serializable format
            edges_data = []
            for edge in self._edges.values():
                edge_dict = edge.model_dump()
                # Convert datetime to ISO string
                if "created_at" in edge_dict and isinstance(edge_dict["created_at"], datetime):
                    edge_dict["created_at"] = edge_dict["created_at"].isoformat()
                edges_data.append(edge_dict)

            # Save to files
            nodes_file = self.storage_path / "nodes.json"
            edges_file = self.storage_path / "edges.json"

            with open(nodes_file, "w", encoding="utf-8") as f:
                json.dump(nodes_data, f, indent=2, ensure_ascii=False)

            with open(edges_file, "w", encoding="utf-8") as f:
                json.dump(edges_data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved knowledge graph to {self.storage_path}")

        except Exception as e:
            logger.error(f"Failed to save knowledge graph to {self.storage_path}: {e}")

    def _add_node_to_indexes(self, node: KnowledgeGraphNode) -> None:
        """Add a node to all indexes."""
        self._nodes[node.node_id] = node

        # Update type index
        if node.node_type not in self._node_type_index:
            self._node_type_index[node.node_type] = set()
        self._node_type_index[node.node_type].add(node.node_id)

    def _add_edge_to_indexes(self, edge: KnowledgeGraphEdge) -> None:
        """Add an edge to all indexes."""
        self._edges[edge.edge_id] = edge

        # Update relationship type index
        if edge.relationship_type not in self._edge_type_index:
            self._edge_type_index[edge.relationship_type] = set()
        self._edge_type_index[edge.relationship_type].add(edge.edge_id)

        # Update source/target indexes
        if edge.source_id not in self._source_index:
            self._source_index[edge.source_id] = set()
        self._source_index[edge.source_id].add(edge.edge_id)

        if edge.target_id not in self._target_index:
            self._target_index[edge.target_id] = set()
        self._target_index[edge.target_id].add(edge.edge_id)

    def _remove_node_from_indexes(self, node_id: str) -> None:
        """Remove a node from all indexes."""
        if node_id not in self._nodes:
            return

        node = self._nodes[node_id]

        # Remove from type index
        if node.node_type in self._node_type_index:
            self._node_type_index[node.node_type].discard(node_id)
            if not self._node_type_index[node.node_type]:
                del self._node_type_index[node.node_type]

        # Remove the node
        del self._nodes[node_id]

    def _remove_edge_from_indexes(self, edge_id: str) -> None:
        """Remove an edge from all indexes."""
        if edge_id not in self._edges:
            return

        edge = self._edges[edge_id]

        # Remove from relationship type index
        if edge.relationship_type in self._edge_type_index:
            self._edge_type_index[edge.relationship_type].discard(edge_id)
            if not self._edge_type_index[edge.relationship_type]:
                del self._edge_type_index[edge.relationship_type]

        # Remove from source/target indexes
        if edge.source_id in self._source_index:
            self._source_index[edge.source_id].discard(edge_id)
            if not self._source_index[edge.source_id]:
                del self._source_index[edge.source_id]

        if edge.target_id in self._target_index:
            self._target_index[edge.target_id].discard(edge_id)
            if not self._target_index[edge.target_id]:
                del self._target_index[edge.target_id]

        # Remove the edge
        del self._edges[edge_id]

    def add_node(
        self,
        node_id: str,
        node_type: str,
        properties: dict[str, Any],
        embeddings: list[float] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> KnowledgeGraphNode:
        """Add a node to the graph.

        Args:
            node_id: Unique node identifier
            node_type: Type of node (character, plot, location, concept, etc.)
            properties: Node properties
            embeddings: Optional vector embeddings for semantic search
            created_at: Optional creation time (default: now)
            updated_at: Optional update time (default: now)

        Returns:
            The created node

        Raises:
            ValueError: If node with same ID already exists
        """
        if node_id in self._nodes:
            raise ValueError(f"Node with ID '{node_id}' already exists")

        now = datetime.now()
        created_at = created_at or now
        updated_at = updated_at or now

        node = KnowledgeGraphNode(
            node_id=node_id,
            node_type=node_type,
            properties=properties,
            embeddings=embeddings,
            created_at=created_at,
            updated_at=updated_at,
        )

        self._add_node_to_indexes(node)

        # Auto-save if storage path is configured
        if self.storage_path:
            self._save_to_storage()

        logger.debug(f"Added node: {node_id} ({node_type})")
        return node

    def update_node(
        self,
        node_id: str,
        properties: dict[str, Any] | None = None,
        embeddings: list[float] | None = None,
        merge_properties: bool = True,
    ) -> KnowledgeGraphNode | None:
        """Update an existing node.

        Args:
            node_id: Node identifier
            properties: New properties (None to keep existing)
            embeddings: New embeddings (None to keep existing)
            merge_properties: If True, merge with existing properties; if False, replace

        Returns:
            Updated node or None if node not found
        """
        if node_id not in self._nodes:
            logger.warning(f"Cannot update non-existent node: {node_id}")
            return None

        node = self._nodes[node_id]

        # Update properties
        if properties is not None:
            if merge_properties:
                node.properties.update(properties)
            else:
                node.properties = properties

        # Update embeddings
        if embeddings is not None:
            node.embeddings = embeddings

        # Update timestamp
        node.updated_at = datetime.now()

        # Auto-save if storage path is configured
        if self.storage_path:
            self._save_to_storage()

        logger.debug(f"Updated node: {node_id}")
        return node

    def get_node(self, node_id: str) -> KnowledgeGraphNode | None:
        """Get a node by ID."""
        return self._nodes.get(node_id)
    def get_all_nodes(self) -> list[KnowledgeGraphNode]:
        """Get all nodes in the knowledge graph."""
        return list(self._nodes.values())

    def get_all_entities(self) -> list[KnowledgeGraphNode]:
        """Get all entities (nodes) in the knowledge graph.

        Alias for get_all_nodes() for backward compatibility.
        """
        return self.get_all_nodes()


    def delete_node(self, node_id: str, cascade: bool = True) -> bool:
        """Delete a node from the graph.

        Args:
            node_id: Node identifier
            cascade: If True, also delete all connected edges

        Returns:
            True if node was deleted
        """
        if node_id not in self._nodes:
            return False

        # Delete connected edges if cascading
        if cascade:
            # Find all edges connected to this node
            edges_to_delete = []
            for edge_id, edge in self._edges.items():
                if edge.source_id == node_id or edge.target_id == node_id:
                    edges_to_delete.append(edge_id)

            # Delete edges
            for edge_id in edges_to_delete:
                self._remove_edge_from_indexes(edge_id)

        # Delete the node
        self._remove_node_from_indexes(node_id)

        # Auto-save if storage path is configured
        if self.storage_path:
            self._save_to_storage()

        logger.debug(f"Deleted node: {node_id} (cascade={cascade})")
        return True

    def add_edge(
        self,
        edge_id: str,
        source_id: str,
        target_id: str,
        relationship_type: str,
        weight: float = 1.0,
        properties: dict[str, Any] | None = None,
        created_at: datetime | None = None,
    ) -> KnowledgeGraphEdge:
        """Add an edge (relationship) to the graph.

        Args:
            edge_id: Unique edge identifier
            source_id: Source node ID
            target_id: Target node ID
            relationship_type: Type of relationship
            weight: Relationship strength (0.0 to 1.0)
            properties: Edge properties
            created_at: Optional creation time (default: now)

        Returns:
            The created edge

        Raises:
            ValueError: If edge with same ID already exists or nodes don't exist
        """
        if edge_id in self._edges:
            raise ValueError(f"Edge with ID '{edge_id}' already exists")

        if source_id not in self._nodes:
            raise ValueError(f"Source node '{source_id}' not found")

        if target_id not in self._nodes:
            raise ValueError(f"Target node '{target_id}' not found")

        if not 0.0 <= weight <= 1.0:
            raise ValueError(f"Weight must be between 0.0 and 1.0, got {weight}")

        created_at = created_at or datetime.now()

        edge = KnowledgeGraphEdge(
            edge_id=edge_id,
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            weight=weight,
            properties=properties or {},
            created_at=created_at,
        )

        self._add_edge_to_indexes(edge)

        # Auto-save if storage path is configured
        if self.storage_path:
            self._save_to_storage()

        logger.debug(f"Added edge: {edge_id} ({source_id} -> {target_id}, {relationship_type})")
        return edge

    def update_edge(
        self,
        edge_id: str,
        weight: float | None = None,
        properties: dict[str, Any] | None = None,
        merge_properties: bool = True,
    ) -> KnowledgeGraphEdge | None:
        """Update an existing edge.

        Args:
            edge_id: Edge identifier
            weight: New weight (None to keep existing)
            properties: New properties (None to keep existing)
            merge_properties: If True, merge with existing properties; if False, replace

        Returns:
            Updated edge or None if edge not found
        """
        if edge_id not in self._edges:
            logger.warning(f"Cannot update non-existent edge: {edge_id}")
            return None

        edge = self._edges[edge_id]

        # Update weight
        if weight is not None:
            if not 0.0 <= weight <= 1.0:
                raise ValueError(f"Weight must be between 0.0 and 1.0, got {weight}")
            edge.weight = weight

        # Update properties
        if properties is not None:
            if merge_properties:
                edge.properties.update(properties)
            else:
                edge.properties = properties

        # Auto-save if storage path is configured
        if self.storage_path:
            self._save_to_storage()

        logger.debug(f"Updated edge: {edge_id}")
        return edge

    def get_edge(self, edge_id: str) -> KnowledgeGraphEdge | None:
        """Get an edge by ID."""
        return self._edges.get(edge_id)

    def delete_edge(self, edge_id: str) -> bool:
        """Delete an edge from the graph.

        Returns:
            True if edge was deleted
        """
        if edge_id not in self._edges:
            return False

        self._remove_edge_from_indexes(edge_id)

        # Auto-save if storage path is configured
        if self.storage_path:
            self._save_to_storage()

        logger.debug(f"Deleted edge: {edge_id}")
        return True

    def query(self, query: KnowledgeGraphQuery) -> list[KnowledgeGraphNode]:
        """Execute a graph query.

        Args:
            query: Query specification

        Returns:
            List of matching nodes
        """
        # Start with all nodes or filtered by type
        if query.node_types:
            candidate_ids = set()
            for node_type in query.node_types:
                if node_type in self._node_type_index:
                    candidate_ids.update(self._node_type_index[node_type])
        else:
            candidate_ids = set(self._nodes.keys())

        # Filter by properties
        if query.property_filters:
            filtered_ids = set()
            for node_id in candidate_ids:
                node = self._nodes[node_id]
                matches = True

                for key, value in query.property_filters.items():
                    if key not in node.properties or node.properties[key] != value:
                        matches = False
                        break

                if matches:
                    filtered_ids.add(node_id)

            candidate_ids = filtered_ids

        # If no relationship filtering, return the nodes
        if not query.relationship_types or query.depth == 0:
            nodes = [self._nodes[node_id] for node_id in list(candidate_ids)[: query.limit]]
            return nodes

        # Perform graph traversal for relationship filtering
        result_ids = set()

        for start_id in candidate_ids:
            # Perform BFS up to specified depth
            visited = {start_id}
            queue = [(start_id, 0)]  # (node_id, current_depth)
            found_nodes = set()

            while queue:
                current_id, depth = queue.pop(0)

                # Stop if we've reached max depth
                if depth >= query.depth:
                    continue

                # Get outgoing edges
                edge_ids = self._source_index.get(current_id, set())
                for edge_id in edge_ids:
                    edge = self._edges[edge_id]

                    # Check relationship type filter
                    if edge.relationship_type in query.relationship_types:
                        neighbor_id = edge.target_id
                        if neighbor_id == current_id:
                            # Self-loop edge
                            found_nodes.add(neighbor_id)
                        elif neighbor_id not in visited:
                            visited.add(neighbor_id)
                            found_nodes.add(neighbor_id)
                            queue.append((neighbor_id, depth + 1))

                # Get incoming edges (for undirected traversal)
                edge_ids = self._target_index.get(current_id, set())
                for edge_id in edge_ids:
                    edge = self._edges[edge_id]

                    # Check relationship type filter
                    if edge.relationship_type in query.relationship_types:
                        neighbor_id = edge.source_id
                        if neighbor_id == current_id:
                            # Self-loop edge
                            found_nodes.add(neighbor_id)
                        elif neighbor_id not in visited:
                            visited.add(neighbor_id)
                            found_nodes.add(neighbor_id)
                            queue.append((neighbor_id, depth + 1))

            result_ids.update(found_nodes)

        # Limit results
        limited_ids = list(result_ids)[: query.limit]
        nodes = [self._nodes[node_id] for node_id in limited_ids]
        return nodes

    def find_nodes_by_type(self, node_type: str) -> list[KnowledgeGraphNode]:
        """Find all nodes of a specific type."""
        if node_type not in self._node_type_index:
            return []

        node_ids = self._node_type_index[node_type]
        return [self._nodes[node_id] for node_id in node_ids]

    def find_edges_by_relationship(self, relationship_type: str) -> list[KnowledgeGraphEdge]:
        """Find all edges of a specific relationship type."""
        if relationship_type not in self._edge_type_index:
            return []

        edge_ids = self._edge_type_index[relationship_type]
        return [self._edges[edge_id] for edge_id in edge_ids]

    def get_neighbors(
        self,
        node_id: str,
        relationship_types: list[str] | None = None,
        direction: str = "both",
    ) -> list[KnowledgeGraphNode]:
        """Get neighboring nodes of a given node.

        Args:
            node_id: Node identifier
            relationship_types: Optional filter for relationship types
            direction: "outgoing", "incoming", or "both"

        Returns:
            List of neighboring nodes
        """
        if node_id not in self._nodes:
            return []

        neighbor_ids = set()

        # Outgoing edges
        if direction in ["outgoing", "both"]:
            edge_ids = self._source_index.get(node_id, set())
            for edge_id in edge_ids:
                edge = self._edges[edge_id]
                if not relationship_types or edge.relationship_type in relationship_types:
                    neighbor_ids.add(edge.target_id)

        # Incoming edges
        if direction in ["incoming", "both"]:
            edge_ids = self._target_index.get(node_id, set())
            for edge_id in edge_ids:
                edge = self._edges[edge_id]
                if not relationship_types or edge.relationship_type in relationship_types:
                    neighbor_ids.add(edge.source_id)

        neighbors = [self._nodes[nid] for nid in neighbor_ids]
        return neighbors

    def get_relationships(
        self,
        source_id: str | None = None,
        target_id: str | None = None,
        relationship_types: list[str] | None = None,
    ) -> list[KnowledgeGraphEdge]:
        """Get edges matching criteria.

        Args:
            source_id: Optional source node filter
            target_id: Optional target node filter
            relationship_types: Optional relationship type filter

        Returns:
            List of matching edges
        """
        edges = []

        if source_id and target_id:
            # Find edges between specific nodes
            source_edges = self._source_index.get(source_id, set())
            for edge_id in source_edges:
                edge = self._edges[edge_id]
                if edge.target_id == target_id:
                    if not relationship_types or edge.relationship_type in relationship_types:
                        edges.append(edge)

        elif source_id:
            # Find edges from source node
            edge_ids = self._source_index.get(source_id, set())
            for edge_id in edge_ids:
                edge = self._edges[edge_id]
                if not relationship_types or edge.relationship_type in relationship_types:
                    edges.append(edge)

        elif target_id:
            # Find edges to target node
            edge_ids = self._target_index.get(target_id, set())
            for edge_id in edge_ids:
                edge = self._edges[edge_id]
                if not relationship_types or edge.relationship_type in relationship_types:
                    edges.append(edge)

        else:
            # Find all edges matching relationship types
            if relationship_types:
                for rel_type in relationship_types:
                    if rel_type in self._edge_type_index:
                        edge_ids = self._edge_type_index[rel_type]
                        for edge_id in edge_ids:
                            edges.append(self._edges[edge_id])
            else:
                edges = list(self._edges.values())

        return edges

    def find_shortest_path(
        self,
        source_id: str,
        target_id: str,
        relationship_types: list[str] | None = None,
        max_depth: int = 10,
    ) -> list[str] | None:
        """Find shortest path between two nodes.

        Args:
            source_id: Starting node ID
            target_id: Target node ID
            relationship_types: Optional filter for relationship types
            max_depth: Maximum search depth

        Returns:
            List of node IDs in the path, or None if no path found
        """
        if source_id not in self._nodes or target_id not in self._nodes:
            return None

        if source_id == target_id:
            return [source_id]

        # BFS for shortest path
        visited = {source_id}
        queue = [(source_id, [source_id])]  # (current_node, path)

        while queue:
            current_id, path = queue.pop(0)

            # Stop if we've reached max depth
            if len(path) > max_depth:
                continue

            # Get outgoing edges
            edge_ids = self._source_index.get(current_id, set())
            for edge_id in edge_ids:
                edge = self._edges[edge_id]

                # Check relationship filter
                if relationship_types and edge.relationship_type not in relationship_types:
                    continue

                neighbor_id = edge.target_id

                if neighbor_id == target_id:
                    return path + [neighbor_id]

                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))

            # Get incoming edges (for undirected search)
            edge_ids = self._target_index.get(current_id, set())
            for edge_id in edge_ids:
                edge = self._edges[edge_id]

                # Check relationship filter
                if relationship_types and edge.relationship_type not in relationship_types:
                    continue

                neighbor_id = edge.source_id

                if neighbor_id == target_id:
                    return path + [neighbor_id]

                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))

        return None  # No path found

    def get_subgraph(
        self, node_ids: list[str]
    ) -> tuple[list[KnowledgeGraphNode], list[KnowledgeGraphEdge]]:
        """Get subgraph containing specified nodes and edges between them.

        Args:
            node_ids: List of node IDs to include

        Returns:
            Tuple of (nodes, edges) in the subgraph
        """
        node_set = set(node_ids)

        # Get nodes
        nodes = [self._nodes[nid] for nid in node_ids if nid in self._nodes]

        # Get edges where both source and target are in the node_set
        edges = []
        for edge in self._edges.values():
            if edge.source_id in node_set and edge.target_id in node_set:
                edges.append(edge)

        return nodes, edges

    def export_to_dict(self) -> dict[str, Any]:
        """Export graph to dictionary representation."""
        return {
            "graph_id": self.graph_id,
            "nodes": [node.model_dump() for node in self._nodes.values()],
            "edges": [edge.model_dump() for edge in self._edges.values()],
            "statistics": {
                "total_nodes": len(self._nodes),
                "total_edges": len(self._edges),
                "node_types": {nt: len(ids) for nt, ids in self._node_type_index.items()},
                "relationship_types": {rt: len(ids) for rt, ids in self._edge_type_index.items()},
            },
        }

    def clear(self) -> None:
        """Clear all nodes and edges from the graph."""
        self._nodes.clear()
        self._edges.clear()
        self._node_type_index.clear()
        self._edge_type_index.clear()
        self._source_index.clear()
        self._target_index.clear()

        logger.info(f"Cleared knowledge graph '{self.graph_id}'")

    def stats(self) -> dict[str, Any]:
        """Get graph statistics."""
        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "node_types": {nt: len(ids) for nt, ids in self._node_type_index.items()},
            "relationship_types": {rt: len(ids) for rt, ids in self._edge_type_index.items()},
            "avg_degree": len(self._edges) / max(len(self._nodes), 1),
        }
    # ==========================================================================
    # T2-4: Advanced Query Methods
    # ==========================================================================

    def query_related_entities(
        self,
        node_id: str,
        relation_types: list[str] | None = None,
        max_depth: int = 2,
    ) -> list[KnowledgeGraphNode]:
        """Query all entities related to the given entity (BFS traversal).

        Args:
            node_id: Starting entity ID
            relation_types: Limit relationship types, None means all types
            max_depth: Maximum traversal depth

        Returns:
            List of related entities (deduplicated, excluding start node)
        """
        if node_id not in self._nodes:
            return []

        visited = {node_id}
        queue = [(node_id, 0)]  # (current_node_id, current_depth)
        related_ids = set()

        while queue:
            current_id, depth = queue.pop(0)

            if depth >= max_depth:
                continue

            # Get all connected edges
            connected_edges = set()

            # Outgoing edges
            connected_edges.update(self._source_index.get(current_id, set()))
            # Incoming edges
            connected_edges.update(self._target_index.get(current_id, set()))

            for edge_id in connected_edges:
                edge = self._edges.get(edge_id)
                if not edge:
                    continue

                # Filter by relation type if specified
                if relation_types and edge.relationship_type not in relation_types:
                    continue

                # Get the neighbor (other end of the edge)
                if edge.source_id == current_id:
                    neighbor_id = edge.target_id
                elif edge.target_id == current_id:
                    neighbor_id = edge.source_id
                else:
                    continue

                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    related_ids.add(neighbor_id)
                    queue.append((neighbor_id, depth + 1))

        return [self._nodes[nid] for nid in related_ids if nid in self._nodes]

    def query_by_time_range(
        self,
        start_chapter: int,
        end_chapter: int,
        node_type: str | None = None,
    ) -> list[KnowledgeGraphNode]:
        """Query entities active in a specific chapter range.

        Useful for: "Get all characters that appeared in chapters 50-60"

        Args:
            start_chapter: Start chapter number (inclusive)
            end_chapter: End chapter number (inclusive)
            node_type: Limit to specific entity type, None means all types

        Returns:
            List of entities that appeared in the chapter range
        """
        result = []

        # Get candidate nodes (filter by type if specified)
        if node_type:
            candidate_ids = self._node_type_index.get(node_type, set())
        else:
            candidate_ids = set(self._nodes.keys())

        for node_id in candidate_ids:
            node = self._nodes.get(node_id)
            if not node:
                continue

            # Get appearances from properties
            appearances = node.properties.get("appearances", [])
            if not appearances:
                # Fallback to first_appearance
                first_appearance = node.properties.get("first_appearance", 0)
                if first_appearance > 0:
                    appearances = [first_appearance]

            # Check if entity appeared in the range
            for chapter in appearances:
                if start_chapter <= chapter <= end_chapter:
                    result.append(node)
                    break

        return result

    def get_entity_timeline(self, node_id: str) -> list[dict[str, Any]]:
        """Get entity's timeline (chapters appeared, status changes, events participated).

        Args:
            node_id: Entity ID

        Returns:
            List of timeline events sorted by chapter
        """
        if node_id not in self._nodes:
            return []

        node = self._nodes[node_id]
        timeline = []

        # Add appearance events
        appearances = node.properties.get("appearances", [])
        if not appearances:
            first_appearance = node.properties.get("first_appearance", 0)
            if first_appearance > 0:
                appearances = [first_appearance]

        for chapter in sorted(appearances):
            timeline.append({
                "chapter": chapter,
                "event_type": "appearance",
                "description": f"{node.properties.get('name', node_id)} appeared in chapter {chapter}",
                "details": {},
            })

        # Add status change events if tracked
        status_history = node.properties.get("status_history", [])
        for status_event in status_history:
            timeline.append({
                "chapter": status_event.get("chapter", 0),
                "event_type": "status_change",
                "description": status_event.get("description", "Status changed"),
                "details": status_event,
            })

        # Find events where this entity participated
        # Look for edges that indicate participation
        connected_edges = set()
        connected_edges.update(self._source_index.get(node_id, set()))
        connected_edges.update(self._target_index.get(node_id, set()))

        for edge_id in connected_edges:
            edge = self._edges.get(edge_id)
            if not edge:
                continue

            chapter = edge.properties.get("chapter", 0)
            if chapter > 0:
                timeline.append({
                    "chapter": chapter,
                    "event_type": "relation",
                    "description": edge.properties.get("description", f"{edge.relationship_type} relationship"),
                    "details": {
                        "relation_type": edge.relationship_type,
                        "source": edge.source_id,
                        "target": edge.target_id,
                        "evidence": edge.properties.get("evidence", ""),
                    },
                })

        # Sort by chapter
        timeline.sort(key=lambda x: x["chapter"])
        return timeline

    def get_entity_by_name(self, name: str, node_type: str | None = None) -> KnowledgeGraphNode | None:
        """Find entity by name (case-insensitive).

        Args:
            name: Entity name to search for
            node_type: Optional type filter

        Returns:
            Matching entity or None
        """
        name_lower = name.lower()

        # Get candidate nodes
        if node_type:
            candidate_ids = self._node_type_index.get(node_type, set())
        else:
            candidate_ids = set(self._nodes.keys())

        for node_id in candidate_ids:
            node = self._nodes.get(node_id)
            if not node:
                continue

            # Check name
            node_name = node.properties.get("name", "")
            if node_name.lower() == name_lower:
                return node

            # Check aliases
            aliases = node.properties.get("aliases", [])
            for alias in aliases:
                if alias.lower() == name_lower:
                    return node

        return None
    def cleanup_unreferenced(
        self,
        recent_chapters: list[str],
        primary_characters: set[str],
        active_plot_threads: list[str],
        chapter_num: int | None = None,
    ) -> list[str]:
        """Remove unreferenced entities from the knowledge graph.

        Implements entity protection rules to avoid removing plot-relevant entities.
        Protection rules (in order):
        1. Primary characters are NEVER removed
        2. Entities mentioned in last LOOKBACK_CHAPTERS are kept
        3. Entities referenced in active plot threads are kept
        4. Main locations (is_main=True) are kept
        5. Entities with status='active' are kept

        Args:
            recent_chapters: Content of recent chapters (last LOOKBACK_CHAPTERS)
            primary_characters: Set of primary character IDs that should never be removed
            active_plot_threads: List of active plot thread descriptions
            chapter_num: Optional chapter number for logging

        Returns:
            List of removed entity IDs for audit logging
        """
        removed: list[str] = []

        # Log cleanup start
        if chapter_num:
            logger.info(f"Knowledge graph cleanup starting at chapter {chapter_num}")
        logger.info(f"Total entities before cleanup: {len(self._nodes)}")
        logger.debug(f"Primary characters: {primary_characters}")

        # Get snapshot of current nodes to avoid modifying during iteration
        nodes_snapshot = list(self._nodes.items())

        for node_id, node in nodes_snapshot:
            if self._is_unreferenced(
                node, recent_chapters, primary_characters, active_plot_threads
            ):
                # Log before removing
                logger.info(
                    f"Removing unreferenced entity: {node_id} ({node.node_type})"
                )

                # Remove node with cascade to clean up edges
                self.delete_node(node_id, cascade=True)
                removed.append(node_id)

        logger.info(
            f"Cleanup complete: removed {len(removed)} entities, "
            f"{len(self._nodes)} remaining"
        )

        # Auto-save if storage path is configured
        if self.storage_path:
            self._save_to_storage()

        return removed

    def _is_unreferenced(
        self,
        entity: KnowledgeGraphNode,
        recent_chapters: list[str],
        primary_characters: set[str],
        active_plot_threads: list[str],
    ) -> bool:
        """Check if an entity is safe to remove.

        Returns False if entity should be protected (NOT removed).

        Args:
            entity: The node to check
            recent_chapters: Recent chapter content to search for mentions
            primary_characters: Set of protected character IDs
            active_plot_threads: List of active plot thread descriptions

        Returns:
            True if entity can be safely removed, False if protected
        """
        # Protection Rule 1: Primary characters NEVER removed
        if entity.node_id in primary_characters:
            return False

        # Protection Rule 2: Entities with status='active' are kept
        if entity.properties.get("status") == "active":
            return False

        # Get entity name for reference checking
        entity_name = entity.properties.get("name", entity.node_id)

        # Protection Rule 3: Recently mentioned in chapters
        if any(entity_name in chapter for chapter in recent_chapters):
            return False

        # Protection Rule 4: Referenced in active plot threads
        if any(entity_name in thread for thread in active_plot_threads):
            return False

        # Protection Rule 5: Main locations are kept
        if entity.node_type == "location" and entity.properties.get("is_main", False):
            return False

        # All checks passed - entity is unreferenced
        return True


# Factory function
def create_knowledge_graph(
    graph_id: str = "default",
    storage_path: Path | None = None,
) -> KnowledgeGraph:
    """Create a knowledge graph.

    Args:
        graph_id: Unique identifier for the graph
        storage_path: Optional storage path (default: data/knowledge_graphs/{graph_id})

    Returns:
        Initialized KnowledgeGraph
    """
    if storage_path is None:
        # Default to data/knowledge_graphs in project root
        project_root = Path(__file__).parent.parent.parent
        storage_path = project_root / "data" / "knowledge_graphs" / graph_id

    return KnowledgeGraph(graph_id, storage_path)

