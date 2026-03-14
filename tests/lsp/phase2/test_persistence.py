"""Tests for SymbolIndex database persistence functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from novelwriter_lsp.index import SymbolIndex
from novelwriter_lsp.storage.symbol_graph_client import SymbolGraphClient
from novelwriter_lsp.storage.postgres_client import PostgresClient
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


class TestSymbolIndexPersistence:
    """Test suite for SymbolIndex database persistence."""

    def test_initialization_without_clients(self):
        """Test SymbolIndex initializes correctly without database clients."""
        index = SymbolIndex(max_size=100)
        assert index.max_size == 100
        assert index._neo4j_client is None
        assert index._postgres_client is None

    def test_initialization_with_clients(self):
        """Test SymbolIndex initializes correctly with database clients."""
        mock_neo4j = MagicMock(spec=SymbolGraphClient)
        mock_postgres = MagicMock(spec=PostgresClient)
        index = SymbolIndex(
            max_size=100,
            neo4j_client=mock_neo4j,
            postgres_client=mock_postgres,
        )
        assert index._neo4j_client is mock_neo4j
        assert index._postgres_client is mock_postgres

    @pytest.mark.asyncio
    async def test_persist_to_db_single_symbol_neo4j(self):
        """Test persisting a single symbol to Neo4j."""
        mock_neo4j = MagicMock(spec=SymbolGraphClient)
        mock_neo4j.index_symbol = AsyncMock()
        index = SymbolIndex(neo4j_client=mock_neo4j)
        symbol = create_test_symbol()
        index.update(symbol)

        await index.persist_to_db(symbol.id)

        mock_neo4j.index_symbol.assert_called_once_with(symbol)

    @pytest.mark.asyncio
    async def test_persist_to_db_single_symbol_postgres(self):
        """Test persisting a single symbol to PostgreSQL."""
        mock_postgres = MagicMock(spec=PostgresClient)
        mock_postgres.save_symbol = AsyncMock()
        index = SymbolIndex(postgres_client=mock_postgres)
        symbol = create_test_symbol()
        index.update(symbol)

        await index.persist_to_db(symbol.id)

        mock_postgres.save_symbol.assert_called_once_with(symbol)

    @pytest.mark.asyncio
    async def test_persist_to_db_all_symbols(self):
        """Test persisting all symbols to both databases."""
        mock_neo4j = MagicMock(spec=SymbolGraphClient)
        mock_neo4j.index_symbol = AsyncMock()
        mock_postgres = MagicMock(spec=PostgresClient)
        mock_postgres.save_symbol = AsyncMock()
        index = SymbolIndex(
            neo4j_client=mock_neo4j,
            postgres_client=mock_postgres,
        )
        symbol1 = create_test_symbol(symbol_id="test-1", name="Symbol 1")
        symbol2 = create_test_symbol(symbol_id="test-2", name="Symbol 2")
        index.update(symbol1)
        index.update(symbol2)

        await index.persist_to_db()

        assert mock_neo4j.index_symbol.call_count == 2
        assert mock_postgres.save_symbol.call_count == 2

    @pytest.mark.asyncio
    async def test_load_from_db_single_symbol_neo4j(self):
        """Test loading a single symbol from Neo4j."""
        mock_neo4j = MagicMock(spec=SymbolGraphClient)
        symbol = create_test_symbol()
        mock_neo4j.get_symbol_by_id = AsyncMock(return_value=symbol)
        index = SymbolIndex(neo4j_client=mock_neo4j)

        await index.load_from_db(symbol.id)

        mock_neo4j.get_symbol_by_id.assert_called_once_with(symbol.id)
        assert index.get_symbol(symbol.name) == symbol

    @pytest.mark.asyncio
    async def test_load_from_db_single_symbol_postgres(self):
        """Test loading a single symbol from PostgreSQL."""
        from novelwriter_lsp.storage.postgres_client import SymbolResult

        mock_postgres = MagicMock(spec=PostgresClient)
        symbol = create_test_symbol()
        mock_postgres.load_symbol_by_id = AsyncMock(
            return_value=SymbolResult(success=True, symbol=symbol)
        )
        index = SymbolIndex(postgres_client=mock_postgres)

        await index.load_from_db(symbol.id)

        mock_postgres.load_symbol_by_id.assert_called_once_with(symbol.id)
        assert index.get_symbol(symbol.name) == symbol

    @pytest.mark.asyncio
    async def test_load_from_db_all_symbols_neo4j(self):
        """Test loading all symbols from Neo4j."""
        mock_neo4j = MagicMock(spec=SymbolGraphClient)
        symbol1 = create_test_symbol(symbol_id="test-1", name="Symbol 1")
        symbol2 = create_test_symbol(symbol_id="test-2", name="Symbol 2")
        mock_neo4j.get_all_symbols = AsyncMock(return_value=[symbol1, symbol2])
        index = SymbolIndex(neo4j_client=mock_neo4j)

        await index.load_from_db()

        mock_neo4j.get_all_symbols.assert_called_once()
        assert index.get_symbol(symbol1.name) == symbol1
        assert index.get_symbol(symbol2.name) == symbol2

    def test_update_without_clients_does_not_persist(self):
        """Test that update doesn't persist when no clients are configured."""
        index = SymbolIndex()
        symbol = create_test_symbol()
        # Just ensure no errors
        index.update(symbol)
        assert index.get_symbol(symbol.name) == symbol
