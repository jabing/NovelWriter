"""Tests for the goto_definition feature handler."""

import pytest
from pygls.lsp.server import LanguageServer

from novelwriter_lsp.features.definition import register_goto_definition, _extract_word
from novelwriter_lsp.index import SymbolIndex
from novelwriter_lsp.types import CharacterSymbol


class TestExtractWord:
    """Test word extraction from lines."""
    
    def test_extract_word_simple(self) -> None:
        """Test extracting a simple word."""
        line = "John"
        result = _extract_word(line, 2)
        assert result == "John"
    
    def test_extract_word_at_boundary(self) -> None:
        """Test extracting word when position is at word boundary."""
        line = "John"
        result = _extract_word(line, 0)
        assert result == "John"
    
    def test_extract_word_empty_line(self) -> None:
        """Test extracting word from empty line."""
        result = _extract_word("", 0)
        assert result == ""
    
    def test_extract_word_out_of_bounds(self) -> None:
        """Test extracting word with out of bounds position."""
        line = "John"
        result = _extract_word(line, 10)
        assert result == ""


class TestGotoDefinition:
    """Test goto_definition handler."""
    
    @pytest.fixture
    def index(self) -> SymbolIndex:
        """Create a test index with sample data."""
        idx = SymbolIndex()
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
        """Create a test server instance."""
        return LanguageServer(name="Test", version="0.1.0")
    
    def test_register_handler(self, server: LanguageServer, index: SymbolIndex) -> None:
        """Test that handler registration doesn't raise."""
        register_goto_definition(server, index)
    
    def test_goto_definition_symbol_not_in_index(self, server: LanguageServer, index: SymbolIndex) -> None:
        """Test goto_definition when symbol is not in index."""
        register_goto_definition(server, index)
        
        symbol = index.get_symbol("Nonexistent")
        assert symbol is None
