"""
NovelWriter LSP - Symbol Index with LRU Cache and Database Persistence

This module provides an in-memory index for storing and querying symbols
with LRU (Least Recently Used) cache eviction support and optional database
persistence.
"""

import logging
from collections import OrderedDict
from typing import Any

from novelwriter_lsp.types import BaseSymbol, SymbolType
from novelwriter_lsp.storage.symbol_graph_client import SymbolGraphClient
from novelwriter_lsp.storage.postgres_client import PostgresClient

logger = logging.getLogger(__name__)


class SymbolIndex:
    """
    In-memory symbol index with LRU cache support and optional database persistence.

    This index stores symbols parsed from documents and provides
    efficient lookup by name, ID, and URI. It uses an OrderedDict
    to implement LRU cache eviction when max_size is reached.

    Attributes:
        max_size: Maximum number of symbols to keep in cache
        _cache: OrderedDict for LRU cache (name -> symbol)
        _uri_map: Mapping from URI to list of symbol names
        _id_map: Mapping from symbol ID to symbol name
        _neo4j_client: Optional SymbolGraphClient for Neo4j persistence
        _postgres_client: Optional PostgresClient for PostgreSQL persistence
    """

    def __init__(
        self,
        max_size: int = 1000,
        neo4j_client: SymbolGraphClient | None = None,
        postgres_client: PostgresClient | None = None,
    ) -> None:
        """
        Initialize the symbol index.

        Args:
            max_size: Maximum number of symbols in LRU cache (default: 1000)
            neo4j_client: Optional SymbolGraphClient for Neo4j persistence
            postgres_client: Optional PostgresClient for PostgreSQL persistence
        """
        self.max_size = max_size
        self._cache: OrderedDict[str, BaseSymbol] = OrderedDict()
        self._uri_map: dict[str, list[str]] = {}
        self._id_map: dict[str, str] = {}
        self._neo4j_client = neo4j_client
        self._postgres_client = postgres_client

    def update(self, symbol: BaseSymbol) -> None:
        """
        Add or update a symbol in the index.

        If the symbol already exists, it will be updated. If adding a new
        symbol would exceed max_size, the least recently used symbol will
        be evicted.

        Args:
            symbol: The symbol to add or update
        """
        name = symbol.name
        symbol_id = symbol.id
        uri = symbol.definition_uri

        if name not in self._cache and len(self._cache) >= self.max_size:
            self._evict_oldest()

        if name in self._cache:
            self._cache.move_to_end(name)

        self._cache[name] = symbol

        if uri not in self._uri_map:
            self._uri_map[uri] = []
        if name not in self._uri_map[uri]:
            self._uri_map[uri].append(name)

        self._id_map[symbol_id] = name

        # Auto-persist to database if configured
        if self._neo4j_client or self._postgres_client:
            import asyncio

            try:
                # Check if we're in an event loop
                loop = asyncio.get_running_loop()
                # If we are, create a task
                _ = loop.create_task(self.persist_to_db(symbol_id))
            except RuntimeError:
                # If no event loop, skip auto-persist (not ideal, but for compatibility)
                logger.warning("No running event loop, skipping auto-persist to database")

    def _evict_oldest(self) -> None:
        """
        Evict the least recently used symbol from the cache.

        This removes the oldest item from the OrderedDict and cleans up
        the associated maps.
        """
        if not self._cache:
            return

        oldest_name, oldest_symbol = self._cache.popitem(last=False)
        uri = oldest_symbol.definition_uri

        if uri in self._uri_map:
            if oldest_name in self._uri_map[uri]:
                self._uri_map[uri].remove(oldest_name)
            if not self._uri_map[uri]:
                del self._uri_map[uri]

        if oldest_symbol.id in self._id_map:
            del self._id_map[oldest_symbol.id]

    def remove(self, uri: str) -> list[BaseSymbol]:
        """
        Remove all symbols associated with a URI.

        This is typically called when a document is closed or deleted.

        Args:
            uri: The URI of the document to remove symbols for

        Returns:
            List of symbols that were removed
        """
        removed_symbols = []
        symbol_names = self._uri_map.pop(uri, [])

        for name in symbol_names:
            if name in self._cache:
                symbol = self._cache.pop(name)
                removed_symbols.append(symbol)
                if symbol.id in self._id_map:
                    del self._id_map[symbol.id]

        return removed_symbols

    def get_symbol(self, name: str) -> BaseSymbol | None:
        """
        Get a symbol by name with LRU cache support.

        If the symbol is found, it will be moved to the end of the cache
        (most recently used) to prevent eviction.

        Args:
            name: The name of the symbol to retrieve

        Returns:
            The symbol if found, None otherwise
        """
        if name not in self._cache:
            return None

        self._cache.move_to_end(name)
        return self._cache[name]

    def get_symbol_by_id(self, symbol_id: str) -> BaseSymbol | None:
        """
        Get a symbol by its ID.

        Args:
            symbol_id: The ID of the symbol to retrieve

        Returns:
            The symbol if found, None otherwise
        """
        name = self._id_map.get(symbol_id)
        if name:
            return self.get_symbol(name)
        return None

    def search(
        self,
        query: str,
        symbol_type: SymbolType | None = None,
        novel_id: str | None = None,
    ) -> list[BaseSymbol]:
        """
        Search for symbols matching criteria.

        Args:
            query: Search query (matches symbol names)
            symbol_type: Optional filter by symbol type
            novel_id: Optional filter by novel ID

        Returns:
            List of matching symbols
        """
        results = []

        for symbol in self._cache.values():
            if query.lower() not in symbol.name.lower():
                continue

            if symbol_type and symbol.type != symbol_type:
                continue

            if novel_id and symbol.novel_id != novel_id:
                continue

            results.append(symbol)

        return results

    def get_symbols_by_uri(self, uri: str) -> list[BaseSymbol]:
        """
        Get all symbols associated with a URI.

        Args:
            uri: The URI to get symbols for

        Returns:
            List of symbols defined in the document
        """
        symbol_names = self._uri_map.get(uri, [])
        symbols = []

        for name in symbol_names:
            symbol = self.get_symbol(name)
            if symbol:
                symbols.append(symbol)

        return symbols

    def find_symbol_at_position(
        self,
        uri: str,
        line: int,
        character: int,
    ) -> BaseSymbol | None:
        """
        Find a symbol defined at a specific position in a document.

        Args:
            uri: The URI of the document
            line: Line number (0-based)
            character: Character position (0-based)

        Returns:
            The symbol if found at the position, None otherwise
        """
        symbol_names = self._uri_map.get(uri, [])

        for name in symbol_names:
            symbol = self.get_symbol(name)
            if symbol:
                def_range = symbol.definition_range
                start_line = def_range.get("start_line", 0)
                end_line = def_range.get("end_line", 0)
                start_char = def_range.get("start_character", 0)
                end_char = def_range.get("end_character", 0)

                if start_line <= line <= end_line:
                    if line == start_line and character < start_char:
                        continue
                    if line == end_line and character > end_char:
                        continue
                    return symbol

        return None

    def get_all_symbols(self) -> list[BaseSymbol]:
        """
        Get all symbols in the index.

        Returns:
            List of all symbols
        """
        return list(self._cache.values())

    def clear(self) -> None:
        """Clear all symbols from the index."""
        self._cache.clear()
        self._uri_map.clear()
        self._id_map.clear()

    def __len__(self) -> int:
        """Return the number of symbols in the index."""
        return len(self._cache)

    def __contains__(self, name: object) -> bool:
        """Check if a symbol name exists in the index."""
        if isinstance(name, str):
            return name in self._cache
        return False

    async def persist_to_db(self, symbol_id: str | None = None) -> None:
        """
        Persist symbols to configured databases.

        Args:
            symbol_id: Optional specific symbol ID to persist. If None, persists all symbols.
        """
        symbols_to_persist = []

        if symbol_id:
            symbol = self.get_symbol_by_id(symbol_id)
            if symbol:
                symbols_to_persist.append(symbol)
        else:
            symbols_to_persist = self.get_all_symbols()

        for symbol in symbols_to_persist:
            if self._neo4j_client:
                try:
                    _ = await self._neo4j_client.index_symbol(symbol)
                except Exception as e:
                    logger.error(f"Failed to persist symbol {symbol.id} to Neo4j: {e}")

            if self._postgres_client:
                try:
                    _ = await self._postgres_client.save_symbol(symbol)
                except Exception as e:
                    logger.error(f"Failed to persist symbol {symbol.id} to PostgreSQL: {e}")

    async def load_from_db(self, symbol_id: str | None = None) -> None:
        """
        Load symbols from configured databases into cache.

        Args:
            symbol_id: Optional specific symbol ID to load. If None, loads all symbols.
        """
        # Prefer PostgreSQL if available, otherwise Neo4j
        symbols_to_load = []

        if symbol_id:
            if self._postgres_client:
                result = await self._postgres_client.load_symbol_by_id(symbol_id)
                if result.success and result.symbol:
                    symbols_to_load.append(result.symbol)
            elif self._neo4j_client:
                symbol = await self._neo4j_client.get_symbol_by_id(symbol_id)
                if symbol:
                    symbols_to_load.append(symbol)
        else:
            if self._postgres_client:
                # Load all symbols from PostgreSQL (we'll need to iterate, but PostgresClient doesn't have get_all yet—use Neo4j's get_all if needed, or load from one source)
                # For now, we'll support Neo4j for bulk load, or we can note that
                pass
            if self._neo4j_client:
                symbols_to_load = await self._neo4j_client.get_all_symbols()

        for symbol in symbols_to_load:
            self.update(symbol)

    def get_cache_info(self) -> dict[str, Any]:
        """
        Get information about the cache state.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "documents": len(self._uri_map),
            "utilization": len(self._cache) / self.max_size if self.max_size > 0 else 0,
        }
