"""Neo4j graph data models for the novel QA system.

These Pydantic models define the structure of nodes and edges
in the Neo4j graph database, optimized for character tracking,
plot consistency, and reference validation.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Neo4jNode(BaseModel):
    """Represents a node in the Neo4j graph database.

    Nodes represent entities like characters, events, locations, concepts,
    and plot threads with their associated properties.
    """

    node_id: str = Field(..., description="Unique node identifier")
    node_type: str = Field(..., description="Type of node (character, event, location, etc.)")
    properties: dict[str, Any] = Field(default_factory=dict, description="Node properties")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")

    model_config = {"extra": "forbid"}


class Neo4jEdge(BaseModel):
    """Represents a relationship/edge in the Neo4j graph database.

    Edges connect nodes with typed relationships like KNOWS, INVOLVES,
    CAUSES, OCCURS_AT, etc., with optional weights and properties.
    """

    edge_id: str = Field(..., description="Unique edge identifier")
    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    relationship_type: str = Field(..., description="Type of relationship")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Relationship strength")
    properties: dict[str, Any] = Field(default_factory=dict, description="Edge properties")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

    model_config = {"extra": "forbid"}


class Neo4jQuery(BaseModel):
    """Represents a query for the Neo4j graph database.

    Supports filtering by node types, properties, and relationships
    with configurable depth for graph traversal queries.
    """

    node_types: list[str] | None = Field(default=None, description="Filter by node types")
    property_filters: dict[str, Any] | None = Field(
        default=None, description="Filter by property key-value pairs"
    )
    relationship_types: list[str] | None = Field(
        default=None, description="Filter by relationship types"
    )
    depth: int = Field(default=1, ge=0, description="Traversal depth for relationship queries")
    limit: int = Field(default=100, ge=1, description="Maximum number of results")

    model_config = {"extra": "forbid"}


# Relationship type constants for the novel QA system
class RelationshipType:
    """Common relationship types in the novel graph."""

    # Character relationships
    KNOWS = "KNOWS"
    FAMILY = "FAMILY"
    FRIEND = "FRIEND"
    ENEMY = "ENEMY"
    ALLY = "ALLY"
    ROMANTIC = "ROMANTIC"
    MENTOR = "MENTOR"
    STUDENT = "STUDENT"

    # Character-Event relationships
    INVOLVES = "INVOLVES"
    PARTICIPATES_IN = "PARTICIPATES_IN"
    WITNESSES = "WITNESSES"
    CAUSES = "CAUSES"
    AFFECTED_BY = "AFFECTED_BY"

    # Character-Location relationships
    LIVES_AT = "LIVES_AT"
    VISITS = "VISITS"
    ORIGINATED_FROM = "ORIGINATED_FROM"

    # Event relationships
    FOLLOWS = "FOLLOWS"
    PRECEDES = "PRECEDES"
    LEADS_TO = "LEADS_TO"
    SIMULTANEOUS_WITH = "SIMULTANEOUS_WITH"

    # Plot relationships
    ADVANCES = "ADVANCES"
    RESOLVES = "RESOLVES"
    CONFLICTS_WITH = "CONFLICTS_WITH"
    CONNECTS = "CONNECTS"

    # General relationships
    REFERENCES = "REFERENCES"
    MENTIONS = "MENTIONS"
    RELATED_TO = "RELATED_TO"


# Node type constants
class NodeType:
    """Common node types in the novel graph."""

    CHARACTER = "character"
    EVENT = "event"
    LOCATION = "location"
    CONCEPT = "concept"
    PLOT_THREAD = "plot_thread"
    OBJECT = "object"
    THEME = "theme"
    CHAPTER = "chapter"
