"""Basic tests for Neo4j client."""

import pytest
from novelwriter_lsp.storage.neo4j_client import (
    Neo4jClient,
    Neo4jConfig,
    NodeResult,
    RelationshipResult,
    QueryResult,
)


def test_config_defaults():
    """Test that Neo4jConfig has sensible defaults."""
    config = Neo4jConfig()
    assert config.uri == "bolt://localhost:7687"
    assert config.user == "neo4j"
    assert config.password == ""
    assert config.database == "neo4j"


def test_client_initialization():
    """Test that Neo4jClient initializes correctly."""
    config = Neo4jConfig(uri="bolt://test:7687", user="test", password="test")
    client = Neo4jClient(config)
    assert client.config.uri == "bolt://test:7687"
    assert client.config.user == "test"
    assert not client._connected
    assert client._driver is None


def test_node_result():
    """Test NodeResult dataclass."""
    result = NodeResult(success=True, node_id="123", data={"name": "Test"})
    assert result.success
    assert result.node_id == "123"
    assert result.data == {"name": "Test"}
    assert result.error is None


def test_relationship_result():
    """Test RelationshipResult dataclass."""
    result = RelationshipResult(success=True, rel_id="456", data={"type": "KNOWS"})
    assert result.success
    assert result.rel_id == "456"
    assert result.data == {"type": "KNOWS"}
    assert result.error is None


def test_query_result():
    """Test QueryResult dataclass."""
    result = QueryResult(success=True, records=[{"a": 1}, {"b": 2}])
    assert result.success
    assert len(result.records) == 2
    assert result.summary == {}
    assert result.error is None


@pytest.mark.asyncio
async def test_client_not_connected():
    """Test that operations fail when client is not connected."""
    client = Neo4jClient()
    result = await client.execute_query("MATCH (n) RETURN n")
    assert not result.success
    assert result.error is not None and "Not connected" in result.error
