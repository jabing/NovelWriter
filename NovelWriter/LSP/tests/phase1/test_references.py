"""Tests for the find_references feature handler."""

import pytest
from lsprotocol import types
from pygls.lsp.server import LanguageServer

from novelwriter_lsp.features.references import register_find_references, _extract_word
from novelwriter_lsp.index import SymbolIndex
from novelwriter_lsp.types import CharacterSymbol


class TestReferencesHelpers:
    """Test helper functions in references module."""
    
    def test_extract_word_basic(self) -> None:
        """Test basic word extraction."""
        line = "John"
        result = _extract_word(line, 2)
        assert result == "John"


class TestFindReferences:
    """Test find_references handler."""
    
    @pytest.fixture
    def index_with_references(self) -> SymbolIndex:
        """Create index with symbol that has references."""
        idx = SymbolIndex()
        
        symbol = CharacterSymbol(
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
            references=[
                {
                    "uri": "file:///test.md",
                    "start_line": 10,
                    "end_line": 10,
                    "start_character": 5,
                    "end_character": 13,
                },
                {
                    "uri": "file:///test.md",
                    "start_line": 15,
                    "end_line": 15,
                    "start_character": 0,
                    "end_character": 8,
                },
            ],
        )
        
        idx.update(symbol)
        return idx
    
    @pytest.fixture
    def server(self) -> LanguageServer:
        """Create test server."""
        from pygls.lsp.server import LanguageServer
        return LanguageServer(name="Test", version="0.1.0")
    
    def test_register_handler(self, server: LanguageServer, index_with_references: SymbolIndex) -> None:
        """Test handler registration doesn't raise."""
        register_find_references(server, index_with_references)
    
    def test_symbol_with_references(self, index_with_references: SymbolIndex) -> None:
        """Test symbol has references."""
        symbol = index_with_references.get_symbol("John Doe")
        assert symbol is not None
        assert len(symbol.references) == 2
