"""Tests for the document parser module."""

import pytest

from novelwriter_lsp.parser import parse_document, _parse_metadata, _generate_symbol_id
from novelwriter_lsp.types import (
    SymbolType,
    OutlineLevel,
    CharacterSymbol,
    LocationSymbol,
    ItemSymbol,
    LoreSymbol,
    PlotPointSymbol,
    OutlineSymbol,
    EventSymbol,
    RelationshipSymbol,
    ChapterSymbol,
)


class TestParseMetadata:
    """Test metadata parsing from {key: value} format."""

    def test_parse_metadata_empty(self) -> None:
        """Test parsing empty metadata."""
        result = _parse_metadata(None)
        assert result == {}

        result = _parse_metadata("")
        assert result == {}

    def test_parse_metadata_single_key_value(self) -> None:
        """Test parsing single key-value pair."""
        result = _parse_metadata("{ age: 42 }")
        assert result == {"age": "42", "aliases": []}

    def test_parse_metadata_multiple_key_values(self) -> None:
        """Test parsing multiple key-value pairs."""
        result = _parse_metadata("{ age: 42, status: alive }")
        assert result == {"age": "42", "status": "alive", "aliases": []}

    def test_parse_metadata_with_quoted_values(self) -> None:
        """Test parsing metadata with quoted string values."""
        result = _parse_metadata('{ description: "A rugged detective" }')
        assert result == {"description": "A rugged detective", "aliases": []}

    def test_parse_metadata_with_single_quotes(self) -> None:
        """Test parsing metadata with single-quoted values."""
        result = _parse_metadata("{ description: 'A rugged detective' }")
        assert result == {"description": "A rugged detective", "aliases": []}

    def test_parse_metadata_complex(self) -> None:
        """Test parsing complex metadata with multiple fields."""
        result = _parse_metadata('{ age: 42, status: "alive", occupation: detective }')
        assert result == {"age": "42", "status": "alive", "occupation": "detective", "aliases": []}


class TestGenerateSymbolId:
    """Test symbol ID generation."""

    def test_generate_symbol_id_basic(self) -> None:
        """Test basic ID generation."""
        result = _generate_symbol_id(SymbolType.CHARACTER, "John Doe", 5)
        assert result == "character_john_doe_5"

    def test_generate_symbol_id_with_spaces(self) -> None:
        """Test ID generation converts spaces to underscores."""
        result = _generate_symbol_id(SymbolType.LOCATION, "The Rusty Anchor", 10)
        assert result == "location_the_rusty_anchor_10"

    def test_generate_symbol_id_different_types(self) -> None:
        """Test ID generation for different symbol types."""
        result = _generate_symbol_id(SymbolType.ITEM, "Sword", 3)
        assert result == "item_sword_3"

        result = _generate_symbol_id(SymbolType.LORE, "Magic System", 15)
        assert result == "lore_magic_system_15"


class TestCharacterSymbol:
    """Test parsing of Character symbols."""

    def test_parse_character_simple(self) -> None:
        """Test parsing a simple character definition."""
        content = "@Character: John Doe"
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 1
        symbol = symbols[0]
        assert isinstance(symbol, CharacterSymbol)
        assert symbol.name == "John Doe"
        assert symbol.type == SymbolType.CHARACTER

    def test_parse_character_with_metadata(self) -> None:
        """Test parsing character with metadata."""
        content = '@Character: Jane Smith { age: 30, status: "alive", occupation: "writer" }'
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 1
        symbol = symbols[0]
        assert isinstance(symbol, CharacterSymbol)
        assert symbol.name == "Jane Smith"
        assert symbol.age == 30
        assert symbol.status == "alive"
        assert symbol.occupation == "writer"

    def test_parse_character_multiple_lines(self) -> None:
        """Test parsing multiple characters on different lines."""
        content = """@Character: John Doe
@Character: Jane Smith { age: 25 }"""
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 2
        assert symbols[0].name == "John Doe"
        assert symbols[1].name == "Jane Smith"
        assert isinstance(symbols[1], CharacterSymbol)
        assert symbols[1].age == 25


class TestLocationSymbol:
    """Test parsing of Location symbols."""

    def test_parse_location_simple(self) -> None:
        """Test parsing a simple location definition."""
        content = "@Location: The Rusty Anchor Pub"
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 1
        symbol = symbols[0]
        assert isinstance(symbol, LocationSymbol)
        assert symbol.name == "The Rusty Anchor Pub"
        assert symbol.type == SymbolType.LOCATION

    def test_parse_location_with_metadata(self) -> None:
        """Test parsing location with metadata."""
        content = '@Location: Boston Harbor { location_type: "harbor", region: "Massachusetts" }'
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 1
        symbol = symbols[0]
        assert isinstance(symbol, LocationSymbol)
        assert symbol.name == "Boston Harbor"
        assert symbol.location_type == "harbor"
        assert symbol.region == "Massachusetts"


class TestItemSymbol:
    """Test parsing of Item symbols."""

    def test_parse_item_simple(self) -> None:
        """Test parsing a simple item definition."""
        content = "@Item: Golden Sword"
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 1
        symbol = symbols[0]
        assert isinstance(symbol, ItemSymbol)
        assert symbol.name == "Golden Sword"
        assert symbol.type == SymbolType.ITEM

    def test_parse_item_with_metadata(self) -> None:
        """Test parsing item with metadata."""
        content = '@Item: Magic Ring { item_type: "artifact", owner: "John Doe" }'
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 1
        symbol = symbols[0]
        assert isinstance(symbol, ItemSymbol)
        assert symbol.name == "Magic Ring"
        assert symbol.item_type == "artifact"
        assert symbol.owner == "John Doe"


class TestLoreSymbol:
    """Test parsing of Lore symbols."""

    def test_parse_lore_simple(self) -> None:
        """Test parsing a simple lore definition."""
        content = "@Lore: The Great War"
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 1
        symbol = symbols[0]
        assert isinstance(symbol, LoreSymbol)
        assert symbol.name == "The Great War"
        assert symbol.type == SymbolType.LORE

    def test_parse_lore_with_metadata(self) -> None:
        """Test parsing lore with metadata."""
        content = '@Lore: Magic System { lore_type: "magic", category: "supernatural" }'
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 1
        symbol = symbols[0]
        assert isinstance(symbol, LoreSymbol)
        assert symbol.name == "Magic System"
        assert symbol.lore_type == "magic"
        assert symbol.category == "supernatural"


class TestPlotPointSymbol:
    """Test parsing of PlotPoint symbols."""

    def test_parse_plotpoint_simple(self) -> None:
        """Test parsing a simple plot point definition."""
        content = "@PlotPoint: The Discovery"
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 1
        symbol = symbols[0]
        assert isinstance(symbol, PlotPointSymbol)
        assert symbol.name == "The Discovery"
        assert symbol.type == SymbolType.PLOTPOINT

    def test_parse_plotpoint_with_metadata(self) -> None:
        """Test parsing plot point with metadata."""
        content = '@PlotPoint: Inciting Incident { plot_type: "inciting_incident" }'
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 1
        symbol = symbols[0]
        assert isinstance(symbol, PlotPointSymbol)
        assert symbol.name == "Inciting Incident"
        assert symbol.plot_type == "inciting_incident"


class TestOutlineSymbol:
    """Test parsing of Outline symbols."""

    def test_parse_outline_simple(self) -> None:
        """Test parsing a simple outline definition."""
        content = "@Outline: Master Plan"
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 1
        symbol = symbols[0]
        assert isinstance(symbol, OutlineSymbol)
        assert symbol.name == "Master Plan"
        assert symbol.type == SymbolType.OUTLINE
        assert symbol.level == OutlineLevel.MASTER

    def test_parse_outline_with_level(self) -> None:
        """Test parsing outline with level metadata."""
        content = '@Outline: Volume 1 Arc { level: "volume", volume_number: 1 }'
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 1
        symbol = symbols[0]
        assert isinstance(symbol, OutlineSymbol)
        assert symbol.name == "Volume 1 Arc"
        assert symbol.level == OutlineLevel.VOLUME
        assert symbol.volume_number == 1

    def test_parse_outline_chapter_level(self) -> None:
        """Test parsing chapter-level outline."""
        content = '@Outline: Chapter 3 Setup { level: "chapter", chapter_number: 3 }'
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 1
        symbol = symbols[0]
        assert isinstance(symbol, OutlineSymbol)
        assert symbol.name == "Chapter 3 Setup"
        assert symbol.level == OutlineLevel.CHAPTER
        assert symbol.chapter_number == 3


class TestEventSymbol:
    """Test parsing of Event symbols."""

    def test_parse_event_simple(self) -> None:
        """Test parsing a simple event definition."""
        content = "@Event: The First Meeting"
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 1
        symbol = symbols[0]
        assert isinstance(symbol, EventSymbol)
        assert symbol.name == "The First Meeting"
        assert symbol.type == SymbolType.EVENT

    def test_parse_event_with_metadata(self) -> None:
        """Test parsing event with metadata."""
        content = (
            '@Event: Battle Scene { chapter: 5, location: "The Arena", importance: "critical" }'
        )
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 1
        symbol = symbols[0]
        assert isinstance(symbol, EventSymbol)
        assert symbol.name == "Battle Scene"
        assert symbol.chapter == 5
        assert symbol.location == "The Arena"
        assert symbol.importance == "critical"


class TestRelationshipSymbol:
    """Test parsing of Relationship symbols."""

    def test_parse_relationship_simple(self) -> None:
        """Test parsing a simple relationship definition."""
        content = "@Relationship: John and Jane"
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 1
        symbol = symbols[0]
        assert isinstance(symbol, RelationshipSymbol)
        assert symbol.name == "John and Jane"
        assert symbol.type == SymbolType.RELATIONSHIP

    def test_parse_relationship_with_metadata(self) -> None:
        """Test parsing relationship with metadata."""
        content = '@Relationship: Rivals { from_character: "John", to_character: "Mike", relation_type: "enemies" }'
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 1
        symbol = symbols[0]
        assert isinstance(symbol, RelationshipSymbol)
        assert symbol.name == "Rivals"
        assert symbol.from_character == "John"
        assert symbol.to_character == "Mike"
        assert symbol.relation_type == "enemies"


class TestChapterSymbol:
    """Test parsing of Chapter symbols."""

    def test_parse_chapter_simple(self) -> None:
        """Test parsing a simple chapter heading."""
        content = "# Chapter 1"
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 1
        symbol = symbols[0]
        assert isinstance(symbol, ChapterSymbol)
        assert symbol.name == "Chapter 1"
        assert symbol.type == SymbolType.CHAPTER
        assert symbol.title == "Chapter 1"

    def test_parse_chapter_with_title(self) -> None:
        """Test parsing chapter with custom title."""
        content = "# The Beginning"
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 1
        symbol = symbols[0]
        assert isinstance(symbol, ChapterSymbol)
        assert symbol.name == "The Beginning"
        assert symbol.title == "The Beginning"


class TestParseDocument:
    """Test the main parse_document function."""

    def test_parse_document_empty(self) -> None:
        """Test parsing empty document."""
        symbols = parse_document("", "file:///test.md")
        assert len(symbols) == 0

    def test_parse_document_no_symbols(self) -> None:
        """Test parsing document with no symbol definitions."""
        content = "Just some regular text\nNo symbols here"
        symbols = parse_document(content, "file:///test.md")
        assert len(symbols) == 0

    def test_parse_document_mixed_symbols(self) -> None:
        """Test parsing document with multiple symbol types."""
        content = """# Chapter 1

@Character: John Doe { age: 42 }
@Location: The Rusty Anchor Pub
@Item: Golden Sword { item_type: "weapon" }

John Doe entered The Rusty Anchor Pub.
"""
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 4
        symbol_types = [s.type for s in symbols]
        assert SymbolType.CHAPTER in symbol_types
        assert SymbolType.CHARACTER in symbol_types
        assert SymbolType.LOCATION in symbol_types
        assert SymbolType.ITEM in symbol_types

    def test_parse_document_line_numbers(self) -> None:
        """Test that line numbers are correctly tracked."""
        content = """Line 1
@Character: John Doe
Line 3
@Location: The Pub"""
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 2
        assert symbols[0].definition_range["start_line"] == 1
        assert symbols[1].definition_range["start_line"] == 3

    def test_parse_document_uri_tracking(self) -> None:
        """Test that document URI is correctly tracked."""
        content = "@Character: John Doe"
        symbols = parse_document(content, "file:///path/to/document.md")

        assert len(symbols) == 1
        assert symbols[0].definition_uri == "file:///path/to/document.md"

    def test_parse_document_all_symbol_types(self) -> None:
        """Test parsing all 9 symbol types in one document."""
        content = """@Character: John Doe
@Location: Boston
@Item: Sword
@Lore: Magic Rules
@PlotPoint: The Twist
@Outline: Story Arc
@Event: The Battle
@Relationship: Love Triangle
# Chapter 1
"""
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 9
        symbol_types = {s.type for s in symbols}
        assert len(symbol_types) == 9
        assert SymbolType.CHARACTER in symbol_types
        assert SymbolType.LOCATION in symbol_types
        assert SymbolType.ITEM in symbol_types
        assert SymbolType.LORE in symbol_types
        assert SymbolType.PLOTPOINT in symbol_types
        assert SymbolType.OUTLINE in symbol_types
        assert SymbolType.EVENT in symbol_types
        assert SymbolType.RELATIONSHIP in symbol_types
        assert SymbolType.CHAPTER in symbol_types

    def test_parse_document_character_attributes(self) -> None:
        """Test parsing character with all supported attributes."""
        content = '@Character: Jane Doe { age: 35, status: "alive", occupation: "detective", description: "Sharp and witty" }'
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 1
        symbol = symbols[0]
        assert isinstance(symbol, CharacterSymbol)
        assert symbol.age == 35
        assert symbol.status == "alive"
        assert symbol.occupation == "detective"
        assert symbol.description == "Sharp and witty"

    def test_parse_document_multiple_chapters(self) -> None:
        """Test parsing multiple chapter headings."""
        content = """# Chapter 1
Some content here.
# Chapter 2
More content.
# Chapter 3"""
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 3
        assert all(isinstance(s, ChapterSymbol) for s in symbols)
        assert symbols[0].name == "Chapter 1"
        assert symbols[1].name == "Chapter 2"
        assert symbols[2].name == "Chapter 3"

    def test_parse_document_symbol_id_generation(self) -> None:
        """Test that symbol IDs are correctly generated."""
        content = "@Character: John Doe"
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 1
        assert symbols[0].id == "character_john_doe_0"

    def test_parse_document_definition_range(self) -> None:
        """Test that definition ranges are correctly set."""
        content = "@Character: John Doe"
        symbols = parse_document(content, "file:///test.md")

        assert len(symbols) == 1
        symbol = symbols[0]
        assert "start_line" in symbol.definition_range
        assert "end_line" in symbol.definition_range
        assert "start_character" in symbol.definition_range
        assert "end_character" in symbol.definition_range
        assert symbol.definition_range["start_line"] == symbol.definition_range["end_line"]
