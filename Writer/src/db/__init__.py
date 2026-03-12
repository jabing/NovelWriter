# src/db/__init__.py
"""Database integrations for Neo4j, PostgreSQL, and Pinecone.

Provides unified interface for various database backends.
"""

# PostgreSQL imports (primary relational database)
try:
    from src.db.postgres_client import PostgresClient
    from src.db.postgres_models import (
        Base,
        CharacterProfile,
        Contradiction,
        StoryFact,
        TimelineEvent,
    )
except ImportError:
    # PostgreSQL not yet installed
    PostgresClient = None  # type: ignore
    CharacterProfile = None  # type: ignore
    TimelineEvent = None  # type: ignore
    StoryFact = None  # type: ignore
    Contradiction = None  # type: ignore
    Base = None  # type: ignore

# Neo4j imports
try:
    from src.db.neo4j_client import Neo4jClient
    from src.db.neo4j_models import Neo4jEdge, Neo4jNode, Neo4jQuery
except ImportError:
    Neo4jClient = None  # type: ignore
    Neo4jNode = None  # type: ignore
    Neo4jEdge = None  # type: ignore
    Neo4jQuery = None  # type: ignore

# Pinecone imports (optional - for vector embeddings)
try:
    from src.db.pinecone_client import EmbeddingGenerator, VectorStore
except ImportError:
    # Pinecone not installed - that's okay
    VectorStore = None  # type: ignore
    EmbeddingGenerator = None  # type: ignore

__all__ = [
    # Neo4j
    "Neo4jClient",
    "Neo4jNode",
    "Neo4jEdge",
    "Neo4jQuery",
    # PostgreSQL
    "PostgresClient",
    "CharacterProfile",
    "TimelineEvent",
    "StoryFact",
    "Contradiction",
    "Base",
    # Pinecone
    "VectorStore",
    "EmbeddingGenerator",
]
