"""Tests for the hover feature handler."""

import pytest
from lsprotocol import types
from pygls.lsp.server import LanguageServer

from novelwriter_lsp.features.hover import (
    register_hover,
    _extract_word,
    _build_hover_content,
)
from novelwriter_lsp.index import SymbolIndex
from novelwriter_lsp.types import (
    CharacterSymbol,
    LocationSymbol,
    ItemSymbol,
    LoreSymbol,
    PlotPointSymbol,
    ChapterSymbol,
)


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

    def test_extract_word_with_underscores(self) -> None:
        """Test extracting word with underscores."""
        line = "John_Doe"
        result = _extract_word(line, 5)
        assert result == "John_Doe"

    def test_extract_word_in_text(self) -> None:
        """Test extracting word in middle of text."""
        line = "John walked into the room"
        result = _extract_word(line, 15)
        assert result == "into"


class TestBuildHoverContent:
    """Test hover content generation for different symbol types."""

    def test_build_character_content(self) -> None:
        """Test building hover content for a character."""
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
            age=42,
            status="alive",
            occupation="Detective",
            description="A rugged detective with a mysterious past.",
            personality=["grumpy", "loyal", "sharp"],
        )

        content = _build_hover_content(symbol)

        assert "**Character**: John Doe" in content
        assert "**Age**: 42" in content
        assert "**Status**: alive" in content
        assert "**Occupation**: Detective" in content
        assert "**Description**:" in content
        assert "**Traits**: grumpy, loyal, sharp" in content

    def test_build_location_content(self) -> None:
        """Test building hover content for a location."""
        symbol = LocationSymbol(
            id="loc_pub_1",
            name="The Rusty Anchor",
            novel_id="novel_1",
            definition_uri="file:///test.md",
            definition_range={
                "start_line": 10,
                "end_line": 10,
                "start_character": 0,
                "end_character": 15,
            },
            location_type="pub",
            region="Boston",
            climate="temperate",
            description="A dimly lit pub with sawdust on the floor.",
            significance="Where John meets his informants.",
        )

        content = _build_hover_content(symbol)

        assert "**Location**: The Rusty Anchor" in content
        assert "**Type**: pub" in content
        assert "**Region**: Boston" in content
        assert "**Climate**: temperate" in content

    def test_build_item_content(self) -> None:
        """Test building hover content for an item."""
        symbol = ItemSymbol(
            id="item_key_1",
            name="Brass Key",
            novel_id="novel_1",
            definition_uri="file:///test.md",
            definition_range={
                "start_line": 15,
                "end_line": 15,
                "start_character": 0,
                "end_character": 10,
            },
            item_type="artifact",
            owner="John Doe",
            description="An old brass key with intricate engravings.",
            abilities=["opens safe deposit box"],
        )

        content = _build_hover_content(symbol)

        assert "**Item**: Brass Key" in content
        assert "**Type**: artifact" in content
        assert "**Owner**: John Doe" in content

    def test_build_lore_content(self) -> None:
        """Test building hover content for lore."""
        symbol = LoreSymbol(
            id="lore_magic_1",
            name="The Old Magic",
            novel_id="novel_1",
            definition_uri="file:///test.md",
            definition_range={
                "start_line": 20,
                "end_line": 20,
                "start_character": 0,
                "end_character": 13,
            },
            lore_type="magic system",
            category="World Building",
            description="An ancient form of magic lost to time.",
            rules=["Requires blood sacrifice", "Only works at midnight"],
        )

        content = _build_hover_content(symbol)

        assert "**Lore**: The Old Magic" in content
        assert "**Type**: magic system" in content
        assert "**Category**: World Building" in content

    def test_build_plotpoint_content(self) -> None:
        """Test building hover content for a plot point."""
        symbol = PlotPointSymbol(
            id="plot_murder_1",
            name="The Murder",
            novel_id="novel_1",
            definition_uri="file:///test.md",
            definition_range={
                "start_line": 25,
                "end_line": 25,
                "start_character": 0,
                "end_character": 10,
            },
            plot_type="inciting incident",
            chapter=3,
            volume=1,
            description="The body is discovered in the library.",
            involved_characters=["John Doe", "Victim"],
        )

        content = _build_hover_content(symbol)

        assert "**Plotpoint**: The Murder" in content
        assert "**Type**: inciting incident" in content
        assert "**Chapter**: 3" in content
        assert "**Volume**: 1" in content

    def test_build_chapter_content(self) -> None:
        """Test building hover content for a chapter."""
        symbol = ChapterSymbol(
            id="chap_1",
            name="Chapter 1",
            novel_id="novel_1",
            definition_uri="file:///test.md",
            definition_range={
                "start_line": 30,
                "end_line": 30,
                "start_character": 0,
                "end_character": 10,
            },
            chapter_number=1,
            volume_number=1,
            title="The Beginning",
            word_count=2500,
            status="draft",
            summary="John arrives in town and meets his first suspect.",
        )

        content = _build_hover_content(symbol)

        assert "**Chapter**: Chapter 1" in content
        assert "**Number**: 1" in content
        assert "**Volume**: 1" in content
        assert "**Title**: The Beginning" in content
        assert "**Words**: 2,500" in content
        assert "**Status**: draft" in content

    def test_build_content_with_metadata(self) -> None:
        """Test building hover content with metadata."""
        symbol = CharacterSymbol(
            id="char_jane_1",
            name="Jane Smith",
            novel_id="novel_1",
            definition_uri="file:///test.md",
            definition_range={
                "start_line": 35,
                "end_line": 35,
                "start_character": 0,
                "end_character": 10,
            },
            metadata={
                "alias": "The Informant",
                "first_appearance": "Chapter 2",
            },
        )

        content = _build_hover_content(symbol)

        assert "---" in content
        assert "**alias**: The Informant" in content
        assert "**first_appearance**: Chapter 2" in content


class TestHover:
    """Test hover handler."""

    @pytest.fixture
    def index(self) -> SymbolIndex:
        """Create a test index with sample data."""
        idx = SymbolIndex()
        idx.update(
            CharacterSymbol(
                id="char_john_1",
                name="JohnDoe",
                novel_id="novel_1",
                definition_uri="file:///test.md",
                definition_range={
                    "start_line": 5,
                    "end_line": 5,
                    "start_character": 0,
                    "end_character": 7,
                },
                age=42,
                status="alive",
            )
        )
        return idx

    @pytest.fixture
    def server(self) -> LanguageServer:
        """Create a test server instance."""
        return LanguageServer(name="Test", version="0.1.0")

    def test_register_handler(self, server: LanguageServer, index: SymbolIndex) -> None:
        """Test that handler registration doesn't raise."""
        register_hover(server, index)

    def test_hover_symbol_not_in_index(self, server: LanguageServer, index: SymbolIndex) -> None:
        """Test hover when symbol is not in index."""
        register_hover(server, index)

        symbol = index.get_symbol("Nonexistent")
        assert symbol is None
