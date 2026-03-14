"""Tests for the completion feature handler."""

import pytest
from lsprotocol import types
from pygls.lsp.server import LanguageServer

from novelwriter_lsp.features.completion import (
    register_completion,
    _get_completion_item_kind,
)
from novelwriter_lsp.index import SymbolIndex
from novelwriter_lsp.types import (
    CharacterSymbol,
    LocationSymbol,
    ItemSymbol,
    LoreSymbol,
    PlotPointSymbol,
    ChapterSymbol,
    OutlineSymbol,
    EventSymbol,
    SymbolType,
)


class TestGetCompletionItemKind:
    """Test mapping from SymbolType to CompletionItemKind."""

    def test_character_kind(self) -> None:
        """Test Character maps to Class."""
        kind = _get_completion_item_kind(SymbolType.CHARACTER)
        assert kind == types.CompletionItemKind.Class

    def test_location_kind(self) -> None:
        """Test Location maps to Struct."""
        kind = _get_completion_item_kind(SymbolType.LOCATION)
        assert kind == types.CompletionItemKind.Struct

    def test_item_kind(self) -> None:
        """Test Item maps to Variable."""
        kind = _get_completion_item_kind(SymbolType.ITEM)
        assert kind == types.CompletionItemKind.Variable

    def test_lore_kind(self) -> None:
        """Test Lore maps to Interface."""
        kind = _get_completion_item_kind(SymbolType.LORE)
        assert kind == types.CompletionItemKind.Interface

    def test_plotpoint_kind(self) -> None:
        """Test PlotPoint maps to Event."""
        kind = _get_completion_item_kind(SymbolType.PLOTPOINT)
        assert kind == types.CompletionItemKind.Event

    def test_outline_kind(self) -> None:
        """Test Outline maps to Module."""
        kind = _get_completion_item_kind(SymbolType.OUTLINE)
        assert kind == types.CompletionItemKind.Module

    def test_event_kind(self) -> None:
        """Test Event maps to Event."""
        kind = _get_completion_item_kind(SymbolType.EVENT)
        assert kind == types.CompletionItemKind.Event

    def test_chapter_kind(self) -> None:
        """Test Chapter maps to File."""
        kind = _get_completion_item_kind(SymbolType.CHAPTER)
        assert kind == types.CompletionItemKind.File


class TestCompletion:
    """Test completion handler."""

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
        idx.update(
            CharacterSymbol(
                id="char_jane_1",
                name="JaneSmith",
                novel_id="novel_1",
                definition_uri="file:///test.md",
                definition_range={
                    "start_line": 6,
                    "end_line": 6,
                    "start_character": 0,
                    "end_character": 8,
                },
            )
        )
        idx.update(
            LocationSymbol(
                id="loc_pub_1",
                name="TheRustyAnchor",
                novel_id="novel_1",
                definition_uri="file:///test.md",
                definition_range={
                    "start_line": 10,
                    "end_line": 10,
                    "start_character": 0,
                    "end_character": 14,
                },
            )
        )
        idx.update(
            ChapterSymbol(
                id="chap_1",
                name="Chapter1",
                novel_id="novel_1",
                definition_uri="file:///test.md",
                definition_range={
                    "start_line": 15,
                    "end_line": 15,
                    "start_character": 0,
                    "end_character": 8,
                },
                chapter_number=1,
            )
        )
        idx.update(
            PlotPointSymbol(
                id="plot_murder_1",
                name="TheMurder",
                novel_id="novel_1",
                definition_uri="file:///test.md",
                definition_range={
                    "start_line": 20,
                    "end_line": 20,
                    "start_character": 0,
                    "end_character": 9,
                },
            )
        )
        return idx

    @pytest.fixture
    def server(self) -> LanguageServer:
        """Create a test server instance."""
        return LanguageServer(name="Test", version="0.1.0")

    def test_register_handler(self, server: LanguageServer, index: SymbolIndex) -> None:
        """Test that handler registration doesn't raise."""
        register_completion(server, index)
