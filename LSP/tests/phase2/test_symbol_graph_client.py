"""Tests for SymbolGraphClient - LSP-focused Neo4j interface."""

import pytest

from novelwriter_lsp.storage.symbol_graph_client import SymbolGraphClient
from novelwriter_lsp.storage.neo4j_client import Neo4jConfig
from novelwriter_lsp.types import BaseSymbol, SymbolType


def create_test_symbol(
    symbol_id: str = "test-123",
    name: str = "Test Character",
    symbol_type: SymbolType = SymbolType.CHARACTER,
) -> BaseSymbol:
    """Helper to create a test symbol."""
    return BaseSymbol(
        id=symbol_id,
        type=symbol_type,
        name=name,
        novel_id="novel-456",
        definition_uri="file:///test.md",
        definition_range={
            "start_line": 10,
            "end_line": 15,
            "start_character": 0,
            "end_character": 20,
        },
        references=[{"uri": "file:///test.md", "line": 20, "character": 5}],
        metadata={"age": 42},
    )


class TestSymbolGraphClient:
    """Test suite for SymbolGraphClient."""

    def test_initialization(self):
        """Test that SymbolGraphClient initializes correctly."""
        config = Neo4jConfig(uri="bolt://test:7687")
        client = SymbolGraphClient(config)

        assert client.client is not None
        assert client.client.config.uri == "bolt://test:7687"

    def test_default_initialization(self):
        """Test initialization with default config."""
        client = SymbolGraphClient()

        assert client.client is not None
        assert client.client.config.uri == "bolt://localhost:7687"

    def test_symbol_to_properties(self):
        """Test converting a symbol to Neo4j properties."""
        client = SymbolGraphClient()
        symbol = create_test_symbol()

        props = client._symbol_to_properties(symbol)

        assert props["id"] == symbol.id
        assert props["name"] == symbol.name
        assert props["type"] == "character"
        assert "updated_at" in props

    def test_properties_to_symbol(self):
        client = SymbolGraphClient()
        symbol = create_test_symbol()
        props = client._symbol_to_properties(symbol)

        props["node_id"] = "neo-123"
        props["created_at"] = "2024-01-01T00:00:00"

        reconstructed = client._properties_to_symbol(props)

        assert reconstructed.id == symbol.id
        assert reconstructed.name == symbol.name
        assert reconstructed.type == SymbolType.CHARACTER
        assert reconstructed.novel_id == symbol.novel_id

    def test_properties_to_symbol_string_type(self):
        """Test converting string type back to enum."""
        client = SymbolGraphClient()
        props = {
            "id": "test-123",
            "type": "location",
            "name": "Test Location",
            "novel_id": "novel-456",
            "definition_uri": "file:///test.md",
            "definition_range": {
                "start_line": 10,
                "end_line": 15,
                "start_character": 0,
                "end_character": 20,
            },
            "references": [],
            "metadata": {},
        }

        reconstructed = client._properties_to_symbol(props)

        assert reconstructed.type == SymbolType.LOCATION

    @pytest.mark.asyncio
    async def test_client_not_connected(self):
        client = SymbolGraphClient()
        symbol = create_test_symbol()

        result = await client.index_symbol(symbol)
        assert not result.success

        fetched = await client.get_symbol_by_id("test-123")
        assert fetched is None

        found = await client.find_symbol_by_name("Test")
        assert found == []

        refs = await client.get_references("test-123")
        assert refs == []

        deleted = await client.delete_symbol("test-123")
        assert not deleted
