"""Cognitive Graph for double-layer consistency checking.

This module implements a simplified cognitive graph using NetworkX
for managing character knowledge and relationships.
"""

from __future__ import annotations

from typing import Any

import networkx as nx


class CognitiveGraph:
    """Simplified cognitive graph for prototype.
    
    Uses NetworkX DiGraph to represent:
    - Character nodes and their knowledge
    - Location nodes and relationships
    - Plot thread connections
    """
    
    def __init__(self, graph_id: str = "default") -> None:
        """Initialize cognitive graph.
        
        Args:
            graph_id: Unique identifier for this graph
        """
        self.graph_id = graph_id
        self.graph: nx.DiGraph = nx.DiGraph()
    
    def add_character_node(
        self,
        character_id: str,
        name: str,
        tier: int = 1,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Add a character node to the graph.
        
        Args:
            character_id: Unique character identifier
            name: Character name
            tier: Character tier (0=protagonist, 1=important, 2=normal, 3=public)
            properties: Additional character properties
        """
        props = properties or {}
        self.graph.add_node(
            character_id,
            node_type="character",
            name=name,
            tier=tier,
            **props
        )
    
    def add_location_node(
        self,
        location_id: str,
        name: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Add a location node to the graph.
        
        Args:
            location_id: Unique location identifier
            name: Location name
            properties: Additional location properties
        """
        props = properties or {}
        self.graph.add_node(
            location_id,
            node_type="location",
            name=name,
            **props
        )
    
    def add_plot_thread_node(
        self,
        thread_id: str,
        name: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Add a plot thread node to the graph.
        
        Args:
            thread_id: Unique plot thread identifier
            name: Plot thread name
            properties: Additional plot thread properties
        """
        props = properties or {}
        self.graph.add_node(
            thread_id,
            node_type="plot_thread",
            name=name,
            **props
        )
    
    def add_fact_node(
        self,
        fact_id: str,
        fact_type: str,
        content: str,
        source_character: str,
        chapter: int,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Add a fact node to the graph.
        
        Facts represent pieces of information that characters know.
        
        Args:
            fact_id: Unique fact identifier
            fact_type: Type of fact (e.g., "event", "secret", "relationship")
            content: The factual content/statement
            source_character: Character ID who is the source of this fact
            chapter: Chapter number where this fact was established
            properties: Additional fact properties
        """
        props = properties or {}
        self.graph.add_node(
            fact_id,
            node_type="fact",
            fact_type=fact_type,
            content=content,
            source_character=source_character,
            chapter=chapter,
            **props
        )
    
    def get_facts_for_character(self, character_id: str) -> list[dict[str, Any]]:
        """Get all facts known by a character.
        
        Args:
            character_id: Character identifier
            
        Returns:
            List of fact dictionaries with node data
        """
        facts = []
        for node_id, data in self.graph.nodes(data=True):
            if data.get("node_type") == "fact":
                # Check if this fact originated from or is known by the character
                if data.get("source_character") == character_id:
                    facts.append({"id": node_id, **data})
                else:
                    # Check for "knows" relationship
                    edge_data = self.graph.get_edge_data(character_id, node_id)
                    if edge_data and edge_data.get("relation_type") == "knows":
                        facts.append({"id": node_id, **data})
        return facts
    
    def get_facts_by_type(self, fact_type: str) -> list[dict[str, Any]]:
        """Get all facts of a specific type.
        
        Args:
            fact_type: Type of fact to filter by
            
        Returns:
            List of fact dictionaries with node data
        """
        facts = []
        for node_id, data in self.graph.nodes(data=True):
            if data.get("node_type") == "fact" and data.get("fact_type") == fact_type:
                facts.append({"id": node_id, **data})
        return facts
    
    def add_character_knowledge(
        self,
        character_id: str,
        fact_id: str,
        confidence: float = 1.0,
        source: str = "direct",
    ) -> None:
        """Link a character to a fact with a knowledge relation.
        
        Args:
            character_id: Character who knows the fact
            fact_id: Fact that the character knows
            confidence: Confidence level (0.0-1.0) of character's knowledge
            source: How the character learned this (e.g., "direct", "hearsay", "inference")
        """
        self.graph.add_edge(
            character_id,
            fact_id,
            relation_type="knows",
            confidence=confidence,
            source=source,
        )
    
    def get_character_knowledge(
        self,
        character_id: str,
    ) -> list[tuple[dict[str, Any], float, str]]:
        """Get all facts a character knows with confidence scores.
        
        Args:
            character_id: Character identifier
            
        Returns:
            List of (fact_data, confidence, source) tuples
        """
        knowledge = []
        if character_id not in self.graph:
            return knowledge
        
        for neighbor in self.graph.neighbors(character_id):
            edge_data = self.graph.get_edge_data(character_id, neighbor)
            if edge_data and edge_data.get("relation_type") == "knows":
                node_data = self.graph.nodes.get(neighbor)
                if node_data and node_data.get("node_type") == "fact":
                    fact_data = {"id": neighbor, **dict(node_data)}
                    confidence = edge_data.get("confidence", 1.0)
                    source = edge_data.get("source", "direct")
                    knowledge.append((fact_data, confidence, source))
        
        return knowledge
    
    def add_relationship(
        self,
        from_id: str,
        to_id: str,
        relation_type: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Add a relationship edge between nodes.
        
        Args:
            from_id: Source node ID
            to_id: Target node ID
            relation_type: Type of relationship (e.g., "knows", "located_at")
            properties: Additional edge properties
        """
        props = properties or {}
        self.graph.add_edge(
            from_id,
            to_id,
            relation_type=relation_type,
            **props
        )
    
    def get_node(self, node_id: str) -> dict[str, Any] | None:
        """Get node data.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Node properties or None if not found
        """
        if node_id not in self.graph:
            return None
        return dict(self.graph.nodes[node_id])
    
    def get_neighbors(
        self,
        node_id: str,
        relation_type: str | None = None,
    ) -> list[str]:
        """Get neighboring nodes.
        
        Args:
            node_id: Node identifier
            relation_type: Optional filter by relation type
            
        Returns:
            List of neighbor node IDs
        """
        if node_id not in self.graph:
            return []
        
        if relation_type is None:
            return list(self.graph.neighbors(node_id))
        
        # Filter by relation type
        neighbors = []
        for neighbor in self.graph.neighbors(node_id):
            edge_data = self.graph.get_edge_data(node_id, neighbor)
            if edge_data and edge_data.get("relation_type") == relation_type:
                neighbors.append(neighbor)
        
        return neighbors
    
    def get_relationships(
        self,
        node_id: str,
        relation_type: str | None = None,
    ) -> list[tuple[str, str, dict[str, Any]]]:
        """Get all relationships for a node.
        
        Args:
            node_id: Node identifier
            relation_type: Optional filter by relation type
            
        Returns:
            List of (from_id, to_id, edge_data) tuples
        """
        if node_id not in self.graph:
            return []
        
        relationships = []
        
        # Outgoing edges
        for neighbor in self.graph.neighbors(node_id):
            edge_data = self.graph.get_edge_data(node_id, neighbor)
            if relation_type is None or edge_data.get("relation_type") == relation_type:
                relationships.append((node_id, neighbor, dict(edge_data)))
        
        # Incoming edges
        for predecessor in self.graph.predecessors(node_id):
            edge_data = self.graph.get_edge_data(predecessor, node_id)
            if relation_type is None or edge_data.get("relation_type") == relation_type:
                relationships.append((predecessor, node_id, dict(edge_data)))
        
        return relationships
    
    def get_nodes_by_type(self, node_type: str) -> list[str]:
        """Get all nodes of a specific type.
        
        Args:
            node_type: Type of node (character, location, plot_thread)
            
        Returns:
            List of node IDs matching the type
        """
        return [
            node_id
            for node_id, data in self.graph.nodes(data=True)
            if data.get("node_type") == node_type
        ]
    
    def remove_node(self, node_id: str) -> bool:
        """Remove a node from the graph.
        
        Args:
            node_id: Node identifier
            
        Returns:
            True if node was removed, False if not found
        """
        if node_id not in self.graph:
            return False
        self.graph.remove_node(node_id)
        return True
    
    def clear(self) -> None:
        """Clear all nodes and edges from the graph."""
        self.graph.clear()
    
    @property
    def node_count(self) -> int:
        """Get total number of nodes."""
        return self.graph.number_of_nodes()
    
    @property
    def edge_count(self) -> int:
        """Get total number of edges."""
        return self.graph.number_of_edges()
    
    def check_consistency(self, fact_id: str) -> list[dict[str, Any]]:
        """Check if a fact conflicts with other facts in the graph.
        
        Uses simple string matching for prototype implementation.
        
        Args:
            fact_id: Fact identifier to check
            
        Returns:
            List of conflicting fact dictionaries (empty if no conflicts)
        """
        if fact_id not in self.graph:
            return []
        
        fact_data = self.graph.nodes[fact_id]
        if fact_data.get("node_type") != "fact":
            return []
        
        content = fact_data.get("content", "").lower()
        fact_type = fact_data.get("fact_type", "")
        conflicts = []
        
        for node_id, data in self.graph.nodes(data=True):
            if node_id == fact_id:
                continue
            if data.get("node_type") != "fact":
                continue
            
            other_content = data.get("content", "").lower()
            other_type = data.get("fact_type", "")
            
            if fact_type == other_type and self._contents_conflict(content, other_content):
                conflicts.append({"id": node_id, **data})
        
        return conflicts
    
    def _contents_conflict(self, content1: str, content2: str) -> bool:
        """Check if two fact contents conflict with each other.
        
        Simple string-based conflict detection for prototype.
        Detects negations and contradictory statements.
        
        Args:
            content1: First fact content
            content2: Second fact content
            
        Returns:
            True if contents appear to conflict
        """
        chinese_negations = ["不", "没", "非", "无", "未"]
        english_negations = ["not ", "no ", "never ", "did not ", "does not ", "is not "]
        
        def has_negation(text: str) -> bool:
            for neg in chinese_negations:
                if neg in text:
                    return True
            for neg in english_negations:
                if neg in text:
                    return True
            return False
        
        def remove_negations(text: str) -> str:
            result = text
            for neg in chinese_negations:
                result = result.replace(neg, "")
            for neg in english_negations:
                result = result.replace(neg, "")
            return result.strip()
        
        has_negation1 = has_negation(content1)
        has_negation2 = has_negation(content2)
        
        base1 = remove_negations(content1)
        base2 = remove_negations(content2)
        
        if base1 and base2 and base1 == base2 and has_negation1 != has_negation2:
            return True
        
        return False
    
    def find_conflicts(self) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        """Find all conflicting fact pairs in the graph.
        
        Returns:
            List of (fact1, fact2) tuples representing conflicts
        """
        conflicts = []
        facts = [
            (node_id, data)
            for node_id, data in self.graph.nodes(data=True)
            if data.get("node_type") == "fact"
        ]
        
        checked_pairs: set[tuple[str, str]] = set()
        
        for i, (fact_id1, data1) in enumerate(facts):
            for fact_id2, data2 in facts[i + 1:]:
                pair_key = tuple(sorted([fact_id1, fact_id2]))
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)
                
                if data1.get("fact_type") != data2.get("fact_type"):
                    continue
                
                content1 = data1.get("content", "").lower()
                content2 = data2.get("content", "").lower()
                
                if self._contents_conflict(content1, content2):
                    conflicts.append((
                        {"id": fact_id1, **data1},
                        {"id": fact_id2, **data2},
                    ))
        
        return conflicts
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize graph to dictionary.
        
        Returns:
            Dictionary representation of the graph
        """
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                **data
            })
        
        edges = []
        for from_id, to_id, data in self.graph.edges(data=True):
            edges.append({
                "from": from_id,
                "to": to_id,
                **data
            })
        
        return {
            "graph_id": self.graph_id,
            "nodes": nodes,
            "edges": edges,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CognitiveGraph:
        """Deserialize graph from dictionary.
        
        Args:
            data: Dictionary representation of the graph
            
        Returns:
            CognitiveGraph instance
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
        
        return graph
