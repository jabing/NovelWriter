"""Graph-related Pydantic schemas for Cytoscape.js API responses."""

from typing import Any

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    """Represents a node in the Cytoscape.js graph format.

    Attributes:
        data: Node data containing id, label, type, and properties
    """

    data: dict[str, Any] = Field(
        ..., description="Node data containing id, label, type, and properties"
    )


class GraphEdge(BaseModel):
    """Represents an edge (relationship) in the Cytoscape.js graph format.

    Attributes:
        data: Edge data containing source, target, relationship type, and properties
    """

    data: dict[str, Any] = Field(
        ..., description="Edge data containing source, target, relationship type, and properties"
    )


class GraphResponse(BaseModel):
    """Response schema for graph queries in Cytoscape.js format.

    Attributes:
        nodes: List of graph nodes
        edges: List of graph edges
    """

    nodes: list[GraphNode] = Field(default_factory=list, description="List of graph nodes")
    edges: list[GraphEdge] = Field(default_factory=list, description="List of graph edges")


class RelationshipType(str):
    """Relationship type constants for character relationships."""

    KNOWS = "KNOWS"
    FAMILY = "FAMILY"
    FRIEND = "FRIEND"
    ENEMY = "ENEMY"
    ALLY = "ALLY"
    ROMANTIC = "ROMANTIC"
    MENTOR = "MENTOR"
    STUDENT = "STUDENT"
    RIVAL = "RIVAL"
    BUSINESS = "BUSINESS"
