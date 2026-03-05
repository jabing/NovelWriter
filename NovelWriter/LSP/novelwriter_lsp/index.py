"""
NovelWriter LSP - Symbol Index with LRU Cache

This module provides an in-memory index for storing and querying symbols
with LRU (Least Recently Used) cache eviction support.
"""

from collections import OrderedDict
from typing import Any

from novelwriter_lsp.types import BaseSymbol, SymbolType


class SymbolIndex:
    """
    In-memory symbol index with LRU cache support.
    
    This index stores symbols parsed from documents and provides
    efficient lookup by name, ID, and URI. It uses an OrderedDict
    to implement LRU cache eviction when max_size is reached.
    
    Attributes:
        max_size: Maximum number of symbols to keep in cache
        _cache: OrderedDict for LRU cache (name -> symbol)
        _uri_map: Mapping from URI to list of symbol names
        _id_map: Mapping from symbol ID to symbol name
    """
    
    def __init__(self, max_size: int = 1000) -> None:
        """
        Initialize the symbol index.
        
        Args:
            max_size: Maximum number of symbols in LRU cache (default: 1000)
        """
        self.max_size = max_size
        self._cache: OrderedDict[str, BaseSymbol] = OrderedDict()
        self._uri_map: dict[str, list[str]] = {}
        self._id_map: dict[str, str] = {}
    
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
