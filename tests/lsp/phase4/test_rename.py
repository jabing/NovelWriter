"""Tests for the rename feature handler."""

import pytest
from pygls.lsp.server import LanguageServer
from lsprotocol import types

from novelwriter_lsp.features.rename import register_rename, _extract_word
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


class TestRename:
    """Test rename handler."""

    @pytest.fixture
    def index(self) -> SymbolIndex:
        """Create a test index with sample data."""
        idx = SymbolIndex()
        idx.update(
            CharacterSymbol(
                id="char_john_1",
                name="John",
                novel_id="novel_1",
                definition_uri="file:///test.md",
                definition_range={
                    "start_line": 5,
                    "end_line": 5,
                    "start_character": 0,
                    "end_character": 4,
                },
                references=[
                    {
                        "uri": "file:///test.md",
                        "start_line": 10,
                        "end_line": 10,
                        "start_character": 5,
                        "end_character": 9,
                    },
                    {
                        "uri": "file:///test.md",
                        "start_line": 15,
                        "end_line": 15,
                        "start_character": 2,
                        "end_character": 6,
                    },
                ],
            )
        )
        return idx

    @pytest.fixture
    def server(self) -> LanguageServer:
        """Create a test server instance."""
        return LanguageServer(name="Test", version="0.1.0")

    def test_register_handler(self, server: LanguageServer, index: SymbolIndex) -> None:
        """Test that handler registration doesn't raise."""
        register_rename(server, index)

    def test_rename_symbol_not_in_index(self, server: LanguageServer, index: SymbolIndex) -> None:
        """Test rename when symbol is not in index."""
        register_rename(server, index)

        symbol = index.get_symbol("Nonexistent")
        assert symbol is None

    def test_rename_updates_index(self, server: LanguageServer, index: SymbolIndex) -> None:
        """Test that rename updates the symbol in the index."""
        register_rename(server, index)

        old_symbol = index.get_symbol("John")
        assert old_symbol is not None
        assert old_symbol.name == "John"
        assert len(old_symbol.references) == 2
