"""Tests for incremental parsing functionality."""

from lsprotocol import types
from typing import Any

from novelwriter_lsp.parser import parse_incremental
from novelwriter_lsp.types import CharacterSymbol


class TestIncrementalParsing:
    """Test suite for incremental parsing."""

    def test_parse_incremental_full_change(self) -> None:
        """Test incremental parsing with full document change."""
        old_content = ""
        new_content = "@Character: John Doe"

        # For full document change, we can use a dict or just create a simple object
        # Let's use a simple object with 'text' attribute for this test
        class SimpleChange:
            def __init__(self, text: str) -> None:
                self.text = text

        changes = [SimpleChange(new_content)]
        uri = "file:///test.md"

        symbols = parse_incremental(old_content, new_content, changes, uri)  # type: ignore[arg-type]

        assert len(symbols) == 1
        assert isinstance(symbols[0], CharacterSymbol)
        assert symbols[0].name == "John Doe"

    def test_parse_incremental_range_change(self) -> None:
        """Test incremental parsing with a range change."""
        old_content = """Line 0
@Character: John Doe
Line 2
@Character: Jane Smith
Line 4"""
        new_content = """Line 0
@Character: John Doe
Line 2
@Character: Jane Doe
Line 4"""
        uri = "file:///test.md"

        # Create a simple change object with range
        class ChangeWithRange:
            def __init__(self, range_: types.Range, text: str) -> None:
                self.range = range_
                self.text = text

        range_ = types.Range(
            start=types.Position(line=3, character=0),
            end=types.Position(line=3, character=len("@Character: Jane Smith")),
        )
        changes = [ChangeWithRange(range_, "@Character: Jane Doe")]

        symbols = parse_incremental(old_content, new_content, changes, uri)  # type: ignore[arg-type]

        # Should only return symbols affected by the change (line 3)
        assert len(symbols) == 1
        assert isinstance(symbols[0], CharacterSymbol)
        assert symbols[0].name == "Jane Doe"

    def test_parse_incremental_multiple_symbols(self) -> None:
        """Test incremental parsing with multiple symbols."""
        old_content = """# Chapter 1
@Character: John
@Location: Pub"""
        new_content = """# Chapter 1
@Character: John Doe
@Location: The Rusty Anchor Pub"""
        uri = "file:///test.md"

        # Create a simple change object with range
        class ChangeWithRange:
            def __init__(self, range_: types.Range, text: str) -> None:
                self.range = range_
                self.text = text

        range1 = types.Range(
            start=types.Position(line=1, character=0),
            end=types.Position(line=1, character=len("@Character: John")),
        )
        range2 = types.Range(
            start=types.Position(line=2, character=0),
            end=types.Position(line=2, character=len("@Location: Pub")),
        )
        changes = [
            ChangeWithRange(range1, "@Character: John Doe"),
            ChangeWithRange(range2, "@Location: The Rusty Anchor Pub"),
        ]

        symbols = parse_incremental(old_content, new_content, changes, uri)  # type: ignore[arg-type]

        assert len(symbols) == 3  # Chapter 1, John Doe, The Rusty Anchor Pub
        symbol_names = {s.name for s in symbols}
        assert "Chapter 1" in symbol_names
        assert "John Doe" in symbol_names
        assert "The Rusty Anchor Pub" in symbol_names

    def test_parse_incremental_same_content(self) -> None:
        """Test incremental parsing with no actual content changes."""
        old_content = "@Character: John Doe"
        new_content = "@Character: John Doe"
        uri = "file:///test.md"

        # Create a simple change object with range
        class ChangeWithRange:
            def __init__(self, range_: types.Range, text: str) -> None:
                self.range = range_
                self.text = text

        range_ = types.Range(
            start=types.Position(line=0, character=0),
            end=types.Position(line=0, character=len(old_content)),
        )
        changes = [ChangeWithRange(range_, new_content)]

        symbols = parse_incremental(old_content, new_content, changes, uri)  # type: ignore[arg-type]

        # Should still parse the affected line (though content is same)
        assert len(symbols) == 1
        assert symbols[0].name == "John Doe"
