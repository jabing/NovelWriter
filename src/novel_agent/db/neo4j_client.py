"""Neo4j graph database client for knowledge graph storage.

Provides async interface for connecting to Neo4j and performing
CRUD operations on nodes and relationships.

Usage:
    client = Neo4jClient(uri="bolt://localhost:7687", user="neo4j", password="password")
    await client.connect()
    await client.create_node("character", {"name": "Alice", "age": 25})
    await client.close()
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class Neo4jConfig:
    """Configuration for Neo4j connection."""

    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = ""
    database: str = "neo4j"
    max_connection_pool_size: int = 50
    connection_timeout: float = 30.0
    max_retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class NodeResult:
    """Result of a node operation."""

    success: bool
    node_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class RelationshipResult:
    """Result of a relationship operation."""

    success: bool
    rel_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class QueryResult:
    """Result of a Cypher query."""

    success: bool
    records: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class Neo4jClient:
    """Async Neo4j client for knowledge graph operations.

    This client provides a high-level interface for interacting with Neo4j
    graph database, supporting batch operations and connection management.

    Attributes:
        config: Neo4j connection configuration
        _driver: Neo4j driver instance (lazy initialization)
        _connected: Whether client is connected
    """

    def __init__(self, config: Neo4jConfig | None = None) -> None:
        """Initialize the Neo4j client.

        Args:
            config: Optional configuration object. If None, uses defaults.
        """
        self.config = config or Neo4jConfig()
        self._driver = None
        self._connected = False
        self._transaction_session = None

    async def connect(self) -> bool:
        """Establish connection to Neo4j database.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Import neo4j driver (will fail if not installed)
            from neo4j import AsyncGraphDatabase

            self._driver = AsyncGraphDatabase.driver(
                self.config.uri,
                auth=(self.config.user, self.config.password),
                max_connection_pool_size=self.config.max_connection_pool_size,
                connection_timeout=self.config.connection_timeout,
            )

            # Verify connection
            await self._driver.verify_connectivity()
            self._connected = True
            logger.info(f"Connected to Neo4j at {self.config.uri}")
            return True

        except ImportError:
            logger.error("neo4j package not installed. Install with: pip install neo4j>=5.0.0")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self._connected = False
            return False

    async def close(self) -> None:
        """Close the Neo4j connection."""
        if self._driver:
            await self._driver.close()
            self._driver = None
            self._connected = False
            logger.info("Neo4j connection closed")

    @asynccontextmanager
    async def session(self, database: str | None = None):
        """Get an async session context manager.

        Args:
            database: Optional database name (defaults to config.database)

        Yields:
            Neo4j async session
        """
        if not self._connected or not self._driver:
            raise RuntimeError("Not connected to Neo4j. Call connect() first.")

        db = database or self.config.database
        async with self._driver.session(database=db) as session:
            yield session

    async def execute_query(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        database: str | None = None,
    ) -> QueryResult:
        """Execute a Cypher query.

        Args:
            query: Cypher query string
            parameters: Query parameters
            database: Optional database name

        Returns:
            QueryResult with records and summary
        """
        if not self._connected:
            return QueryResult(success=False, error="Not connected to Neo4j")

        params = parameters or {}
        attempts = 0

        while attempts < self.config.max_retry_attempts:
            try:
                async with self.session(database) as session:
                    result = await session.run(query, params)
                    records = [dict(record) async for record in result]
                    summary = await result.consume()

                    return QueryResult(
                        success=True,
                        records=records,
                        summary={
                            "query_type": summary.query_type,
                            "counters": dict(summary.counters),
                        },
                    )

            except Exception as e:
                attempts += 1
                if attempts >= self.config.max_retry_attempts:
                    logger.error(f"Query failed after {attempts} attempts: {e}")
                    return QueryResult(success=False, error=str(e))

                await asyncio.sleep(self.config.retry_delay)
                logger.warning(
                    f"Query failed, retrying ({attempts}/{self.config.max_retry_attempts}): {e}"
                )

        return QueryResult(success=False, error="Max retry attempts exceeded")

    async def create_node(
        self,
        label: str,
        properties: dict[str, Any],
        node_id: str | None = None,
    ) -> NodeResult:
        """Create a node in the graph.

        Args:
            label: Node label (e.g., "Character", "Location")
            properties: Node properties
            node_id: Optional unique identifier (will use UUID if not provided)

        Returns:
            NodeResult with created node info
        """
        import uuid

        nid = node_id or str(uuid.uuid4())

        # Add timestamp
        props = dict(properties)
        props["node_id"] = nid
        props["created_at"] = datetime.now().isoformat()

        query = f"""
        MERGE (n:{label} {{node_id: $node_id}})
        SET n += $properties
        RETURN n
        """

        result = await self.execute_query(query, {"node_id": nid, "properties": props})

        if result.success and result.records:
            return NodeResult(success=True, node_id=nid, data=props)

        return NodeResult(success=False, error=result.error)

    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: dict[str, Any] | None = None,
        rel_id: str | None = None,
    ) -> RelationshipResult:
        """Create a relationship between two nodes.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            rel_type: Relationship type (e.g., "KNOWS", "LOCATED_AT")
            properties: Optional relationship properties
            rel_id: Optional unique identifier for the relationship

        Returns:
            RelationshipResult with created relationship info
        """
        import uuid

        rid = rel_id or str(uuid.uuid4())
        props = dict(properties or {})
        props["rel_id"] = rid
        props["created_at"] = datetime.now().isoformat()

        query = f"""
        MATCH (source {{node_id: $source_id}})
        MATCH (target {{node_id: $target_id}})
        MERGE (source)-[r:{rel_type} {{rel_id: $rel_id}}]->(target)
        SET r += $properties
        RETURN r
        """

        result = await self.execute_query(
            query,
            {
                "source_id": source_id,
                "target_id": target_id,
                "rel_id": rid,
                "properties": props,
            },
        )

        if result.success and result.records:
            return RelationshipResult(success=True, rel_id=rid, data=props)

        return RelationshipResult(success=False, error=result.error)

    async def batch_create_nodes(
        self,
        nodes: list[tuple[str, dict[str, Any]]],
        batch_size: int = 1000,
        progress_callback: Callable | None = None,
    ) -> tuple[int, list[str]]:
        """Batch create nodes for better performance.

        Args:
            nodes: List of (label, properties) tuples
            batch_size: Number of nodes per batch
            progress_callback: Optional callback(current, total) for progress

        Returns:
            Tuple of (success_count, error_messages)
        """
        success_count = 0
        errors = []
        total = len(nodes)

        for i in range(0, total, batch_size):
            batch = nodes[i : i + batch_size]

            # Build UNWIND query for batch
            query = """
            UNWIND $nodes AS node_data
            CALL apoc.create.node([node_data.label], node_data.properties) YIELD n
            RETURN n.node_id AS node_id
            """

            # Prepare batch data
            batch_data = [
                {
                    "label": label,
                    "properties": {
                        **props,
                        "node_id": props.get("node_id") or str(uuid.uuid4()),
                        "created_at": datetime.now().isoformat(),
                    },
                }
                for label, props in batch
            ]

            # Try with APOC first, fall back to standard Cypher
            try:
                result = await self.execute_query(query, {"nodes": batch_data})
                if result.success:
                    success_count += len(batch)
                else:
                    # Fallback to individual creates
                    for label, props in batch:
                        node_result = await self.create_node(label, props)
                        if node_result.success:
                            success_count += 1
                        else:
                            errors.append(node_result.error or "Unknown error")
            except Exception:
                # APOC not available, use individual creates
                for label, props in batch:
                    node_result = await self.create_node(label, props)
                    if node_result.success:
                        success_count += 1
                    else:
                        errors.append(node_result.error or "Unknown error")

            if progress_callback:
                progress_callback(min(i + batch_size, total), total)

        return success_count, errors

    async def batch_create_relationships(
        self,
        relationships: list[tuple[str, str, str, dict[str, Any]]],
        batch_size: int = 1000,
        progress_callback: Callable | None = None,
    ) -> tuple[int, list[str]]:
        """Batch create relationships for better performance.

        Args:
            relationships: List of (source_id, target_id, rel_type, properties) tuples
            batch_size: Number of relationships per batch
            progress_callback: Optional callback(current, total) for progress

        Returns:
            Tuple of (success_count, error_messages)
        """
        success_count = 0
        errors = []
        total = len(relationships)

        for i in range(0, total, batch_size):
            batch = relationships[i : i + batch_size]

            # Create relationships individually (APOC might not be available)
            for source_id, target_id, rel_type, props in batch:
                result = await self.create_relationship(source_id, target_id, rel_type, props)
                if result.success:
                    success_count += 1
                else:
                    errors.append(result.error or "Unknown error")

            if progress_callback:
                progress_callback(min(i + batch_size, total), total)

        return success_count, errors

    async def get_node(self, node_id: str) -> dict[str, Any] | None:
        """Get a node by its ID.

        Args:
            node_id: Node identifier

        Returns:
            Node properties or None if not found
        """
        query = """
        MATCH (n {node_id: $node_id})
        RETURN n
        """

        result = await self.execute_query(query, {"node_id": node_id})

        if result.success and result.records:
            node = result.records[0].get("n")
            return dict(node) if node else None

        return None

    async def get_node_count(self, label: str | None = None) -> int:
        """Get the count of nodes, optionally filtered by label.

        Args:
            label: Optional node label to filter by

        Returns:
            Number of nodes
        """
        if label:
            query = f"MATCH (n:{label}) RETURN count(n) AS count"
        else:
            query = "MATCH (n) RETURN count(n) AS count"

        result = await self.execute_query(query)

        if result.success and result.records:
            return result.records[0].get("count", 0)

        return 0

    async def get_relationship_count(self, rel_type: str | None = None) -> int:
        """Get the count of relationships, optionally filtered by type.

        Args:
            rel_type: Optional relationship type to filter by

        Returns:
            Number of relationships
        """
        if rel_type:
            query = f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS count"
        else:
            query = "MATCH ()-[r]->() RETURN count(r) AS count"

        result = await self.execute_query(query)

        if result.success and result.records:
            return result.records[0].get("count", 0)

        return 0

    async def clear_all(self) -> bool:
        """Clear all nodes and relationships from the database.

        WARNING: This is destructive!

        Returns:
            True if successful
        """
        query = "MATCH (n) DETACH DELETE n"
        result = await self.execute_query(query)
        return result.success

    async def health_check(self) -> dict[str, Any]:
        """Check database health and return stats.

        Returns:
            Dictionary with health status and statistics
        """
        try:
            node_count = await self.get_node_count()
            rel_count = await self.get_relationship_count()

            return {
                "connected": self._connected,
                "healthy": True,
                "node_count": node_count,
                "relationship_count": rel_count,
                "database": self.config.database,
            }
        except Exception as e:
            return {
                "connected": False,
                "healthy": False,
                "error": str(e),
            }


# Import uuid at module level
import uuid
