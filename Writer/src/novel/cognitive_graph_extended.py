"""Extended Cognitive Graph with inference, conflict resolution, and visualization.

This module extends CognitiveGraph with advanced features:
- Relationship inference from existing data
- Automatic conflict repair suggestions
- Graph visualization export support
- Subgraph extraction for characters
- Indirect relationship path finding
- Graph statistics calculation
"""

from __future__ import annotations

import logging
from typing import Any

from src.novel.cognitive_graph import CognitiveGraph

logger = logging.getLogger(__name__)

# Resolution suggestions for different conflict types
RESOLUTION_SUGGESTIONS: dict[str, str] = {
    "timeline_order": "Consider reordering facts or adjusting timestamps",
    "location_duplicate": "Character may have moved between locations",
    "content_conflict": "Verify which fact is correct through narrative context",
    "knowledge_conflict": "Character may have learned this information earlier",
    "negation_conflict": "One statement may be a correction or update to the other",
}


class ConflictResolution:
    """Represents a suggested resolution for a conflict."""

    def __init__(
        self,
        conflict_id: str,
        conflict_type: str,
        suggestion: str,
        affected_nodes: list[str],
        priority: int = 2,
        auto_fixable: bool = False,
    ) -> None:
        """Initialize a conflict resolution suggestion.

        Args:
            conflict_id: Identifier for the conflict
            conflict_type: Type of conflict (e.g., "timeline_order", "content_conflict")
            suggestion: Human-readable suggestion for resolving the conflict
            affected_nodes: List of node IDs affected by this conflict
            priority: Resolution priority (0=critical, 1=high, 2=medium, 3=low)
            auto_fixable: Whether this conflict can be automatically fixed
        """
        self.conflict_id = conflict_id
        self.conflict_type = conflict_type
        self.suggestion = suggestion
        self.affected_nodes = affected_nodes
        self.priority = priority
        self.auto_fixable = auto_fixable

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "conflict_id": self.conflict_id,
            "conflict_type": self.conflict_type,
            "suggestion": self.suggestion,
            "affected_nodes": self.affected_nodes,
            "priority": self.priority,
            "auto_fixable": self.auto_fixable,
        }


class ExtendedCognitiveGraph(CognitiveGraph):
    """Extended cognitive graph with inference and visualization capabilities.

    Extends CognitiveGraph to provide:
    - Relationship inference based on transitivity and co-location
    - Conflict resolution suggestions
    - Graph visualization export
    - Character subgraph extraction
    - Indirect relationship finding
    - Graph statistics

    Example:
        >>> graph = ExtendedCognitiveGraph()
        >>> graph.add_character_node("char1", "林晚", tier=0)
        >>> graph.add_character_node("char2", "丞相", tier=1)
        >>> graph.add_fact_node("fact1", "secret", "丞相私通敌国", "char2", 3)
        >>>
        >>> # Infer relationships
        >>> inferred = graph.infer_relationships("char1")
        >>>
        >>> # Export for visualization
        >>> viz_data = graph.export_for_visualization()
    """

    def __init__(self, graph_id: str = "default") -> None:
        """Initialize extended cognitive graph.

        Args:
            graph_id: Unique identifier for this graph
        """
        super().__init__(graph_id=graph_id)
        self._inferred_edges: set[tuple[str, str, str]] = set()
        # Track inference metadata
        self._inference_metadata: dict[tuple[str, str, str], dict[str, Any]] = {}

    def infer_relationships(self, character_id: str) -> list[dict[str, Any]]:
        """Infer potential relationships for a character.

        Applies inference rules to discover potential relationships:
        1. Transitivity: If A knows B and B knows C, infer A might know C
        2. Co-location: If A and B are at the same location, infer they might have met
        3. Shared knowledge: If A and B know the same fact, they might have discussed it

        Args:
            character_id: Character to infer relationships for

        Returns:
            List of inferred relationship dictionaries with:
            - target_id: ID of the related node
            - relation_type: Type of inferred relationship
            - confidence: Confidence level (0.0-1.0)
            - inference_method: How the relationship was inferred
            - evidence: Supporting evidence for the inference
        """
        if character_id not in self.graph:
            logger.warning(f"Character {character_id} not found in graph")
            return []

        inferred: list[dict[str, Any]] = []
        character_node = self.graph.nodes[character_id]

        # 1. Transitivity inference: A->B (knows), B->C (knows) => A might know C
        inferred.extend(self._infer_transitive_relationships(character_id))

        # 2. Co-location inference: Same location implies potential meeting
        inferred.extend(self._infer_colocation_relationships(character_id))

        # 3. Shared knowledge inference: Common facts imply discussion
        inferred.extend(self._infer_shared_knowledge_relationships(character_id))

        # Store inferred edges for tracking
        for rel in inferred:
            edge_key = (character_id, rel["target_id"], rel["relation_type"])
            self._inferred_edges.add(edge_key)
            self._inference_metadata[edge_key] = {
                "confidence": rel["confidence"],
                "inference_method": rel["inference_method"],
                "evidence": rel.get("evidence", []),
            }

        logger.debug(
            f"Inferred {len(inferred)} potential relationships for {character_id}"
        )
        return inferred

    def _infer_transitive_relationships(
        self, character_id: str
    ) -> list[dict[str, Any]]:
        """Infer relationships through transitivity.

        If A knows B and B knows C, infer that A might know of C.

        Args:
            character_id: Character to analyze

        Returns:
            List of inferred relationships
        """
        inferred: list[dict[str, Any]] = []

        # Get all characters this character knows
        direct_known = self.get_neighbors(character_id, relation_type="knows")

        for known_id in direct_known:
            # Get what the known character knows
            if self.graph.nodes[known_id].get("node_type") == "character":
                known_by_known = self.get_neighbors(known_id, relation_type="knows")

                for indirect_id in known_by_known:
                    # Skip self and already known
                    if indirect_id == character_id:
                        continue
                    if indirect_id in direct_known:
                        continue

                    # Check if relationship already exists
                    edge_key = (character_id, indirect_id, "knows_of")
                    if edge_key in self._inferred_edges:
                        continue

                    # Infer "knows_of" relationship
                    target_node = self.graph.nodes.get(indirect_id)
                    if target_node:
                        inferred.append({
                            "target_id": indirect_id,
                            "target_name": target_node.get("name", indirect_id),
                            "relation_type": "knows_of",
                            "confidence": 0.6,  # Lower confidence for inferred
                            "inference_method": "transitivity",
                            "evidence": [f"Both connected through {known_id}"],
                        })

        return inferred

    def _infer_colocation_relationships(
        self, character_id: str
    ) -> list[dict[str, Any]]:
        """Infer relationships from co-location.

        If A and B are at the same location, they might have met.

        Args:
            character_id: Character to analyze

        Returns:
            List of inferred relationships
        """
        inferred: list[dict[str, Any]] = []

        # Get locations this character is at
        locations = self.get_neighbors(character_id, relation_type="located_at")

        for location_id in locations:
            # Find other characters at this location
            for node_id, node_data in self.graph.nodes(data=True):
                if node_id == character_id:
                    continue
                if node_data.get("node_type") != "character":
                    continue

                # Check if this character is at the same location
                other_locations = self.get_neighbors(node_id, relation_type="located_at")
                if location_id in other_locations:
                    # Check if relationship already exists
                    edge_key = (character_id, node_id, "met")
                    if edge_key in self._inferred_edges:
                        continue

                    location_name = self.graph.nodes[location_id].get(
                        "name", location_id
                    )
                    inferred.append({
                        "target_id": node_id,
                        "target_name": node_data.get("name", node_id),
                        "relation_type": "met",
                        "confidence": 0.7,
                        "inference_method": "co-location",
                        "evidence": [f"Both at {location_name}"],
                    })

        return inferred

    def _infer_shared_knowledge_relationships(
        self, character_id: str
    ) -> list[dict[str, Any]]:
        """Infer relationships from shared knowledge.

        If A and B know the same fact, they might have discussed it.

        Args:
            character_id: Character to analyze

        Returns:
            List of inferred relationships
        """
        inferred: list[dict[str, Any]] = []

        # Get facts this character knows
        known_facts = set(self.get_neighbors(character_id, relation_type="knows"))

        # Find other characters who know the same facts
        for node_id, node_data in self.graph.nodes(data=True):
            if node_id == character_id:
                continue
            if node_data.get("node_type") != "character":
                continue

            other_facts = set(self.get_neighbors(node_id, relation_type="knows"))
            shared_facts = known_facts & other_facts

            if shared_facts:
                # Check if relationship already exists
                edge_key = (character_id, node_id, "discussed_with")
                if edge_key in self._inferred_edges:
                    continue

                # Get fact names for evidence
                fact_names = []
                for fact_id in list(shared_facts)[:3]:  # Limit to 3 for brevity
                    fact_node = self.graph.nodes.get(fact_id)
                    if fact_node:
                        fact_names.append(
                            fact_node.get("content", fact_id)[:30] + "..."
                        )

                inferred.append({
                    "target_id": node_id,
                    "target_name": node_data.get("name", node_id),
                    "relation_type": "discussed_with",
                    "confidence": 0.5 + (len(shared_facts) * 0.1),  # More shared = higher confidence
                    "inference_method": "shared_knowledge",
                    "evidence": fact_names,
                    "shared_fact_count": len(shared_facts),
                })

        return inferred

    def suggest_conflict_resolutions(
        self, conflict_id: str
    ) -> list[ConflictResolution]:
        """Suggest how to resolve a conflict.

        Analyzes the conflict and provides actionable suggestions for resolution.

        Args:
            conflict_id: ID of the conflict (fact ID or conflict pair identifier)

        Returns:
            List of ConflictResolution suggestions
        """
        resolutions: list[ConflictResolution] = []

        # Get the conflicting fact
        fact_node = self.get_node(conflict_id)
        if not fact_node or fact_node.get("node_type") != "fact":
            logger.warning(f"Conflict {conflict_id} not found or not a fact")
            return resolutions

        # Find conflicting facts
        conflicts = self.check_consistency(conflict_id)

        for conflict in conflicts:
            conflict_type = self._determine_conflict_type(fact_node, conflict)
            suggestion = RESOLUTION_SUGGESTIONS.get(
                conflict_type, "Review and verify the conflicting facts"
            )

            resolution = ConflictResolution(
                conflict_id=f"{conflict_id}_vs_{conflict['id']}",
                conflict_type=conflict_type,
                suggestion=suggestion,
                affected_nodes=[conflict_id, conflict["id"]],
                priority=self._get_conflict_priority(conflict_type),
                auto_fixable=conflict_type == "timeline_order",
            )
            resolutions.append(resolution)

        # Add general suggestions based on fact type
        fact_type = fact_node.get("fact_type", "")
        if fact_type == "event":
            resolutions.append(ConflictResolution(
                conflict_id=f"{conflict_id}_timeline_check",
                conflict_type="timeline_order",
                suggestion="Verify the chronological order of events in the narrative",
                affected_nodes=[conflict_id],
                priority=2,
                auto_fixable=False,
            ))
        elif fact_type == "location":
            resolutions.append(ConflictResolution(
                conflict_id=f"{conflict_id}_location_check",
                conflict_type="location_duplicate",
                suggestion="Check if character locations are consistent with travel",
                affected_nodes=[conflict_id],
                priority=2,
                auto_fixable=False,
            ))

        return resolutions

    def _determine_conflict_type(
        self, fact1: dict[str, Any], fact2: dict[str, Any]
    ) -> str:
        """Determine the type of conflict between two facts.

        Args:
            fact1: First conflicting fact
            fact2: Second conflicting fact

        Returns:
            Conflict type string
        """
        content1 = fact1.get("content", "").lower()
        content2 = fact2.get("content", "").lower()

        # Check for negation conflict
        if self._is_negation_conflict(content1, content2):
            return "negation_conflict"

        # Check for timeline conflict (different chapters, same content)
        chapter1 = fact1.get("chapter", 0)
        chapter2 = fact2.get("chapter", 0)
        if chapter1 != chapter2:
            return "timeline_order"

        # Default to content conflict
        return "content_conflict"

    def _is_negation_conflict(self, content1: str, content2: str) -> bool:
        """Check if two contents have a negation conflict.

        Args:
            content1: First content string
            content2: Second content string

        Returns:
            True if there's a negation conflict
        """
        # Reuse the parent class's conflict detection
        return self._contents_conflict(content1, content2)

    def _get_conflict_priority(self, conflict_type: str) -> int:
        """Get priority for a conflict type.

        Args:
            conflict_type: Type of conflict

        Returns:
            Priority level (0=critical, 3=low)
        """
        priorities: dict[str, int] = {
            "negation_conflict": 0,
            "timeline_order": 1,
            "content_conflict": 1,
            "location_duplicate": 2,
            "knowledge_conflict": 2,
        }
        return priorities.get(conflict_type, 2)

    def export_for_visualization(self) -> dict[str, Any]:
        """Export graph data for visualization.

        Creates a JSON-serializable dictionary suitable for:
        - D3.js force-directed graphs
        - Cytoscape.js graphs
        - Other graph visualization libraries

        Returns:
            Dictionary with:
            - nodes: List of node objects with id, type, label, and properties
            - edges: List of edge objects with source, target, label, and confidence
            - statistics: Graph statistics
        """
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []

        # Export nodes
        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get("node_type", "unknown")
            label = data.get("name", data.get("content", node_id)[:30])

            node: dict[str, Any] = {
                "id": node_id,
                "type": node_type,
                "label": label,
            }

            # Add type-specific properties
            if node_type == "character":
                node["tier"] = data.get("tier", 1)
                node["name"] = data.get("name", node_id)
            elif node_type == "fact":
                node["fact_type"] = data.get("fact_type", "unknown")
                node["chapter"] = data.get("chapter", 0)
                node["content"] = data.get("content", "")[:100]
            elif node_type == "location":
                node["name"] = data.get("name", node_id)

            nodes.append(node)

        # Export edges
        for from_id, to_id, data in self.graph.edges(data=True):
            relation_type = data.get("relation_type", "unknown")
            confidence = data.get("confidence", 1.0)

            edge: dict[str, Any] = {
                "source": from_id,
                "target": to_id,
                "label": relation_type,
                "confidence": round(confidence, 2),
            }

            # Add inference metadata if this is an inferred edge
            edge_key = (from_id, to_id, relation_type)
            if edge_key in self._inference_metadata:
                edge["inferred"] = True
                edge["inference_method"] = self._inference_metadata[edge_key].get(
                    "inference_method"
                )

            edges.append(edge)

        # Export inferred edges (those not in the main graph)
        for edge_key in self._inferred_edges:
            source, target, relation_type = edge_key
            # Only add if not already in the graph edges
            if not self.graph.has_edge(source, target):
                metadata = self._inference_metadata.get(edge_key, {})
                edges.append({
                    "source": source,
                    "target": target,
                    "label": relation_type,
                    "confidence": round(metadata.get("confidence", 0.5), 2),
                    "inferred": True,
                    "inference_method": metadata.get("inference_method"),
                })

        # Add statistics
        statistics = self.get_graph_statistics()

        return {
            "nodes": nodes,
            "edges": edges,
            "statistics": statistics,
            "graph_id": self.graph_id,
        }

    def get_character_subgraph(self, character_id: str) -> dict[str, Any]:
        """Get subgraph centered on a character.

        Extracts all nodes and edges relevant to a specific character:
        - The character node itself
        - All facts they know
        - All locations they're at
        - All characters they have relationships with
        - All relevant edges

        Args:
            character_id: Character to get subgraph for

        Returns:
            Dictionary with nodes and edges for the character's subgraph
        """
        if character_id not in self.graph:
            logger.warning(f"Character {character_id} not found in graph")
            return {"nodes": [], "edges": [], "character_id": character_id}

        # Collect relevant node IDs
        relevant_nodes: set[str] = {character_id}
        relevant_edges: list[tuple[str, str, dict[str, Any]]] = []

        # Get all direct relationships
        relationships = self.get_relationships(character_id)
        for from_id, to_id, edge_data in relationships:
            relevant_nodes.add(from_id)
            relevant_nodes.add(to_id)
            relevant_edges.append((from_id, to_id, edge_data))

        # Get facts the character knows
        knowledge = self.get_character_knowledge(character_id)
        for fact_data, confidence, source in knowledge:
            fact_id = fact_data.get("id")
            if fact_id:
                relevant_nodes.add(fact_id)
                edge_data = {
                    "relation_type": "knows",
                    "confidence": confidence,
                    "source": source,
                }
                relevant_edges.append((character_id, fact_id, edge_data))

        # Build subgraph dict
        nodes: list[dict[str, Any]] = []
        for node_id in relevant_nodes:
            node_data = self.graph.nodes.get(node_id)
            if node_data:
                nodes.append({"id": node_id, **dict(node_data)})

        edges: list[dict[str, Any]] = []
        for from_id, to_id, data in relevant_edges:
            edges.append({
                "from": from_id,
                "to": to_id,
                **data,
            })

        return {
            "character_id": character_id,
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    def find_indirect_relationships(
        self, character_id: str, target_id: str, max_depth: int = 3
    ) -> list[dict[str, Any]]:
        """Find relationship paths between two characters.

        Uses BFS to find all paths up to max_depth edges between two nodes.

        Args:
            character_id: Starting character ID
            target_id: Target character ID
            max_depth: Maximum path length to search

        Returns:
            List of path dictionaries, each containing:
            - path: List of node IDs from source to target
            - edges: List of edge data along the path
            - length: Path length (number of edges)
            - confidence: Combined confidence of all edges
        """
        if character_id not in self.graph:
            logger.warning(f"Character {character_id} not found in graph")
            return []
        if target_id not in self.graph:
            logger.warning(f"Target {target_id} not found in graph")
            return []

        paths: list[dict[str, Any]] = []
        queue: list[tuple[str, list[str], list[dict[str, Any]], float]]

        # BFS to find paths
        queue = [(character_id, [character_id], [], 1.0)]

        while queue:
            current, path, edges, confidence = queue.pop(0)

            if len(path) > max_depth + 1:
                continue

            if current == target_id and len(path) > 1:
                paths.append({
                    "path": path,
                    "edges": edges,
                    "length": len(edges),
                    "confidence": round(confidence, 3),
                })
                continue

            for neighbor in self.graph.neighbors(current):
                if neighbor in path:
                    continue  # Avoid cycles

                edge_data = self.graph.get_edge_data(current, neighbor)
                if edge_data:
                    edge_confidence = edge_data.get("confidence", 1.0)
                    new_confidence = confidence * edge_confidence

                    queue.append((
                        neighbor,
                        path + [neighbor],
                        edges + [{"from": current, "to": neighbor, **dict(edge_data)}],
                        new_confidence,
                    ))

        # Sort by path length, then by confidence
        paths.sort(key=lambda p: (p["length"], -p["confidence"]))

        return paths

    def get_graph_statistics(self) -> dict[str, Any]:
        """Get comprehensive graph statistics.

        Returns:
            Dictionary with:
            - node_count: Total number of nodes
            - edge_count: Total number of edges
            - density: Graph density
            - node_types: Count by node type
            - relation_types: Count by relation type
            - avg_connections: Average connections per node
            - inferred_edge_count: Number of inferred edges
        """
        node_count = self.node_count
        edge_count = self.edge_count

        # Calculate density
        if node_count > 1:
            # For directed graph: max edges = n*(n-1)
            max_edges = node_count * (node_count - 1)
            density = edge_count / max_edges if max_edges > 0 else 0.0
        else:
            density = 0.0

        # Count by node type
        node_types: dict[str, int] = {}
        for _, data in self.graph.nodes(data=True):
            node_type = data.get("node_type", "unknown")
            node_types[node_type] = node_types.get(node_type, 0) + 1

        # Count by relation type
        relation_types: dict[str, int] = {}
        for _, _, data in self.graph.edges(data=True):
            relation_type = data.get("relation_type", "unknown")
            relation_types[relation_type] = relation_types.get(relation_type, 0) + 1

        # Average connections
        avg_connections = edge_count * 2 / node_count if node_count > 0 else 0.0

        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "density": round(density, 4),
            "node_types": node_types,
            "relation_types": relation_types,
            "avg_connections": round(avg_connections, 2),
            "inferred_edge_count": len(self._inferred_edges),
        }

    def clear_inferred_edges(self) -> None:
        """Clear all inferred edges and metadata."""
        self._inferred_edges.clear()
        self._inference_metadata.clear()
        logger.debug("Cleared all inferred edges")

    def get_inferred_edges(self) -> list[dict[str, Any]]:
        """Get all inferred edges with metadata.

        Returns:
            List of inferred edge dictionaries
        """
        result: list[dict[str, Any]] = []
        for edge_key in self._inferred_edges:
            source, target, relation_type = edge_key
            metadata = self._inference_metadata.get(edge_key, {})
            result.append({
                "source": source,
                "target": target,
                "relation_type": relation_type,
                **metadata,
            })
        return result

    def to_dict(self) -> dict[str, Any]:
        """Serialize graph to dictionary, including extended data.

        Returns:
            Dictionary representation including inferred edges
        """
        base_dict = super().to_dict()
        base_dict["inferred_edges"] = [
            {
                "source": e[0],
                "target": e[1],
                "relation_type": e[2],
                **self._inference_metadata.get(e, {}),
            }
            for e in self._inferred_edges
        ]
        return base_dict

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExtendedCognitiveGraph:
        """Deserialize graph from dictionary.

        Args:
            data: Dictionary representation of the graph

        Returns:
            ExtendedCognitiveGraph instance
        """
        graph = cls(graph_id=data.get("graph_id", "default"))

        # Add nodes
        for node_data in data.get("nodes", []):
            node_id = node_data.pop("id")
            graph.graph.add_node(node_id, **node_data)

        # Add edges
        for edge_data in data.get("edges", []):
            from_id = edge_data.pop("from")
            to_id = edge_data.pop("to")
            graph.graph.add_edge(from_id, to_id, **edge_data)

        # Restore inferred edges
        for inferred in data.get("inferred_edges", []):
            source = inferred.pop("source")
            target = inferred.pop("target")
            relation_type = inferred.pop("relation_type")
            edge_key = (source, target, relation_type)
            graph._inferred_edges.add(edge_key)
            graph._inference_metadata[edge_key] = inferred

        return graph
