"""Basic tests for Milvus client."""

import pytest
from novelwriter_lsp.storage.milvus_client import (
    MilvusClient,
    MilvusConfig,
    InsertResult,
    SearchResult,
)


def test_config_defaults():
    """Test that MilvusConfig has sensible defaults."""
    config = MilvusConfig()
    assert config.uri == "http://localhost:19530"
    assert config.db_name == "default"
    assert config.collection_name == "novel_events"
    assert config.dimension == 1536


def test_client_initialization():
    """Test that MilvusClient initializes correctly."""
    config = MilvusConfig(uri="http://test:19530", db_name="test_db")
    client = MilvusClient(config)
    assert client.config.uri == "http://test:19530"
    assert client.config.db_name == "test_db"
    assert not client._connected
    assert client._client is None


def test_insert_result():
    """Test InsertResult dataclass."""
    result = InsertResult(success=True, ids=["event-123"])
    assert result.success
    assert result.ids == ["event-123"]
    assert result.error is None


def test_search_result():
    """Test SearchResult dataclass."""
    result = SearchResult(success=True, results=[{"event_id": "123", "score": 0.9}])
    assert result.success
    assert len(result.results) == 1
    assert result.error is None


@pytest.mark.asyncio
async def test_client_not_connected():
    """Test that operations fail when client is not connected."""
    client = MilvusClient()
    insert_result = await client.insert_event("event-123", [0.1] * 1536, {})
    assert not insert_result.success
    assert insert_result.error is not None and "Not connected" in insert_result.error

    search_result = await client.search_events([0.1] * 1536)
    assert not search_result.success
    assert search_result.error is not None and "Not connected" in search_result.error
