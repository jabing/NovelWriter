"""Tests for the document_symbol feature handler."""

import pytest
from lsprotocol import types
from pygls.lsp.server import LanguageServer

from novelwriter_lsp.features.symbols import register_document_symbol, SYMBOL_KIND_MAP
from novelwriter_lsp.index import SymbolIndex
from novelwriter_lsp.types import (
    CharacterSymbol,
    ChapterSymbol,
    SymbolType,
)


class TestSymbolKindMap:
    """Test symbol kind mapping."""
    
    def test_character_maps_to_class(self) -> None:
        """Test Character symbol maps to Class."""
        assert SYMBOL_KIND_MAP[SymbolType.CHARACTER] == types.SymbolKind.Class
    
    def test_location_maps_to_struct(self) -> None:
        """Test Location symbol maps to Struct."""
        assert SYMBOL_KIND_MAP[SymbolType.LOCATION] == types.SymbolKind.Struct
    
    def test_chapter_maps_to_module(self) -> None:
        """Test Chapter symbol maps to Module."""
        assert SYMBOL_KIND_MAP[SymbolType.CHAPTER] == types.SymbolKind.Module
    
    def test_event_maps_to_event(self) -> None:
        """Test Event symbol maps to Event."""
        assert SYMBOL_KIND_MAP[SymbolType.EVENT] == types.SymbolKind.Event


class TestDocumentSymbol:
    """Test document_symbol handler."""
    
    @pytest.fixture
    def index_with_chapters(self) -> SymbolIndex:
        """Create index with chapter structure."""
        idx = SymbolIndex()
        
        idx.update(ChapterSymbol(
            id="chap_1",
            name="Chapter 1: The Beginning",
            novel_id="novel_1",
            definition_uri="file:///test.md",
            definition_range={
                "start_line": 0,
                "end_line": 0,
                "start_character": 0,
                "end_character": 30,
            },
            chapter_number=1,
        ))
        
        idx.update(CharacterSymbol(
            id="char_john_1",
            name="John Doe",
            novel_id="novel_1",
            definition_uri="file:///test.md",
            definition_range={
                "start_line": 5,
                "end_line": 5,
                "start_character": 0,
                "end_character": 10,
            },
        ))
        
        return idx
    
    @pytest.fixture
    def server(self) -> LanguageServer:
        """Create test server."""
        from pygls.lsp.server import LanguageServer
        return LanguageServer(name="Test", version="0.1.0")
    
    def test_register_handler(self, server: LanguageServer, index_with_chapters: SymbolIndex) -> None:
        """Test handler registration doesn't raise."""
        register_document_symbol(server, index_with_chapters)
    
    def test_get_symbols_by_uri(self, index_with_chapters: SymbolIndex) -> None:
        """Test retrieving symbols by URI."""
        symbols = index_with_chapters.get_symbols_by_uri("file:///test.md")
        assert len(symbols) == 2
    
    def test_empty_document(self, server: LanguageServer) -> None:
        """Test document_symbol on empty document."""
        idx = SymbolIndex()
        register_document_symbol(server, idx)
